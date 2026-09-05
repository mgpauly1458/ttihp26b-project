<!---
This file is published as your project page. Keep the section headings; the
docs workflow checks for them.
-->

## How it works

A single CMOS inverter, laid out by hand in the `ihp-sg13g2` PDK. It is
deliberately the smallest circuit that still exercises every step of the analog
flow — schematic capture, SPICE, layout, DRC and LVS — so that the toolchain and
the submission path can be validated before anything more ambitious is built on
top of them.

- PMOS `sg13_lv_pmos`, W = 2 µm; NMOS `sg13_lv_nmos`, W = 1 µm; both L = 130 nm.
- The 2:1 width ratio puts the switching threshold at 618 mV against an ideal
  600 mV on a 1.2 V supply, with a peak small-signal gain of −17.2.
- Simulated delay into a 10 fF load is 38.5 ps falling and 36.9 ps rising.

The devices come from the PDK's own PCells, so they are correct by
construction; only the interconnect between them is drawn by hand. The layout
is DRC clean against the sg13g2 maximal rule set and LVS clean against the
xschem schematic.

## How to test

`ua[1]` is the input and drives both gates. `ua[0]` is the output, tied to both
drains. Sweep `ua[1]` from 0 V to VDPWR and `ua[0]` should follow the inverting
transfer curve, crossing mid-supply at roughly 0.62 V.

Note there is no output buffer: `ua[0]` drives the analog pad directly through
the pad's own series resistance, so the edges you observe off-chip will be far
slower than the simulated on-chip figures above. For a static sweep this does
not matter.

The digital pins are unused and the tile ignores `clk` and `rst_n`.

## External hardware

None. A voltage source on `ua[1]` and a meter or scope on `ua[0]` is enough.
