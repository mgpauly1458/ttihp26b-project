<!---
This file is published as your project page. Keep the section headings; the
docs workflow checks for them.
-->

## How it works

A digital tile with a hand-drawn analog block inside it.

The Verilog top level is the whole tile. LibreLane hardens it, and while doing
so it places a **hard macro** — a CMOS inverter laid out by hand in the
`ihp-sg13g2` PDK — into the standard-cell array, routes to it, and runs its
power grid over it. The design then does the one thing that makes such a pairing
worth having: it computes the same inversion twice, once in silicon drawn by
hand and once in synthesised logic, and brings both answers out to the pins
along with a flag that goes high if they ever differ.

This is a digital submission. No `ua[]` analog pin is used; the analog content
is entirely internal.

### The analog block

A single CMOS inverter — the smallest circuit that still exercises every step of
an analog flow.

- PMOS `sg13_lv_pmos`, W = 2 µm; NMOS `sg13_lv_nmos`, W = 1 µm; both L = 130 nm.
- The 2:1 width ratio puts the switching threshold at 618 mV against an ideal
  600 mV on a 1.2 V supply, with a peak small-signal gain of −17.2.
- Measured input capacitance 5.98 fF; 17 ps of delay into a minimum load,
  53 ps into 23 fF.

The devices come from the PDK's own PCells, so they are correct by construction;
only the interconnect between them is drawn by hand. The block sits inside a
continuous p+ guard ring tied to ground, and its LEF declares the whole
footprint as a routing obstruction on Metal1 through Metal4, so no tile route
crosses it — only the power grid, on TopMetal1 above.

It is 20.16 × 22.68 µm, which is a whole number of standard-cell sites by a
whole number of rows, so it drops into the floorplan like an oversized cell.

### The digital logic

`ui_in[0]` drives the inverter's gate. Its output comes back into the digital
domain — a CMOS drain node is a full-swing signal, so it drives ordinary cell
inputs directly — and appears three ways:

| pin | meaning |
|---|---|
| `uo_out[0]` | the analog inverter's output, combinationally |
| `uo_out[1]` | the same, registered on `clk` |
| `uo_out[2]` | `~ui_in[0]` computed in standard cells |
| `uo_out[3]` | high when the analog and logic answers disagree |

`uo_out[3]` is the interesting pin on silicon: it is the built-in self-check.

The register is not decoration — it forces clock tree synthesis and static
timing analysis to run rather than the design collapsing into a wire.

## How to test

Drive `ui_in[0]` and watch `uo_out`.

1. Hold `rst_n` low, then release it. `uo_out[1]` clears to 0.
2. With `ui_in[0]` low, `uo_out[0]` and `uo_out[2]` should both read 1;
   with it high, both should read 0.
3. `uo_out[3]` should stay low throughout. If it goes high, the hand-drawn
   inverter and the synthesised one disagree — which is the measurement this
   project exists to make.
4. Clock `clk` (up to 50 MHz) and `uo_out[1]` follows `uo_out[0]` one edge late.

No analog instrumentation is needed: everything is observable on the digital
pins.

## External hardware

None.
