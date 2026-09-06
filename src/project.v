/*
 * Copyright (c) 2026 Maxwell Pauly
 * SPDX-License-Identifier: Apache-2.0
 *
 * Tile interface for a mixed-signal project. Nothing here is synthesised: the
 * tile's real content is the merged layout in
 * gds/tt_um_mgpauly1458_inverter.gds, which contains two independent blocks.
 *
 *   analog   a hand-drawn CMOS inverter. ua[1] drives the gates, ua[0] is the
 *            drain node. Built from PDK PCells in analog/layout/build_gds.py.
 *
 *   digital  ms_hello (src/ms_hello.v), hardened by LibreLane into a
 *            standard-cell macro and merged into the same tile. Its behaviour
 *            is mirrored below so this file describes what the tile actually
 *            does, but the instance in silicon is the hardened macro, not this
 *            RTL.
 *
 * The two halves share only the supply and the substrate; no signal crosses
 * between them.
 */

`default_nettype none

module tt_um_mgpauly1458_inverter (
    input  wire       VGND,
    input  wire       VDPWR,    // 1.8v power supply
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    inout  wire [7:0] ua,       // Analog pins, only ua[5:0] can be used
    input  wire       ena,      // always 1 when the design is powered
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // The digital half: uo_out[0] is ui_in[0] inverted combinationally,
  // uo_out[1] is the same inversion registered on clk.
  reg q;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else        q <= ~ui_in[0];
  end

  // Unused outputs are tied to ground in the layout, as the analog spec
  // requires, so they are driven low here too rather than left floating.
  assign uo_out  = {6'b0, q, ~ui_in[0]};
  assign uio_out = 8'b0;
  assign uio_oe  = 8'b0;

  wire _unused = &{ena, ui_in[7:1], uio_in, VGND, VDPWR, 1'b0};

endmodule
