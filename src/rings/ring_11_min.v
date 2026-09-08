// ring_11_min.v -- 11-stage minimum-drive ring (slot 5): NAND2_1 enable + 10 INV_1, same cells as ring_21_min
//   code    [7:0]  broadcast trim code, ignored here
//   enable         1 = oscillate; 0 holds the NAND output high, the ring stops in a defined state
//   clk_out        the ring through buffer u_out, so the mux never loads the loop
// Free-running clock source, no clock domain. Half the stages of slot 0, so the frequency ratio should be
//   near 21/11; if not, something other than stage delay (wire, buffer, mux) sets the frequency and the
//   period = 2 * stages * t_stage model is suspect for every ring.
// Expected period (typical, no wires) = 2 * (65 + 10*55) ps = 1.23 ns, ~810 MHz: the fastest standard-cell
//   ring here, and the reason the divider exists.
// - Structural, every cell named and (* keep *); -DSIM swaps in sim/ring_model.v: see ring_21_min.v.
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
