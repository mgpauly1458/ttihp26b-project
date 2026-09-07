// ============================================================================
// tt_analog_ring.v -- ring slot 7: the hand-drawn analog ring oscillator
// ----------------------------------------------------------------------------
// What it is
//   A HARD MACRO, not RTL. The layout is analog/macro/tt_analog_ring.gds, an
//   11-stage current-starved ring oscillator whose starving current comes
//   from a binary-weighted bank of 255 unit NMOS transistors switched
//   straight by the code bits, plus two always-on units so code 0 still
//   runs. Everything analog is inside; every port is a rail-to-rail digital
//   signal. analog/README.md is the full description.
//
//   `(* blackbox *)` tells yosys to keep the instance and take nothing else
//   from this file. LibreLane gets the geometry from analog/macro/*.lef, the
//   timing from analog/lib/*.lib and the placement from MACROS in
//   src/config.json.
//
// Interface (the same as every other ring in src/rings/)
//   code    [7:0]  binary weighted, bit 7 widest. Higher code = more
//                  current = higher frequency. Simulated post-layout
//                  (kpex parasitics, typical corner, 27 C): 2.0 MHz at
//                  code 0, 18 MHz at 16, 164 MHz at 255; the pre-layout
//                  netlist runs twice as fast (analog/README.md).
//                  No dead zone: the two always-on units keep it running at
//                  code 0, so a dead ring is distinguishable from code 0.
//                  The input capacitance doubles per bit (code[7] is over a
//                  picofarad); the Liberty file carries the measured values
//                  and the flow sizes the drivers from it.
//   enable         1 = oscillate, 0 = the NAND holds the loop and clk_out
//                  rests high, like the standard-cell rings.
//   clk_out        the ring through a two-inverter buffer. A free-running
//                  clock, declared as one in src/constraints.sdc.
//   VPWR / VGND    not ports here. The tile's PDN reaches the macro's Metal4
//                  bars through PDN_MACRO_CONNECTIONS in src/config.json, and
//                  the flow adds the power pins to the physical netlist from
//                  the LEF. (Declaring them under USE_POWER_PINS only earns a
//                  PINMISSING lint warning from every instance.)
//
// Simulation
//   With SIM defined (iverilog testbenches, cocotb at RTL and at gate level)
//   the body is the behavioural model with the macro's simulated end points.
//   ring_model's curve is quadratic where the real block is nearly linear;
//   the testbenches read the model's own freq_of_code, so the shape does not
//   matter to them. The macro's real curve is in analog/README.md.
// ============================================================================
`default_nettype none

/* verilator lint_off UNUSEDSIGNAL */
/* verilator lint_off UNDRIVEN */
(* blackbox *)
module tt_analog_ring (
    input  wire [7:0] code,     // a blackbox uses nothing and drives nothing:
    input  wire       enable,   // the linter is told so
    output wire       clk_out
);
/* verilator lint_on UNDRIVEN */
/* verilator lint_on UNUSEDSIGNAL */

`ifdef SIM
  ring_model #(
      .F_MIN_HZ  (2.0e6),
      .F_MAX_HZ  (164.0e6),
      .DEAD_CODE (0)
  ) u_model (
      .code    (code),
      .enable  (enable),
      .clk_out (clk_out)
  );
`endif

endmodule

`default_nettype wire
