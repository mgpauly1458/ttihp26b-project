// ring_tap.v -- tap-select trimmed ring (slot 6): NAND2_1 enable + 18 INV_1, feedback tapped by code[2:0]
//   code    [7:0]  [2:0] selects the tap, [7:3] ignored. Higher code = shorter loop = higher frequency
//   enable         1 = oscillate; 0 holds the NAND output high, the ring stops in a defined state
//   clk_out        the ring through buffer u_out, so the mux never loads the loop
// Free-running clock source, no clock domain. Answers whether a cell-level trim is monotonic and what its step is.
// Tap: code 0 -> s18 (19 stages, slowest)  1 -> s16 (17)  2 -> s14 (15)  3 -> s12 (13)  4 -> s10 (11)
//   5 -> s8 (9)  6 -> s6 (7)  7 -> s4 (5 stages, fastest). NAND + an even number of inverters is always odd.
// Expected period (typical, no wires) = 2 * (65 + (18 - 2*code)*55 + 180 + 110) ps: code 0 2.69 ns (370 MHz),
//   code 7 1.15 ns (870 MHz). The mux delay is in the loop and equal for every tap: a fixed period offset.
// - Inverters beyond the tap still toggle but are only loads on the tapped node, identical except for the last two taps.
// - Changing code mid-measurement switches the mux mid-cycle and can glitch the loop; regfile blocks TRIM_CODE writes while busy.
// - Structural, every cell named and (* keep *); -DSIM swaps in sim/ring_model.v: see ring_21_min.v.
`default_nettype none

module ring_tap (
    input  wire [7:0] code,
    input  wire       enable,
    output wire       clk_out
);

`ifdef SIM
  // The model sees code[2:0] stretched to {code[2:0], 5'b11111} = 31, 63, ... 255: no dead zone (a tap
  // ring always oscillates) and a wide span so the eight steps are distinct in the sweep plot.
  ring_model #(
      .F_MIN_HZ  (150.0e6),
      .F_MAX_HZ  (500.0e6),
      .DEAD_CODE (0)
  ) u_model (
      .code    ({code[2:0], 5'b11111}),
      .enable  (enable),
      .clk_out (clk_out)
  );
  wire _unused = &{code[7:3]};
`else
  (* keep *) wire n0;
  (* keep *) wire s1, s2, s3, s4, s5, s6, s7, s8, s9, s10;
  (* keep *) wire s11, s12, s13, s14, s15, s16, s17, s18;
  (* keep *) wire tap_long, tap_short, fb;

  (* keep *) sg13g2_nand2_1 u_en (.Y(n0), .A(enable), .B(fb));

  (* keep *) sg13g2_inv_1    u_i1  (.Y(s1), .A(n0));
  (* keep *) sg13g2_inv_1    u_i2  (.Y(s2), .A(s1));
  (* keep *) sg13g2_inv_1    u_i3  (.Y(s3), .A(s2));
  (* keep *) sg13g2_inv_1    u_i4  (.Y(s4), .A(s3));
  (* keep *) sg13g2_inv_1    u_i5  (.Y(s5), .A(s4));
  (* keep *) sg13g2_inv_1    u_i6  (.Y(s6), .A(s5));
  (* keep *) sg13g2_inv_1    u_i7  (.Y(s7), .A(s6));
  (* keep *) sg13g2_inv_1    u_i8  (.Y(s8), .A(s7));
  (* keep *) sg13g2_inv_1    u_i9  (.Y(s9), .A(s8));
  (* keep *) sg13g2_inv_1    u_i10 (.Y(s10), .A(s9));
  (* keep *) sg13g2_inv_1    u_i11 (.Y(s11), .A(s10));
  (* keep *) sg13g2_inv_1    u_i12 (.Y(s12), .A(s11));
  (* keep *) sg13g2_inv_1    u_i13 (.Y(s13), .A(s12));
  (* keep *) sg13g2_inv_1    u_i14 (.Y(s14), .A(s13));
  (* keep *) sg13g2_inv_1    u_i15 (.Y(s15), .A(s14));
  (* keep *) sg13g2_inv_1    u_i16 (.Y(s16), .A(s15));
  (* keep *) sg13g2_inv_1    u_i17 (.Y(s17), .A(s16));
  (* keep *) sg13g2_inv_1    u_i18 (.Y(s18), .A(s17));

  // Tap select, ordered so a higher code picks a shorter loop.
  (* keep *) sg13g2_mux4_1 u_mux_long (
      .X(tap_long), .A0(s18), .A1(s16), .A2(s14), .A3(s12),
      .S0(code[0]), .S1(code[1]));
  (* keep *) sg13g2_mux4_1 u_mux_short (
      .X(tap_short), .A0(s10), .A1(s8), .A2(s6), .A3(s4),
      .S0(code[0]), .S1(code[1]));
  (* keep *) sg13g2_mux2_1 u_mux_fb (
      .X(fb), .A0(tap_long), .A1(tap_short), .S(code[2]));

  (* keep *) sg13g2_buf_1 u_out (.X(clk_out), .A(n0));

  wire _unused = &{code[7:3]};
`endif

endmodule

`default_nettype wire
