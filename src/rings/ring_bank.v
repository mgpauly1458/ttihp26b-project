// ============================================================================
// ring_bank.v -- the eight ring slots, and nothing else
// ----------------------------------------------------------------------------
// What it does
//   Instantiates the ring population and broadcasts the trim code to all of
//   them. Each ring gets its own enable from the mux and returns its own
//   clock. There is no logic here; this file exists so the slot table in
//   docs/rings.md has exactly one place in the RTL that it describes.
//
// Clock domain
//   None. Eight clock sources.
//
// Slots
//   0..3  ring_21_min      four copies of one netlist, to be placed at four
//                          corners of the tile (region constraints, later)
//   4     ring_21_hd       same stage count, high-drive cells
//   5     ring_11_min      half the stage count
//   6     ring_tap         tap-select trim, code[2:0]
//   7     ring_analog_stub the custom macro, all 8 code bits
//
// Simulation frequencies for slots 0-3 differ by a percent or two so the
// sweep plot shows a population. They are simulation parameters only.
// ============================================================================
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

  ring_analog_stub u_ring7 (
      .code(trim_code), .enable(ring_en[7]), .clk_out(ring_clk[7]));

endmodule

`default_nettype wire
