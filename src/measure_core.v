// measure_core.v -- reciprocal frequency counter: ref_clk cycles over exactly target_n divided-ring periods
//   ref_clk, reset    tile clk and its synchronous active-high reset: FSM, counters and all outputs live here
//   divided_ring      selected ring after the divider; clocks only the window logic, which has no reset
//   start             one-cycle pulse, ignored unless idle
//   target_n [15:0]   periods per measurement, 0 = 65536; static while busy (crosses unsynchronised; regfile enforces)
//   timeout  [15:0]   give up after this many ref cycles; 0 gives up at once (a hang with no flag looks like a dead chip)
//   ref_count[31:0]   result, valid from done to the next start: f_ring = target_n * 2^tap_sel * f_ref / ref_count
//   done, busy, timeout_error   done sticky until start; busy = not idle; timeout_error = result invalid
// FSM: IDLE -start-> CLEAR -(window, finished low)-> ARM -(window)-> RUN -(!window)-> SETTLE -(!finished)-> DONE -> IDLE;
//   a timeout in CLEAR/ARM/RUN/SETTLE goes to DONE with timeout_error.
// - Only single bits cross (arm out; window, finished back, via cdc_sync); sync latency delays both window ends
//   equally and cancels. Window = rising edge 0 to edge target_n = exactly target_n periods; the only error is
//   the +/-1 count from quantising each end, the same for every ring.
// - CLEAR: after a TIMEOUT a slow ring can be mid-window; re-arming before it has seen arm low (2-3 of its edges)
//   leaves it counting stale state and never closing (tb_measure_core recovery test). Also covers X flops after reset.
// - Ring-domain flops have no reset; arm low clears them, and X is safe because every FSM test is "is this bit 1".
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

  // ---- reference domain (ref_clk) -------------------------------------------
  localparam [2:0] S_IDLE   = 3'd0,
                   S_CLEAR  = 3'd1,
                   S_ARM    = 3'd2,
                   S_RUN    = 3'd3,
                   S_SETTLE = 3'd4,
                   S_DONE   = 3'd5;

  reg [2:0]  state;
  reg        arm;             // the one bit sent to the ring domain
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

      // Counts every ref edge at which the synchronised window is high, in any state;
      // cleared on start, final once the window closes.
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

  // ---- ring domain (divided_ring), no reset -----------------------------------
  wire        arm_sync;
  reg         window;         // high for exactly target_n divided-ring periods
  reg         finished;       // window has closed; held until arm drops
  reg  [15:0] edge_count;

  // reset tied low: this domain has none.
  cdc_sync u_sync_arm (
      .clk   (divided_ring),
      .reset (1'b0),
      .d     (arm),
      .q     (arm_sync)
  );

  always @(posedge divided_ring) begin
    if (arm_sync == 1'b0) begin
      // Unarmed: clear everything. finished falling is what completes the SETTLE handshake.
      window     <= 1'b0;
      finished   <= 1'b0;
      edge_count <= 16'd0;
    end else if (finished) begin
      // Closed; hold until the reference side drops arm.
    end else if (!window) begin
      // First rising edge after arming: open on a clean edge.
      window <= 1'b1;
    end else if (edge_count == target_n - 16'd1) begin
      // edge_count is 0 at edge 1, so this is edge target_n: close after exactly target_n periods.
      window   <= 1'b0;
      finished <= 1'b1;
    end else begin
      edge_count <= edge_count + 16'd1;
    end
  end

endmodule

`default_nettype wire
