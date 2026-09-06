<!---
This file is published as your project page. Keep the section headings; the
docs workflow checks for them.
-->

## How it works

Two inverters that arrive at the same tile by completely different routes: one
drawn by hand as a custom analog layout, one written in Verilog and hardened by
LibreLane. They share the tile, the supply and the substrate, and nothing else —
no signal crosses between them. That is deliberate. The point of the project is
to prove out both flows and the merge between them, and the smallest honest
mixed-signal design is the one where each half can still be verified on its own.

### The analog half

A single CMOS inverter, laid out by hand in the `ihp-sg13g2` PDK.

- PMOS `sg13_lv_pmos`, W = 2 µm; NMOS `sg13_lv_nmos`, W = 1 µm; both L = 130 nm.
- The 2:1 width ratio puts the switching threshold at 618 mV against an ideal
  600 mV on a 1.2 V supply, with a peak small-signal gain of −17.2.
- Simulated delay into a 10 fF load is 38.5 ps falling and 36.9 ps rising.

The devices come from the PDK's own PCells, so they are correct by
construction; only the interconnect between them is drawn by hand.

### The digital half

`ms_hello`, written in Verilog and taken through synthesis, placement, clock
tree synthesis and routing by LibreLane into a 50 × 50 µm macro, which is then
merged into the tile. Six logic cells survive — an inverter, a reset flip-flop
and four buffers the tool inserted to drive the output pins — alongside the
usual filler and decap:

- `uo[0]` = `~ui[0]`, combinational.
- `uo[1]` = `~ui[0]`, registered on `clk`, cleared by `rst_n`.

The registered copy is there so the flow has to run clock tree synthesis and
static timing analysis rather than collapsing the whole design to a single gate.

### Verification

The merged tile is DRC clean against the sg13g2 maximal rule set, and LVS clean
in strict port mode against a reference netlist that contains both halves — the
analog inverter from its xschem schematic and the digital macro expanded to the
PDK's transistor-level standard cells. That single LVS run is what actually
checks the merge: that each digital net reaches the pin it is supposed to, that
both blocks are on the right supply, and that the unused outputs really are tied
to ground.

## How to test

The two halves are tested independently.

**Analog.** `ua[1]` is the input and drives both gates; `ua[0]` is the output,
tied to both drains. Sweep `ua[1]` from 0 V to VDPWR and `ua[0]` should follow
the inverting transfer curve, crossing mid-supply at roughly 0.62 V.

There is no output buffer: `ua[0]` drives the analog pad directly through the
pad's own series resistance, so the edges observed off-chip will be far slower
than the simulated on-chip figures above. For a static sweep this does not
matter.

**Digital.** Drive `ui[0]` and read `uo[0]`, which should be its complement
immediately. Clock `clk` and `uo[1]` should take the same value one cycle later.
Hold `rst_n` low and `uo[1]` goes to 0 regardless of `ui[0]`. All other outputs
are tied to ground on chip.

## External hardware

None. A voltage source on `ua[1]` and a meter or scope on `ua[0]` covers the
analog half; the digital half needs nothing beyond the usual pins.
