// ring_21_hd.v -- 21-stage high-drive ring (slot 4): NAND2_2 enable + 20 INV_8, same topology as ring_21_min
//   code    [7:0]  broadcast trim code, ignored here
//   enable         1 = oscillate; 0 holds the NAND output high, the ring stops in a defined state
//   clk_out        the ring through buffer u_out, so the mux never loads the loop
// Free-running clock source, no clock domain. Same stage count as slot 0, wide devices: separates drive
//   strength from stage count in the frequency, tempco and supply-pushing results.
// Expected period (typical, no wires) = 2 * (60 + 20*60) ps = 2.52 ns, ~400 MHz (INV_8 into the next INV_8's
//   22 fF is about INV_1 into INV_1). Of interest is how much less wire load matters, and the tempco.
// - Structural, every cell named and (* keep *); -DSIM swaps in sim/ring_model.v: see ring_21_min.v.
`default_nettype none

module ring_21_hd (
    input  wire [7:0] code,
    input  wire       enable,
    output wire       clk_out
);

`ifdef SIM
  ring_model #(
      .F_MIN_HZ  (380.0e6),
      .F_MAX_HZ  (380.0e6),
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
  (* keep *) wire s11, s12, s13, s14, s15, s16, s17, s18, s19, s20;

  (* keep *) sg13g2_nand2_2 u_en (.Y(n0), .A(enable), .B(s20));

  (* keep *) sg13g2_inv_8    u_i1  (.Y(s1), .A(n0));
  (* keep *) sg13g2_inv_8    u_i2  (.Y(s2), .A(s1));
  (* keep *) sg13g2_inv_8    u_i3  (.Y(s3), .A(s2));
  (* keep *) sg13g2_inv_8    u_i4  (.Y(s4), .A(s3));
  (* keep *) sg13g2_inv_8    u_i5  (.Y(s5), .A(s4));
  (* keep *) sg13g2_inv_8    u_i6  (.Y(s6), .A(s5));
  (* keep *) sg13g2_inv_8    u_i7  (.Y(s7), .A(s6));
  (* keep *) sg13g2_inv_8    u_i8  (.Y(s8), .A(s7));
  (* keep *) sg13g2_inv_8    u_i9  (.Y(s9), .A(s8));
  (* keep *) sg13g2_inv_8    u_i10 (.Y(s10), .A(s9));
  (* keep *) sg13g2_inv_8    u_i11 (.Y(s11), .A(s10));
  (* keep *) sg13g2_inv_8    u_i12 (.Y(s12), .A(s11));
  (* keep *) sg13g2_inv_8    u_i13 (.Y(s13), .A(s12));
  (* keep *) sg13g2_inv_8    u_i14 (.Y(s14), .A(s13));
  (* keep *) sg13g2_inv_8    u_i15 (.Y(s15), .A(s14));
  (* keep *) sg13g2_inv_8    u_i16 (.Y(s16), .A(s15));
  (* keep *) sg13g2_inv_8    u_i17 (.Y(s17), .A(s16));
  (* keep *) sg13g2_inv_8    u_i18 (.Y(s18), .A(s17));
  (* keep *) sg13g2_inv_8    u_i19 (.Y(s19), .A(s18));
  (* keep *) sg13g2_inv_8    u_i20 (.Y(s20), .A(s19));

  (* keep *) sg13g2_buf_1 u_out (.X(clk_out), .A(n0));

  wire _unused = &{code};
`endif

endmodule

`default_nettype wire
