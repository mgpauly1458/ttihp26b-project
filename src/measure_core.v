// ============================================================================
// measure_core.v -- reciprocal frequency counter with its window FSM
// ----------------------------------------------------------------------------
// What it does
//   Measures how many reference-clock cycles fit into exactly target_n
//   periods of the divided ring clock. The host then computes
//
//       f_ring = target_n * 2^tap_sel * f_ref / ref_count
//
//   Only f_ref has to be accurate, and it arrives on an ordinary input pin.
//
// Clock domains -- this file straddles two, and says which is which
//   REFERENCE domain (ref_clk): the FSM, the reference-cycle counter, the
//     timeout counter, all outputs.
//   RING domain (divided_ring): the edge counter that decides when the
//     measurement window opens and closes. Nothing else.
//   Every signal that crosses goes through cdc_sync. No multi-bit value is
//   ever read across the boundary; see "The window" below.
//
// Interface
//   ref_clk         reference clock (the tile's clk pin)
//   reset           synchronous, active high, reference domain
//   divided_ring    the selected ring after the divider
//   start           one-cycle pulse; ignored unless idle
//   target_n [15:0] number of divided-ring periods to measure over.
//                   0 behaves as 65536.
//   timeout  [15:0] give up after this many reference cycles. 0 gives up
//                   immediately -- deliberately not "disabled", because a
//                   hung measurement with no error flag is indistinguishable
//                   from a broken chip.
//   ref_count[31:0] the result. Valid from done until the next start.
//   done            sticky: set when a measurement ends, cleared by start
//   busy            high from start until done (or timeout)
//   timeout_error   sticky alongside done: the result is NOT valid
//
// The window -- how the counting works and why there is no freeze-then-read
//   The ring domain owns a single bit, `window`. It goes high on a rising
//   edge of divided_ring and low exactly target_n rising edges later. The
//   reference domain synchronises that bit and counts the reference edges at
//   which the synchronised copy is high.
//
//   Both the opening and the closing edge of the window pass through the same
//   two-flop synchroniser, so its latency delays both ends of the window by
//   the same amount and cancels out of the count. What does not cancel is the
//   quantisation: each end of the window lands somewhere between two
//   reference edges. ref_count is therefore the true ratio rounded to an
//   integer, with an error of at most +/-1 count. That is the whole
//   systematic-error budget of this block, and it is the same for every
//   ring, which is what makes ring-to-ring comparison meaningful.
//
//   Because the only thing that crosses is one bit, there is no multi-bit
//   counter to freeze and read. The ring-domain edge counter is never looked
//   at from the reference side. This is the freeze-then-read rule taken to
//   its conclusion: the reference domain reads a value that lives in the
//   reference domain.
//
// The +/-1 question, settled
//   The window spans from rising edge 0 to rising edge target_n of the
//   divided ring -- that is exactly target_n complete periods, not
//   target_n edges (which would be target_n - 1 periods). ref_count counts
//   reference edges that fall inside that window. With target_n = 1 you get
//   one period. There is no hidden -1 or +1 in the ring-period count; the
//   only +/-1 is the reference-edge quantisation above, and the sweep's
//   pass tolerance is written in terms of it.
//
// The FSM (reference domain)
//   IDLE   -> start: clear counters, arm stays LOW                   -> CLEAR
//   CLEAR  wait until the ring domain reports window and finished
//          both low. Normally instant. It matters after a TIMEOUT:
//          an aborted measurement can leave a slow ring mid-window,
//          and if arm went high again before that ring had produced
//          the two or three edges it needs to notice arm was low, it
//          would carry on counting from stale state and never close
//          the window. tb_measure_core's recovery test found exactly
//          that. Also covers the first measurement after reset, when
//          the ring-domain flops are still X.        then raise arm  -> ARM
//   ARM    the ring domain sees arm, opens the window on its next
//          rising edge (so we always begin on a clean edge, never
//          mid-period). Wait for the synchronised window to go high  -> RUN
//   RUN    count reference cycles until the window goes low          -> SETTLE
//   SETTLE drop `arm`; wait until the ring domain reports it has
//          seen that and cleared itself. This handshake is what lets
//          the next measurement start at any later time without
//          racing a slow ring.                                       -> DONE
//   DONE   one cycle: set done, latch nothing (ref_count is already
//          final), return                                            -> IDLE
//   A timeout in CLEAR, ARM, RUN or SETTLE drops arm and goes to DONE
//   with timeout_error set.
//
// Assumptions
//   * target_n is stable from start until done. It crosses into the ring
//     domain unsynchronised, which is only safe because it does not move.
//     The register file refuses writes to it while busy.
//   * The ring-domain flops have no reset (no clock to reset with). They are
//     cleared by `arm` being low, which it is out of reset and between
//     measurements. Until the divided ring has produced two edges after
//     reset they read X in simulation; the FSM tolerates that because every
//     test it makes is "is this bit 1", which X fails, and the timeout
//     covers a ring that never produces those edges at all.
// ============================================================================
`default_nettype none

module measure_core (
    input  wire        ref_clk,
    input  wire        reset,
    input  wire        divided_ring,
    input  wire        start,
    input  wire [15:0] target_n,
    input  wire [15:0] timeout,
    output reg  [31:0] ref_count,
    output reg         done,
    output wire        busy,
    output reg         timeout_error
);

  // ==========================================================================
  // Reference domain
  // ==========================================================================
  localparam [2:0] S_IDLE   = 3'd0,
                   S_CLEAR  = 3'd1,
                   S_ARM    = 3'd2,
                   S_RUN    = 3'd3,
                   S_SETTLE = 3'd4,
                   S_DONE   = 3'd5;

  reg [2:0]  state;
  reg        arm;             // "please measure" -- the one bit sent to the ring domain
  reg [15:0] timeout_count;

  // The two bits coming back from the ring domain.
  wire window_sync;
  wire finished_sync;

  cdc_sync u_sync_window (
      .clk   (ref_clk),
      .reset (reset),
      .d     (window),
      .q     (window_sync)
  );

  cdc_sync u_sync_finished (
      .clk   (ref_clk),
      .reset (reset),
      .d     (finished),
      .q     (finished_sync)
  );

  assign busy = (state != S_IDLE);

  wire timed_out = (timeout_count == timeout);

  always @(posedge ref_clk) begin
    if (reset) begin
      state         <= S_IDLE;
      arm           <= 1'b0;
      ref_count     <= 32'd0;
      timeout_count <= 16'd0;
      done          <= 1'b0;
      timeout_error <= 1'b0;
    end else begin

      // The count itself is independent of the state: every reference edge
      // at which the synchronised window is high is one count. Cleared on
      // start (below). Holds its value after the window closes, so it is
      // final by the time done is raised.
      if (window_sync)
        ref_count <= ref_count + 32'd1;

      case (state)
        S_IDLE: begin
          if (start) begin
            state         <= S_CLEAR;
            arm           <= 1'b0;
            ref_count     <= 32'd0;
            timeout_count <= 16'd0;
            done          <= 1'b0;
            timeout_error <= 1'b0;
          end
        end

        S_CLEAR: begin
          timeout_count <= timeout_count + 16'd1;
          if (timed_out) begin
            state         <= S_DONE;
            timeout_error <= 1'b1;
          end else if (!window_sync && !finished_sync) begin
            state     <= S_ARM;
            arm       <= 1'b1;
            ref_count <= 32'd0;   // a stale window may have been counted during CLEAR
          end
        end

        S_ARM: begin
          timeout_count <= timeout_count + 16'd1;
          if (timed_out) begin
            state         <= S_DONE;
            arm           <= 1'b0;
            timeout_error <= 1'b1;
          end else if (window_sync) begin
            state <= S_RUN;
          end
        end

        S_RUN: begin
          timeout_count <= timeout_count + 16'd1;
          if (timed_out) begin
            state         <= S_DONE;
            arm           <= 1'b0;
            timeout_error <= 1'b1;
          end else if (!window_sync) begin
            state <= S_SETTLE;
            arm   <= 1'b0;
          end
        end

        S_SETTLE: begin
          timeout_count <= timeout_count + 16'd1;
          if (timed_out) begin
            state         <= S_DONE;
            timeout_error <= 1'b1;
          end else if (!finished_sync) begin
            state <= S_DONE;
          end
        end

        S_DONE: begin
          done  <= 1'b1;
          state <= S_IDLE;
        end

        default: state <= S_IDLE;
      endcase
    end
  end

  // ==========================================================================
  // Ring domain -- clocked by divided_ring, no reset
  // ==========================================================================
  wire        arm_sync;
  reg         window;         // high for exactly target_n divided-ring periods
  reg         finished;       // window has closed; held until arm drops
  reg  [15:0] edge_count;

  // reset tied low: this domain has no reset, see the header.
  cdc_sync u_sync_arm (
      .clk   (divided_ring),
      .reset (1'b0),
      .d     (arm),
      .q     (arm_sync)
  );

  always @(posedge divided_ring) begin
    if (arm_sync == 1'b0) begin
      // Not armed: everything cleared. This is also how the SETTLE handshake
      // completes -- finished falls, the reference side sees it fall.
      window     <= 1'b0;
      finished   <= 1'b0;
      edge_count <= 16'd0;
    end else if (finished) begin
      // Measurement over; hold until the reference side drops arm.
    end else if (!window) begin
      // First rising edge after being armed: open the window here, on a
      // clean edge. edge_count was cleared while unarmed.
      window <= 1'b1;
    end else if (edge_count == target_n - 16'd1) begin
      // This is rising edge number target_n since the window opened
      // (edge_count is 0 at edge 1). Close it: exactly target_n periods.
      window   <= 1'b0;
      finished <= 1'b1;
    end else begin
      edge_count <= edge_count + 16'd1;
    end
  end

endmodule

`default_nettype wire
