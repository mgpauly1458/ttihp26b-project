/*
 * Copyright (c) 2026 Maxwell Pauly
 * SPDX-License-Identifier: Apache-2.0
 *
 * Blackbox stub for an analog project. The tile's real content is the
 * hand-drawn layout in gds/tt_um_mgpauly1458_inverter.gds; nothing is
 * synthesised from this file. It exists so the flow can check the port list
 * and so downstream tools have a module to instantiate.
 *
 * A CMOS inverter: ua[1] drives the gates, ua[0] is the drain node.
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

  // This design is entirely analog; the digital outputs are unused.
  assign uo_out  = 8'b0;
  assign uio_out = 8'b0;
  assign uio_oe  = 8'b0;

  wire _unused = &{ena, clk, rst_n, ui_in, uio_in, VGND, VDPWR, 1'b0};

endmodule
