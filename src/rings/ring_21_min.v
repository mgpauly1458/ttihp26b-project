// ============================================================================
// ring_21_min.v -- 21-stage minimum-drive ring (slots 0-3)
// ----------------------------------------------------------------------------
// What it does
//   A 21-stage ring oscillator built from the smallest cells the library has:
//   one NAND2 (which is also the enable) and twenty INV_1. Untrimmed: it is
//   the baseline process monitor. Slots 0-3 are four instances of THIS
//   module, placed at separate corners of the tile, so that their spread is
//   a within-die matching measurement. Same netlist, different location --
//   that is the whole experiment.
//
// Clock domain
//   None: it IS a clock source. Free-running while enable is high.
//
// Interface (the same for every ring, including the analog macro)
//   code    [7:0]  the broadcast trim code. Ignored by this ring.
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
// Parameter
//   SIM_F_HZ affects ONLY the simulation model, so the four instances can
//   have four slightly different frequencies and the sweep sees a
//   population instead of four copies of one number. The structural
//   netlist has no parameters.
//
// Expected frequency (typical corner, no wires, from the cell delays)
//   period = 2 * (t_nand2_1 + 20 * t_inv_1) = 2 * (65 + 20*55) ps = 2.33 ns
//   so roughly 430 MHz. Wire load will pull that down; 300-400 MHz is the
//   working assumption until layout.
//
// ============================================================================
`default_nettype none

module ring_21_min #(
    parameter real SIM_F_HZ = 350.0e6   // simulation only, see header
) (
    input  wire [7:0] code,
    input  wire       enable,
    output wire       clk_out
);

`ifdef SIM
  // Fixed frequency: F_MIN = F_MAX and the code is tied high, so the model's
  // curve collapses to a single point. No dead zone.
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

  // Stage 1 is the enable gate: with enable low, n0 is stuck high and the
  // loop cannot oscillate. With enable high it is just another inverter.
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
