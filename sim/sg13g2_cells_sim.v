// sg13g2_cells_sim.v -- delay-annotated stand-ins for the cells the structural rings use (tb_rings only)
// - The PDK's Verilog models are zero-delay (timing comes from SDF), and a zero-delay inverter loop
//   never advances simulation time: the simulator hangs.
// - Delays are typical corner (1.2 V, 25 C) from sg13g2_stdcell_typ_1p20V_25C.lib at about fanout-of-one.
//   Enough to check each netlist is a loop at roughly its predicted frequency; not a silicon prediction.
// - Pin names and functions match the Liberty file, so the same netlists go to synthesis untouched.
// - The instrument sweep uses sim/ring_model.v instead: the rings' `ifdef SIM` branch.
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
