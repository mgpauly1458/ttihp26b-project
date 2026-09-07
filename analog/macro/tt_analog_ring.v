// ============================================================================
// tt_analog_ring.v -- the analog ring oscillator macro, as the RTL sees it
// ----------------------------------------------------------------------------
// What it is
//   A hand-generated hard macro (analog/macro/tt_analog_ring.gds + .lef,
//   timing in analog/lib/tt_analog_ring.lib): an 11-stage current-starved
//   ring oscillator whose starving current comes from a binary-weighted
//   bank of 255 unit NMOS transistors switched straight by the code bits,
//   plus two always-on units so code 0 still runs. Everything analog is
//   inside; every port is a rail-to-rail digital signal.
//
// Interface (the same as every other ring in src/rings/)
//   code    [7:0]  binary weighted, bit 7 widest. Higher code = more
//                  current = higher frequency. Simulated (typical corner,
//                  27 C): 3.8 MHz at code 0, 5.8 MHz at 1, 332 MHz at 255.
//                  DC control: change it only while enable is low or
//                  between measurements. Note the input capacitance doubles
//                  per bit (code[7] is over a picofarad); the Liberty file
//                  carries the measured values and the flow sizes the
//                  drivers from it.
//   enable         1 = oscillate, 0 = the NAND holds the loop and clk_out
//                  rests high, like the standard-cell rings.
//   clk_out        the ring through a two-inverter buffer. A free-running
//                  clock: constrain it with create_clock on this pin.
//   VPWR / VGND    only in the physical netlist (USE_POWER_PINS); the
//                  digital flow connects them to the tile PDN through
//                  PDN_MACRO_CONNECTIONS in src/config.json.
//
// Integration
//   1. list this file in info.yaml / the Makefile RTL list, from src/;
//   2. in ring_analog_stub.v replace the tie-off with an instance of this
//      module (keep the `ifdef SIM behavioural model there);
//   3. add MACROS / PDN_MACRO_CONNECTIONS / PDN_HORIZONTAL_LAYER to
//      src/config.json exactly as the inverter on `main` does, pointing at
//      analog/macro and analog/lib;
//   4. SDC: create_clock on the macro's clk_out (analog/README.md).
//
// Simulation
//   This is the blackbox only. With SIM defined the ring slot is modelled by
//   sim/ring_model.v inside ring_analog_stub.v, not here.
// ============================================================================
`default_nettype none

(* blackbox *)
module tt_analog_ring (
`ifdef USE_POWER_PINS
    inout  wire       VPWR,
    inout  wire       VGND,
`endif
    input  wire [7:0] code,
    input  wire       enable,
    output wire       clk_out
);
endmodule

`default_nettype wire
