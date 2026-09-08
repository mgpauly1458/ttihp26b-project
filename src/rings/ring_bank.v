// ring_bank.v -- the eight ring slots: trim code broadcast, per-slot enable in, one clock out. No logic.
//   trim_code [7:0]  broadcast to every ring
//   ring_en   [7:0]  one-hot from ring_mux
//   ring_clk  [7:0]  one clock source per slot
// Slot  0-3 ring_21_min (four copies, four corners of the tile)   4 ring_21_hd   5 ring_11_min
//       6 ring_tap (code[2:0])   7 tt_analog_ring (analog/, all 8 code bits)          docs/rings.md
// - SIM_F_HZ for slots 0-3 differs by a percent or two so the sweep plot shows a population; simulation only.
`default_nettype none

module ring_bank (
    input  wire [7:0] trim_code,
    input  wire [7:0] ring_en,
    output wire [7:0] ring_clk
);

  ring_21_min #(.SIM_F_HZ(350.0e6)) u_ring0 (
      .code(trim_code), .enable(ring_en[0]), .clk_out(ring_clk[0]));

  ring_21_min #(.SIM_F_HZ(343.0e6)) u_ring1 (
      .code(trim_code), .enable(ring_en[1]), .clk_out(ring_clk[1]));

  ring_21_min #(.SIM_F_HZ(357.0e6)) u_ring2 (
      .code(trim_code), .enable(ring_en[2]), .clk_out(ring_clk[2]));

  ring_21_min #(.SIM_F_HZ(351.0e6)) u_ring3 (
      .code(trim_code), .enable(ring_en[3]), .clk_out(ring_clk[3]));

  ring_21_hd u_ring4 (
      .code(trim_code), .enable(ring_en[4]), .clk_out(ring_clk[4]));

  ring_11_min u_ring5 (
      .code(trim_code), .enable(ring_en[5]), .clk_out(ring_clk[5]));

  ring_tap u_ring6 (
      .code(trim_code), .enable(ring_en[6]), .clk_out(ring_clk[6]));

  tt_analog_ring u_ring7 (
      .code(trim_code), .enable(ring_en[7]), .clk_out(ring_clk[7]));

endmodule

`default_nettype wire
