// ring_mux.v -- selects one of eight rings and enables only that one (combinational, on the ring clocks)
//   ring_in [7:0]  the eight ring outputs
//   sel     [2:0]  which one
//   enable         master enable; 0 stops every ring
//   ring_out       the selected ring, through the (* keep *) buffer u_selout
//   ring_en [7:0]  one-hot enable back to the rings; all zero if !enable
// - Unselected rings are off: seven free-running rings would burn power and inject supply and substrate
//   noise into the one being measured. The selected ring is enabled when RING_SEL is written, not at START,
//   so it has run for many clk periods before a window opens; a ring needing longer gets a host-side delay.
// - sel must change only while idle: a combinational clock mux switching between unrelated waveforms can
//   make a runt pulse. regfile blocks RING_SEL writes while busy.
`default_nettype none

module ring_mux (
    input  wire [7:0] ring_in,
    input  wire [2:0] sel,
    input  wire       enable,
    output wire       ring_out,
    output reg  [7:0] ring_en
);

  reg selected;

  always @(*) begin
    case (sel)
      3'd0:    begin selected = ring_in[0]; ring_en = 8'b0000_0001; end
      3'd1:    begin selected = ring_in[1]; ring_en = 8'b0000_0010; end
      3'd2:    begin selected = ring_in[2]; ring_en = 8'b0000_0100; end
      3'd3:    begin selected = ring_in[3]; ring_en = 8'b0000_1000; end
      3'd4:    begin selected = ring_in[4]; ring_en = 8'b0001_0000; end
      3'd5:    begin selected = ring_in[5]; ring_en = 8'b0010_0000; end
      3'd6:    begin selected = ring_in[6]; ring_en = 8'b0100_0000; end
      default: begin selected = ring_in[7]; ring_en = 8'b1000_0000; end
    endcase
    if (!enable) ring_en = 8'b0000_0000;
  end

  // A (* keep *) cell instance keeps its name through synthesis, so src/constraints.sdc can declare
  // the selected ring a clock at u_mux.u_selout/X. Plain assign in simulation (-DSIM).
`ifdef SIM
  assign ring_out = selected;
`else
  (* keep *) sg13g2_buf_1 u_selout (.X(ring_out), .A(selected));
`endif

endmodule

`default_nettype wire
