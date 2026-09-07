// ============================================================================
// ring_tap.v -- tap-select trimmed ring (slot 6)
// ----------------------------------------------------------------------------
// What it does
//   A ring whose length is chosen by code[2:0]. One NAND2_1 (the enable)
//   feeds a chain of eighteen INV_1; the feedback to the NAND is taken from
//   one of eight points along the chain through two MUX4 and a MUX2.
//   Tapping after inverter 18, 16, ... 4 gives loops of 19, 17, ... 5
//   inverting stages (the NAND plus an even number of inverters is always
//   odd, which a ring needs). The mux delay is in the loop too, and is the
//   same for every tap, so it appears as a fixed offset in the period.
//
//   Higher code = shorter loop = higher frequency, so the trim curve reads
//   the same way as the analog ring's. Eight coarse, large steps: the
//   question this ring answers is whether a cell-level trim is monotonic and
//   what its step size is.
//
// Clock domain
//   None: it IS a clock source. Free-running while enable is high.
//
// Interface (the same for every ring, including the analog macro)
//   code    [7:0]  the broadcast trim code. Bits [2:0] select the tap; bits [7:3] are ignored.
//   enable         1 = oscillate. 0 holds the NAND output high and the
//                  ring stops in a defined state.
//   clk_out        the ring, through a buffer so the mux never loads the
//                  loop directly
//
// Structural, not synthesised
//   Every cell is instantiated by name so synthesis cannot see a
//   combinational loop -- it would either refuse or optimise the ring away.
//   The (* keep *) attributes stop yosys removing or merging anything. At
//   the physical stage this module needs: don't-touch on the instances, a
//   set_disable_timing on one arc to break the timing loop, and a region
//   constraint so the placer keeps the loop compact (docs/constraints.md).
//
// Simulation
//   With SIM defined the loop is replaced by sim/ring_model.v with this
//   ring's fixed frequency, so the instrument can be swept against a known
//   answer. Without SIM the structural loop is simulated using the delay
//   stand-ins in sim/sg13g2_cells_sim.v (tb_rings only).
//
// Code to tap
//   code[2:0] = 0 : feedback from s18, 19 stages, slowest
//               1 : s16, 17 stages
//               2 : s14, 15
//               3 : s12, 13
//               4 : s10, 11
//               5 : s8,   9
//               6 : s6,   7
//               7 : s4,   5 stages, fastest
//   The inverters beyond the tap still toggle (they are driven) but are
//   simply loads on the tapped node, and identical loads for every tap
//   except the last two.
//
// Expected period (typical corner, no wires)
//   2 * (t_nand + stages_inv * t_inv + t_mux4 + t_mux2)
//   = 2 * (65 + (18 - 2*code) * 55 + 180 + 110) ps
//   code 0: 2.69 ns (370 MHz)   code 7: 1.15 ns (870 MHz)
//
// Changing code while a measurement runs makes the mux switch mid-cycle and
// can glitch the loop. The register file refuses TRIM_CODE writes while
// busy for exactly this reason.
//
// ============================================================================
`default_nettype none

module ring_tap (
    input  wire [7:0] code,
    input  wire       enable,
    output wire       clk_out
);

`ifdef SIM
  // The model sees only code[2:0], stretched over its curve: code' =
  // {code[2:0], 5'b11111} = 31, 63, ... 255. No dead zone -- a tap-select
  // ring always oscillates -- and a wide span so the eight steps are visibly
  // distinct in the sweep plot.
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

  // Tap select. Ordered so a higher code picks a shorter loop.
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
