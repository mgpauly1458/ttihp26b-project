// tt_analog_ring.v -- slot 7, the hand-drawn analog ring: a HARD MACRO, not RTL (analog/README.md)
//   11-stage current-starved ring, 255 binary-weighted unit NMOS switched by the code bits plus two always-on units.
//   code    [7:0]  bit 7 widest; higher = more current = faster. Post-layout typical 27 C: 2.0 MHz at code 0,
//                  18 MHz at 16, 164 MHz at 255 (pre-layout twice as fast). No dead zone: a dead ring differs from code 0.
//                  Input capacitance doubles per bit (code[7] > 1 pF); analog/lib/*.lib carries it, the flow sizes drivers.
//   enable         1 = oscillate; 0 = the NAND holds the loop, clk_out rests high
//   clk_out        ring through a two-inverter buffer; declared a clock in src/constraints.sdc
//   VPWR / VGND    not ports: PDN_MACRO_CONNECTIONS in src/config.json reaches the Metal4 bars and the flow adds the
//                  power pins from the LEF (under USE_POWER_PINS they only earn PINMISSING lint warnings)
// - (* blackbox *): yosys keeps the instance and nothing else; LEF from analog/macro/, .lib from analog/lib/,
//   placement from MACROS in src/config.json.
// - -DSIM (iverilog, cocotb at RTL and gate level) gives a ring_model body with the macro's end points; its curve is
//   quadratic where the block is nearly linear, which the benches do not depend on (they read freq_of_code).
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
