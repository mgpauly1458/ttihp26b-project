// ring_21_min.v -- 21-stage minimum-drive ring (slots 0-3): NAND2_1 enable + 20 INV_1, the untrimmed baseline
//   code    [7:0]  broadcast trim code, ignored here
//   enable         1 = oscillate; 0 holds the NAND output high, the ring stops in a defined state
//   clk_out        the ring through buffer u_out, so the mux never loads the loop
//   SIM_F_HZ       simulation-only frequency, so slots 0-3 differ and the sweep sees a population
// Free-running clock source, no clock domain. Slots 0-3 are four copies of this netlist placed at four
//   corners of the tile: their spread is a within-die matching measurement.
// Expected period (typical, no wires) = 2 * (65 + 20*55) ps = 2.33 ns, ~430 MHz; 300-400 MHz assumed after layout.
// - Structural, every cell named and (* keep *): synthesis would refuse or remove a combinational loop.
//   Physical needs: don't-touch, set_disable_timing on one loop arc, a region constraint (docs/constraints.md).
// - -DSIM replaces the loop with sim/ring_model.v at a fixed frequency; without SIM the netlist simulates
//   with the delay stand-ins in sim/sg13g2_cells_sim.v (tb_rings only).
`default_nettype none

module ring_21_min #(
    /* verilator lint_off UNUSEDPARAM */
    parameter real SIM_F_HZ = 350.0e6   // simulation only, see header
    /* verilator lint_on UNUSEDPARAM */
) (
    input  wire [7:0] code,
    input  wire       enable,
    output wire       clk_out
);

`ifdef SIM
  // F_MIN = F_MAX and code tied high: the model's curve collapses to one point, no dead zone.
  ring_model #(
      .F_MIN_HZ  (SIM_F_HZ),
      .F_MAX_HZ  (SIM_F_HZ),
      .DEAD_CODE (0)
  ) u_model (
      .code    (8'd255),
      .enable  (enable),
      .clk_out (clk_out)
  );
  wire _unused = &{code};
`else
  (* keep *) wire n0;                                  // NAND output: stage 1
  (* keep *) wire s1, s2, s3, s4, s5, s6, s7, s8, s9, s10;
  (* keep *) wire s11, s12, s13, s14, s15, s16, s17, s18, s19, s20;

  // Stage 1 is the enable gate: enable low sticks n0 high; enable high makes it an inverter.
  (* keep *) sg13g2_nand2_1 u_en (.Y(n0), .A(enable), .B(s20));

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
  (* keep *) sg13g2_inv_1    u_i19 (.Y(s19), .A(s18));
  (* keep *) sg13g2_inv_1    u_i20 (.Y(s20), .A(s19));

  (* keep *) sg13g2_buf_1 u_out (.X(clk_out), .A(n0));

  wire _unused = &{code};
`endif

endmodule

`default_nettype wire
