// ring_divider.v -- ripple divider, /1 to /128 by tap_sel, for the selected ring (ring domain only)
//   ring_clk        the selected ring, raw
//   reset           ASYNCHRONOUS, active high: the ring may be stopped while reset is applied, and a synchronous
//                   reset needs a clock edge, so the stages would never leave X
//   tap_sel [2:0]   divide ratio = 2 ** tap_sel; 0 = the raw ring
//   divided_clk     the chosen tap, through the (* keep *) buffer u_divout
// - Seven toggle flops in a ripple chain (Q-bar to own D, clocked by the previous Q) plus the raw tap. Ripple skew
//   is a fixed offset and does not change how many edges there are.
// - q1 is the only flop on the raw ring and the fastest thing in the design: one flop, Q-bar to D, nothing else. Keep it so.
// - tap_sel must change only while idle: the tap mux switching mid-period makes a runt pulse (tb_ring_divider).
// - u_divout is a clock root in src/constraints.sdc, constrained to 250 MHz: a ring faster than that is measured at
//   tap 1 or higher, the instrument's one usage rule. Tap 0 is for slow rings (analog ring, low codes).
`default_nettype none

module ring_divider (
    input  wire       ring_clk,
    input  wire       reset,
    input  wire [2:0] tap_sel,
    output wire       divided_clk
);

  reg tap;   // tap mux output, before the named buffer

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

  // Tap mux: divide by 2 ** tap_sel.
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

  // Named (* keep *) buffer so src/constraints.sdc can declare the divided ring a clock at
  // u_div.u_divout/X. Plain assign in simulation (-DSIM).
`ifdef SIM
  assign divided_clk = tap;
`else
  (* keep *) sg13g2_buf_1 u_divout (.X(divided_clk), .A(tap));
`endif

endmodule

`default_nettype wire
