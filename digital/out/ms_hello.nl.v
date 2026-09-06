module ms_hello (a,
    clk,
    rst_n,
    y_comb,
    y_reg);
 input a;
 input clk;
 input rst_n;
 output y_comb;
 output y_reg;

 wire net1;
 wire net2;
 wire net3;
 wire net4;

 sg13g2_decap_8 FILLER_0_0 ();
 sg13g2_decap_8 FILLER_0_14 ();
 sg13g2_decap_8 FILLER_0_21 ();
 sg13g2_decap_8 FILLER_0_28 ();
 sg13g2_decap_8 FILLER_0_35 ();
 sg13g2_decap_8 FILLER_0_42 ();
 sg13g2_decap_8 FILLER_0_49 ();
 sg13g2_decap_8 FILLER_0_56 ();
 sg13g2_decap_8 FILLER_0_63 ();
 sg13g2_decap_8 FILLER_0_7 ();
 sg13g2_decap_8 FILLER_0_70 ();
 sg13g2_fill_2 FILLER_0_77 ();
 sg13g2_fill_1 FILLER_0_79 ();
 sg13g2_decap_8 FILLER_1_0 ();
 sg13g2_decap_8 FILLER_1_14 ();
 sg13g2_decap_8 FILLER_1_21 ();
 sg13g2_decap_8 FILLER_1_28 ();
 sg13g2_decap_8 FILLER_1_35 ();
 sg13g2_decap_8 FILLER_1_42 ();
 sg13g2_decap_8 FILLER_1_49 ();
 sg13g2_decap_8 FILLER_1_56 ();
 sg13g2_decap_8 FILLER_1_63 ();
 sg13g2_decap_8 FILLER_1_7 ();
 sg13g2_decap_8 FILLER_1_70 ();
 sg13g2_fill_2 FILLER_1_77 ();
 sg13g2_fill_1 FILLER_1_79 ();
 sg13g2_decap_8 FILLER_2_0 ();
 sg13g2_decap_8 FILLER_2_14 ();
 sg13g2_decap_8 FILLER_2_21 ();
 sg13g2_decap_8 FILLER_2_28 ();
 sg13g2_fill_2 FILLER_2_35 ();
 sg13g2_fill_1 FILLER_2_37 ();
 sg13g2_decap_8 FILLER_2_41 ();
 sg13g2_decap_8 FILLER_2_48 ();
 sg13g2_decap_8 FILLER_2_55 ();
 sg13g2_decap_8 FILLER_2_62 ();
 sg13g2_decap_8 FILLER_2_69 ();
 sg13g2_decap_8 FILLER_2_7 ();
 sg13g2_decap_4 FILLER_2_76 ();
 sg13g2_decap_8 FILLER_3_0 ();
 sg13g2_decap_8 FILLER_3_14 ();
 sg13g2_decap_4 FILLER_3_21 ();
 sg13g2_fill_2 FILLER_3_25 ();
 sg13g2_decap_8 FILLER_3_54 ();
 sg13g2_decap_8 FILLER_3_61 ();
 sg13g2_decap_8 FILLER_3_68 ();
 sg13g2_decap_8 FILLER_3_7 ();
 sg13g2_decap_4 FILLER_3_75 ();
 sg13g2_fill_1 FILLER_3_79 ();
 sg13g2_decap_8 FILLER_4_0 ();
 sg13g2_decap_4 FILLER_4_14 ();
 sg13g2_fill_1 FILLER_4_18 ();
 sg13g2_decap_8 FILLER_4_23 ();
 sg13g2_decap_8 FILLER_4_30 ();
 sg13g2_fill_2 FILLER_4_37 ();
 sg13g2_decap_8 FILLER_4_43 ();
 sg13g2_decap_8 FILLER_4_50 ();
 sg13g2_fill_2 FILLER_4_57 ();
 sg13g2_decap_8 FILLER_4_63 ();
 sg13g2_decap_8 FILLER_4_7 ();
 sg13g2_decap_4 FILLER_4_70 ();
 sg13g2_fill_2 FILLER_4_74 ();
 sg13g2_inv_1 _0_ (.Y(net3),
    .A(net1));
 sg13g2_dfrbpq_1 _1_ (.RESET_B(net2),
    .D(net3),
    .Q(net4),
    .CLK(clk));
 sg13g2_buf_1 input1 (.A(a),
    .X(net1));
 sg13g2_buf_1 input2 (.A(rst_n),
    .X(net2));
 sg13g2_buf_1 output3 (.A(net3),
    .X(y_comb));
 sg13g2_buf_1 output4 (.A(net4),
    .X(y_reg));
endmodule
