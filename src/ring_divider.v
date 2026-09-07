// ============================================================================
// ring_divider.v -- programmable-tap ripple divider for the selected ring
// ----------------------------------------------------------------------------
// What it does
//   Divides the ring clock by 1, 2, 4, ... 128, selected by tap_sel. The ring
//   may run at several hundred MHz; the counter downstream would have to close
//   timing at that speed, and whether it does would move with temperature.
//   Divide first and the counter sees something comfortable. The ratio is
//   exactly known, so the host multiplies it back in.
//
// Clock domain
//   Ring domain. Every flop here is clocked by the ring or by the previous
//   stage; nothing here sees the reference clock.
//
// Interface
//   ring_clk        the selected ring, raw
//   reset           ASYNCHRONOUS, active high. Asynchronous is a deliberate
//                   exception to the project's synchronous-reset rule: the
//                   ring may be stopped (dead code, disabled) while reset is
//                   applied, and a synchronous reset needs a clock edge to
//                   act. With no edges the stages would never leave X.
//   tap_sel [2:0]   0 = ring_clk itself (divide by 1) ... 7 = divide by 128
//   divided_clk     the chosen tap
//
// How it works
//   Seven toggle flops in a ripple chain: each flop's Q-bar feeds its own D,
//   so it halves whatever clocks it, and each flop is clocked by the previous
//   flop's Q. Ripple (asynchronous) is fine here: we are counting edges, not
//   timing them, and the cumulative clock-to-Q skew down the chain is a fixed
//   offset that does not change how many edges there are.
//
//   The brief's counting: "eight stages, divide by 1 to 128". Divide-by-1 is
//   the raw ring, which needs no flop, so 1..128 takes seven flops plus the
//   raw tap -- eight taps, seven flops. Written longhand: seven is not many.
//
// Timing-critical element
//   q1 is the only flop that sees the raw ring and is the fastest thing in
//   the whole design. It is kept to one flop with Q-bar fed back to D and
//   nothing else on the path. Keep it that way.
//
// Assumptions
//   * tap_sel changes only while no measurement is running (the register
//     file enforces this). Changing it while running can produce a runt
//     pulse on divided_clk -- the mux switches between two unrelated
//     waveforms mid-period. tb_ring_divider measures this.
// ============================================================================
`default_nettype none

module ring_divider (
    input  wire       ring_clk,
    input  wire       reset,
    input  wire [2:0] tap_sel,
    output wire       divided_clk
);

  reg tap;   // the tap mux output, before the named buffer below

  reg q1, q2, q3, q4, q5, q6, q7;

  // Stage 1: the only flop on the raw ring. Keep it minimal.
  always @(posedge ring_clk or posedge reset)
    if (reset) q1 <= 1'b0; else q1 <= ~q1;

  always @(posedge q1 or posedge reset)
    if (reset) q2 <= 1'b0; else q2 <= ~q2;

  always @(posedge q2 or posedge reset)
    if (reset) q3 <= 1'b0; else q3 <= ~q3;

  always @(posedge q3 or posedge reset)
    if (reset) q4 <= 1'b0; else q4 <= ~q4;

  always @(posedge q4 or posedge reset)
    if (reset) q5 <= 1'b0; else q5 <= ~q5;

  always @(posedge q5 or posedge reset)
    if (reset) q6 <= 1'b0; else q6 <= ~q6;

  always @(posedge q6 or posedge reset)
    if (reset) q7 <= 1'b0; else q7 <= ~q7;

  // Tap select. divide ratio = 2 ** tap_sel.
  always @(*) begin
    case (tap_sel)
      3'd0:    tap = ring_clk;   // /1
      3'd1:    tap = q1;         // /2
      3'd2:    tap = q2;         // /4
      3'd3:    tap = q3;         // /8
      3'd4:    tap = q4;         // /16
      3'd5:    tap = q5;         // /32
      3'd6:    tap = q6;         // /64
      default: tap = q7;         // /128
    endcase
  end

  // The divided clock leaves through a named buffer so that
  // src/constraints.sdc can declare it a clock at u_div.u_divout/X. That
  // declaration is where the instrument's one timing rule lives: the window
  // logic in measure_core is timed for a divided ring of at most 250 MHz,
  // so a ring faster than that must be measured through tap 1 or higher
  // (the tap-0 path exists for slow rings, such as the analog ring at low
  // codes). In simulation (-DSIM) the buffer is a plain assign.
`ifdef SIM
  assign divided_clk = tap;
`else
  (* keep *) sg13g2_buf_1 u_divout (.X(divided_clk), .A(tap));
`endif

endmodule

`default_nettype wire
