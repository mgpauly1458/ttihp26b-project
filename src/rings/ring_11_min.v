// ============================================================================
// ring_11_min.v -- 11-stage minimum-drive ring (slot 5)
// ----------------------------------------------------------------------------
// What it does
//   Eleven stages of the same cells as ring_21_min: one NAND2_1 and ten
//   INV_1. Roughly half the stage count, so it should run at roughly twice
//   the frequency of slot 0. If the measured ratio is not close to 21/11
//   then something other than stage delay is setting the frequency (wire,
//   the buffer, the mux) and the model of "period = 2 * stages * t_stage"
//   needs revisiting before any other ring's number is trusted.
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
// Expected frequency (typical corner, no wires)
//   period ~ 2 * (65 + 10*55) ps = 1.23 ns, roughly 810 MHz. The fastest
//   standard-cell ring here, and the reason the divider has to exist.
//
// ============================================================================
`default_nettype none

module ring_11_min (
    input  wire [7:0] code,
    input  wire       enable,
    output wire       clk_out
);

`ifdef SIM
  ring_model #(
      .F_MIN_HZ  (650.0e6),
      .F_MAX_HZ  (650.0e6),
      .DEAD_CODE (0)
  ) u_model (
      .code    (8'd255),
      .enable  (enable),
      .clk_out (clk_out)
  );
  wire _unused = &{code};
`else
  (* keep *) wire n0;
  (* keep *) wire s1, s2, s3, s4, s5, s6, s7, s8, s9, s10;

  (* keep *) sg13g2_nand2_1 u_en (.Y(n0), .A(enable), .B(s10));

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

  (* keep *) sg13g2_buf_1 u_out (.X(clk_out), .A(n0));

  wire _unused = &{code};
`endif

endmodule

`default_nettype wire
