/*
 * Tiny Tapeout top level: a digital tile with a hand-drawn analog block inside.
 *
 * The hierarchy is deliberately digital-on-top. LibreLane hardens this module
 * into the whole 1x2 tile, places tt_analog_inverter as a hard macro, builds
 * the PDN over both, and routes between them. The analog block is imported by
 * the digital flow, not the other way round.
 *
 * The submission is a DIGITAL one - analog_pins is 0 in info.yaml and no ua[]
 * pin is touched. The analog content lives entirely inside the tile.
 */

`default_nettype none

module tt_um_mgpauly1458_ms_hello (
    input  wire [7:0] ui_in,    // dedicated inputs
    output wire [7:0] uo_out,   // dedicated outputs
    input  wire [7:0] uio_in,   // IOs: input path
    output wire [7:0] uio_out,  // IOs: output path
    output wire [7:0] uio_oe,   // IOs: enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  wire a = ui_in[0];
  wire y_analog;

  // The hand-drawn CMOS inverter. Hard macro; see src/tt_analog_inverter.v.
  tt_analog_inverter u_inv (
      .A(a),
      .Y(y_analog)
  );

  wire y_comb, y_reg, y_ref, mismatch;

  ms_hello u_dig (
      .clk      (clk),
      .rst_n    (rst_n),
      .a        (a),
      .y_analog (y_analog),
      .y_comb   (y_comb),
      .y_reg    (y_reg),
      .y_ref    (y_ref),
      .mismatch (mismatch)
  );

  assign uo_out = {4'b0000, mismatch, y_ref, y_reg, y_comb};

  // Bidirectionals unused: drive them low and hold them as inputs.
  assign uio_out = 8'b0;
  assign uio_oe  = 8'b0;

  // Silence the linter about the inputs this design does not use.
  wire _unused = &{ena, ui_in[7:1], uio_in, 1'b0};

endmodule

`default_nettype wire
