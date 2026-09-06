# Analog source for this tile

The submitted artefacts — `gds/tt_um_mgpauly1458_inverter.gds` and the matching
`lef/` file — are generated from this directory. Everything runs inside the
`hpretl/iic-osic-tools` container via `./run.sh`, so Docker is the only host
dependency.

```bash
cd analog
make help       # every target, one line each
make all        # both pipelines, end to end
```

Two pipelines, answering different questions:

| target | what it answers | steps |
|---|---|---|
| `make design` | is the circuit right, and does the layout match it? | netlist → sim → gds → drc → lvs |
| `make tt` | will Tiny Tapeout accept it? | drc → lvs → precheck |

They overlap on DRC and LVS but are not the same check. This design was DRC and
LVS clean long before precheck passed; everything that remained was about how
the GDS is *written*, not about the circuit.

| step | does |
|---|---|
| `make netlist` | xschem → SPICE, both the simulation and the LVS netlist |
| `make sim` | ngspice DC sweep + transient |
| `make plot` | waveform figure → `../docs/inverter_sim.png` |
| `make gds` | layout → `../gds/*.gds` and `../lef/*.lef` |
| `make drc` | KLayout DRC, sg13g2 maximal rule set |
| `make lvs` | KLayout LVS, layout vs the xschem netlist |
| `make precheck` | local stand-in for TT's GDS prechecks |
| `make png` | render the layout |
| `make xschem` / `make klayout` / `make shell` | GUIs and a container prompt |
| `make ci` | latest GitHub Actions results for this branch |

Both PDK runners exit non-zero on failure, so `make` genuinely stops rather than
printing errors and continuing.

## What is here

```
xschem/inverter.sch                     the inverter cell
xschem/inverter.sym                     its symbol
xschem/inverter_tb.sch                  testbench: DC sweep and transient
xschem/tt_um_..._inverter.sch           tile wrapper, renames the ports to
                                        ua[0]/ua[1]/VDPWR/VGND for LVS
layout/build_gds.py                     builds the core and the tile, and
                                        emits the LEF from the same constants
layout/render.py                        layout -> PNG
sim/plot.py                             waveform figure
checks/tt_precheck.py                   local stand-in for TT's GDS prechecks
checks/tt_valid_layers.txt              allowlist vendored from tt-support-tools
tech/tt_analog_1x2.def                  TT's tile template; pin names, layers
                                        and positions are parsed from it
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

## Getting through Tiny Tapeout's precheck

The design was DRC and LVS clean well before precheck passed. Every remaining
failure was about how the GDS is *written*, not about the circuit. In order:

**Every LEF port must also be a polygon on the matching `<layer>.pin`** (50/2
for Metal4, 126/2 for TopMetal1) containing the LEF rectangle. `pin_check`
verifies exactly that, so both come from one table in `build_gds.py`.

**The LEF must declare all 51 interface pins**, not just the ones the design
uses — `clk`, `ena`, `rst_n`, every `ui_in`/`uo_out`/`uio_*` and all eight
`ua[]`. They are parsed straight out of `tech/tt_analog_1x2.def` so the names,
layers and positions cannot disagree with the shuttle.

**Power goes on TopMetal1 and must be at least 2.1 µm wide.** The published
analog spec says Metal4 and 1.2 µm, but that is the sky130 guidance; precheck
is the authority for IHP.

**The boundary layer is `prBoundary.boundary` (189/4)**, not `.drawing`
(189/0), which is not on the allowed layer list.

**Strip `HeatTrans` (51/0).** The device PCells draw it and it is not on the
allowed list. It plays no part in DRC or LVS.

**Write the GDS with `write_context_info` disabled.** KLayout otherwise emits a
hidden `$$$CONTEXT_INFO$$$` cell holding PCell parameters. `gdstk`, which
precheck uses, counts it as a second top-level cell and fails the boundary
check — and because `analog_pin_check` inspects `top_level()[0]`, it was
examining that cell rather than the tile and wrongly reported `ua[0]` as
unconnected. One flag fixes two confusing failures.

**An unused `ua[]` pin must have no metal within 0.5 µm of it.** The check
builds a ring 0.1–0.5 µm outside each pad and treats any TopMetal1 there as a
connection, cross-checked against `analog_pins` in `info.yaml`. Drawing the pad
rectangle itself is fine; overhanging it by more than 0.1 µm counts as wired.

`make precheck` (`checks/tt_precheck.py`) reproduces the layer, boundary, pin
and analog-pin checks locally, which is worth it — a CI round trip is about
seven minutes. It is a convenience, not the authority: CI runs the real
precheck, which also does DRC, zero-area, cell-name and Verilog-syntax checks.

**The PMOS and NWell-tap PCells each draw their own NWell**, and where the two
meet the tie ends up only marginally enclosed, tripping `NW.d` (min NWell space
to external N+ Activ, 0.31 µm). One generous well over the whole p-side fixes
it.
