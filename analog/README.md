# Analog source for this tile

The submitted artefacts — `gds/tt_um_mgpauly1458_inverter.gds` and the matching
`lef/` file — are generated from this directory. Everything runs inside the
`hpretl/iic-osic-tools` container via `./run.sh`, so Docker is the only host
dependency.

```bash
cd analog
make            # netlist, simulate, build GDS+LEF, DRC, LVS
make xschem     # schematic / testbench GUI
make klayout    # layout GUI
```

## What is here

```
xschem/inverter.sch                     the inverter cell
xschem/inverter.sym                     its symbol
xschem/inverter_tb.sch                  testbench: DC sweep and transient
xschem/tt_um_..._inverter.sch           tile wrapper, renames the ports to
                                        ua[0]/ua[1]/VDPWR/VGND for LVS
layout/build_gds.py                     builds the core and the tile, and
                                        emits the LEF from the same constants
sim/plot.py                             waveform figure
```

## Tile construction

The tile is 202.08 × 313.74 µm, matching `tt_analog_1x2.def`. The inverter core
is a few µm across, so almost all of the tile is empty; the work is in getting
the four nets out to where Tiny Tapeout expects them:

- **`ua[0]`, `ua[1]`** — TopMetal1 pads on the bottom edge at x = 191.04 µm and
  166.56 µm, reached by `via_stack` PCells running Metal1 → TopMetal1 and then
  TopMetal1 routing.
- **`VDPWR`, `VGND`** — vertical Metal4 stripes 2 µm wide running the full
  height of the tile, per the analog spec (at least 1.2 µm, starting within
  10 µm of the bottom and reaching within 10 µm of the top).

The input takes `ua[1]` and the output `ua[0]`, which looks backwards until you
notice the geometry: the gate contact leaves the core on the left and the drain
strap on the right, and `ua[1]` is the more leftward pad. Assigning them the
other way round forces the two TopMetal1 routes to cross.

## Things that cost time

**LVS needs xschem's LVS-format netlist, not the simulation netlist.** The IHP
symbols carry two format strings. The default emits `XM1 ... sg13_lv_pmos` — a
subcircuit call, which is what ngspice wants. LVS compares extracted *devices*
and reads those X-lines as subcircuit instances, so it fails with no useful
diagnostic. Select the device-line format with
`xschem -n --tcl "set lvs_netlist 1; set top_subckt 1"`.

**Pass `--disable_tap_extraction` to the LVS runner.** By default the well and
substrate ties extract as `ntap1`/`ptap1` resistor devices with the transistor
bulks on unnamed nets, which no hand-drawn schematic will match.

**LVS net names must be on layer 8/25.** The deck reads them via
`metal1_text = labels(8, 25)`. Labels anywhere else are silently ignored and
the extracted netlist comes back with unnamed nets.

**The PMOS and NMOS symbols have opposite D/S pin order** — the PMOS puts its
source at the top, the sensible convention but the reverse of the NMOS. Placing
both at the same rotation silently gives a PMOS with its source on the output
node. Read the netlist, not the picture.

**The PMOS and NWell-tap PCells each draw their own NWell**, and where the two
meet the tie ends up only marginally enclosed, tripping `NW.d` (min NWell space
to external N+ Activ, 0.31 µm). One generous well over the whole p-side fixes
it.
