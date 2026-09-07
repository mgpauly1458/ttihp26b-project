// ============================================================================
// sg13g2_cells_sim.v -- delay-annotated stand-ins for the cells the rings use
// ----------------------------------------------------------------------------
// The structural rings in src/rings/ instantiate SG13G2 standard cells by
// name. To simulate them we need a model of each cell WITH a propagation
// delay: a zero-delay inverter loop never advances simulation time and the
// simulator hangs. The PDK's own Verilog models are zero-delay (their timing
// comes from SDF back-annotation after layout), so this file provides the
// handful of cells the rings use, each with one rough delay.
//
// The delays are typical-corner (1.2 V, 25 C) numbers read from
// sg13g2_stdcell_typ_1p20V_25C.lib at roughly fanout-of-one loading. They
// are here to sanity-check that each netlist is wired into a loop that
// oscillates at about the frequency its stage count predicts. They are NOT
// a prediction of silicon: wire load, the real corner and the layout will
// all move them. Only tb_rings.v compiles this file. The instrument sweep
// uses sim/ring_model.v instead, which is why the ring modules carry an
// `ifdef SIM` branch.
//
// Pin names and functions match the Liberty file exactly, so the same ring
// netlists go to synthesis untouched.
// ============================================================================
`timescale 1ns / 1ps

module sg13g2_inv_1 (output Y, input A);
  assign #0.055 Y = ~A;
endmodule

module sg13g2_inv_8 (output Y, input A);
  assign #0.060 Y = ~A;      // faster edge, but driving another inv_8's 22 fF
endmodule

module sg13g2_nand2_1 (output Y, input A, input B);
  assign #0.065 Y = ~(A & B);
endmodule

module sg13g2_nand2_2 (output Y, input A, input B);
  assign #0.060 Y = ~(A & B);
endmodule

module sg13g2_buf_1 (output X, input A);
  assign #0.080 X = A;
endmodule

module sg13g2_mux2_1 (output X, input A0, input A1, input S);
  assign #0.110 X = S ? A1 : A0;
endmodule

module sg13g2_mux4_1 (output X, input A0, input A1, input A2, input A3, input S0, input S1);
  assign #0.180 X = S1 ? (S0 ? A3 : A2) : (S0 ? A1 : A0);
endmodule
