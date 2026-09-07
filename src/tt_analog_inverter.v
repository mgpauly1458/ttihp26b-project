/*
 * Blackbox declaration + behavioural model of the hand-drawn analog inverter.
 *
 * This module is a HARD MACRO. LibreLane never synthesises it: `(* blackbox *)`
 * tells yosys to keep the instance and take its geometry from the LEF, and
 * `MACROS.tt_analog_inverter` in src/config.json supplies the LEF, the GDS, the
 * Liberty timing and the placement. The layout is built by
 * analog/layout/build_inverter_macro.py out of PDK PCells.
 *
 * The body is only compiled when SIM is defined (iverilog/cocotb pass -DSIM),
 * so simulation sees a plain inverter while synthesis sees an empty box.
 *
 * VPWR/VGND are not ports here: the tile's PDN connects them through the
 * macro's power pins, which is where a hard macro's supply always comes from.
 */

`default_nettype none

(* blackbox *)
module tt_analog_inverter (
    input  wire A,   // gate  - drawn as Metal2 pin on the macro's west edge
    output wire Y    // drain - drawn as Metal2 pin on the macro's east edge
);

`ifdef SIM
  // Zero-delay functional model. The real block's simulated edges are
  // t_PHL = 38.5 ps and t_PLH = 36.9 ps into 10 fF, far below any clock
  // period this tile runs at, so a delayless model is honest enough for the
  // cocotb bench. The Liberty file carries the real numbers for STA.
  assign Y = ~A;
`endif

endmodule

`default_nettype wire
