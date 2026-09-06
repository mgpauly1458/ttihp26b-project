/*
 * Copyright (c) 2026 Maxwell Pauly
 * SPDX-License-Identifier: Apache-2.0
 *
 * The digital half of the mixed-signal tile: a "hello world" inverter in RTL,
 * hardened by LibreLane into a standard-cell macro that is then merged into the
 * hand-drawn analog tile (see analog/layout/build_gds.py).
 *
 * Deliberately small but not degenerate. A purely combinational inverter would
 * synthesise to one cell and exercise neither CTS nor timing analysis, so the
 * block also carries a registered copy of the same inversion.
 *
 *   y_comb = ~a                     combinational, straight through
 *   y_reg  = ~a registered on clk   resets low
 */

`default_nettype none

module ms_hello (
    input  wire clk,
    input  wire rst_n,
    input  wire a,
    output wire y_comb,
    output wire y_reg
);

  reg q;

  assign y_comb = ~a;
  assign y_reg  = q;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else        q <= ~a;
  end

endmodule

`default_nettype wire
