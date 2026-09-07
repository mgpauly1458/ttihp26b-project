// ============================================================================
// ring_analog_stub.v -- the custom analog ring (slot 7), as the RTL sees it
// ----------------------------------------------------------------------------
// What it is
//   A placeholder for the hand-drawn current-starved ring oscillator being
//   designed in parallel as a custom GDS macro. The real implementation is
//   transistor-level layout, not Verilog; from this codebase's point of view
//   it is a black box with the same interface as every other ring, and
//   everything downstream is identical whether it is present or not.
//
//   Architecture, for context only: the ring's inverters are starved through
//   a bank of binary-weighted transistors in parallel, each switched
//   directly by one bit of the code. The gates swing rail to rail from
//   digital signals, so there is no analog bias node and no reference
//   voltage. It is digitally controlled, not current-referenced, which is
//   why it can live on a digital tile.
//
// Interface
//   code    [7:0]  all eight bits are used, binary weighted: bit 7 is the
//                  widest starving device. Higher code = more current =
//                  higher frequency. Low codes (all wide devices off) are
//                  expected NOT to oscillate at all -- the dead zone.
//   enable         1 = oscillate
//   clk_out        the ring
//
// What is here now
//   Without SIM: clk_out tied low. The tile hardens and the slot simply
//   reads as a dead ring (timeout_error), which is the correct answer for a
//   ring that is not there.
//   With SIM: the behavioural model with the "headline" curve -- dead below
//   code 20, 20 MHz to 400 MHz, quadratic. This is what the sweep exercises.
//
// When the macro arrives
//   Replace the tie-off with a `(* blackbox *)` declaration and add the
//   macro's GDS, LEF, Liberty and placement to src/config.json under
//   MACROS, exactly as the `main` branch does for its hand-drawn inverter.
//   That branch is the worked example of importing a custom GDS block into
//   this digital flow, including every trap it took to get there. If the
//   shuttle does not accept the macro, leave this file as it is; the slot
//   costs nothing.
//
// What the test plan has to carry
//   * Frequency tracks process, supply and temperature. It is a TRIMMABLE
//     oscillator, not a stable one; its tempco is the baseline a later
//     bandgap-biased version is compared against.
//   * Monotonicity depends on how well the binary weights match -- the same
//     DNL problem as a binary DAC. Non-monotonic steps in the 256-code sweep
//     are a real possible outcome, not an instrument fault. Thermometer
//     coding on the upper bits is the fix if it shows up.
// ============================================================================
`default_nettype none

module ring_analog_stub (
    input  wire [7:0] code,
    input  wire       enable,
    output wire       clk_out
);

`ifdef SIM
  ring_model #(
      .F_MIN_HZ  (20.0e6),
      .F_MAX_HZ  (400.0e6),
      .DEAD_CODE (20)
  ) u_model (
      .code    (code),
      .enable  (enable),
      .clk_out (clk_out)
  );
`else
  // No macro yet: a dead ring. See header.
  assign clk_out = 1'b0;
  wire _unused = &{code, enable};
`endif

endmodule

`default_nettype wire
