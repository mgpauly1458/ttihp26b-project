# Analog source, and the tile merge

The submitted artefacts — `gds/tt_um_mgpauly1458_inverter.gds` and the matching
`lef/` file — are generated from this directory. It owns the analog inverter
*and* the assembly of the whole tile; the digital half is built next door in
`../digital` and arrives here as a macro GDS. Everything runs inside the
`hpretl/iic-osic-tools` container via `./run.sh`, so Docker is the only host
dependency.

```bash
cd analog
make help       # every target, one line each
make all        # both pipelines, end to end
```

`make gds` depends on `../digital/out/ms_hello.gds` and builds it if it is
missing, so the ordering between the two flows takes care of itself.

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
| `make macro` | build the digital half in `../digital` (LibreLane) |
| `make gds` | analog + digital macro → `../gds/*.gds` and `../lef/*.lef` |
| `make tile-netlist` | whole-tile LVS reference: analog + digital |
| `make drc` | KLayout DRC, sg13g2 maximal rule set |
| `make lvs` | KLayout LVS, whole tile vs the analog + digital netlist |
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
xschem/tt_um_..._inverter.sch           analog wrapper, renames the ports to
                                        ua[0]/ua[1]/VDPWR/VGND for LVS
layout/build_gds.py                     builds the core, merges the digital
                                        macro, routes the tile, and emits the
                                        LEF from the same constants
layout/render.py                        the three figures in ../docs
layout/build_gds3d_tech.py              GDS3D process file, from the PDK stack
layout/build_glb.py                     3D model export, no display needed
sim/plot.py                             waveform figure
checks/build_tile_netlist.py            whole-tile LVS reference netlist
checks/tt_precheck.py                   local stand-in for TT's GDS prechecks
checks/tt_valid_layers.txt              allowlist vendored from tt-support-tools
tech/tt_analog_1x2.def                  TT's tile template; pin names, layers
                                        and positions are parsed from it
tech/sg13g2_gds3d.txt                   generated GDS3D process file
```

## Tile construction

The tile is 202.08 × 313.74 µm, matching `tt_analog_1x2.def`. It holds two
independent blocks that share only the supply and the substrate:

- **`inverter_core`**, bottom right — the hand-drawn analog inverter.
- **`ms_hello`**, upper left — the LibreLane macro, read in from
  `../digital/out/ms_hello.gds`.

Both are small, so most of the tile is empty and the work is in getting nets out
to where Tiny Tapeout expects them.

### The analog nets

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

### The digital nets, and the one idea that makes them tractable

The macro's pins are on its north edge; the tile's digital interface stubs are
0.3 µm Metal4 tabs along the top edge of the die. Five signals have to get from
one to the other, and eighteen unused outputs have to reach ground, across a
region also crossed by two full-height TopMetal1 power stripes.

Routed on a single layer this is a real puzzle: every horizontal run blocks
every vertical run that has to cross it, and the ordering constraints do not
always have a solution. Splitting the two directions across layers makes it
disappear.

| | |
|---|---|
| Metal4 | vertical, interface stub down to the bus |
| Metal3 | horizontal, one bus per net, each at its own `y` |
| Metal2 | vertical, bus down to the macro pin |

Now a vertical run may cross any bus it likes. All that is left is bus-to-bus
spacing — parallel, distinct `y` — and spur-to-spur — parallel, distinct `x` —
and both fall out for free.

The supplies need the same trick for a different reason. The macro's straps
interleave VPWR, VGND, VPWR, VGND, so a horizontal bar on one layer cannot reach
both nets without crossing the other. The two feeds therefore leave the macro on
different layers in the empty band below it — VGND on Metal4, VPWR on Metal3 —
and VGND's bar passes *under* the VDPWR TopMetal1 stripe on the way across,
which is only harmless because it is not on TopMetal1.

### The unused outputs

The analog spec is explicit: "Connect any unused `uo_out`, `uio_out` and
`uio_oe` pins to GND." Eighteen stubs comb down onto one Metal3 bus that ends on
the VGND stripe. Easy to miss on a design that uses no digital pins at all, and
none of the prechecks test for it.

## Looking at the tile in 3D

Four, one of which you already have without doing anything. The three local ones
all show the same stack, because they all read the same layer heights.

| | needs a display | |
|---|---|---|
| Tiny Tapeout's viewer | no | already published by CI — see below |
| `make d25` | yes | KLayout's 2.5D view, driven by the PDK's own BEOL stack |
| `make view3d` | yes | GDS3D, a standalone 3D GDS viewer |
| `make glb` | **no** | writes `out/tile_3d.glb` for any glTF viewer, browser or phone |

**Start with Tiny Tapeout's.** The `viewer` job in `.github/workflows/gds.yaml`
already runs on every push: it uploads the tile to `gds-viewer.tinytapeout.com`
(3D) and `gds-explorer.tinytapeout.com` (layer-by-layer), and publishes a
redirect to them on this repo's GitHub Pages. The links are also printed in the
Actions run summary. Nothing to install, and it is the same view the shuttle
sees. The local viewers are for iterating without a seven-minute round trip.

`make d25` passes `-n sg13g2`, which loads the PDK *technology* rather than just
its layer colours — that is what registers the 2.5D macro, and `-l <lyp>` alone
does not. Once KLayout is up the entry is under
**`sg13g2_menu > SG13G2 PDK > BEOL 2.5D Viewer`**. Select a region before opening
it: the view renders the current selection, and the whole tile at once is mostly
empty space.

GDS3D is installed in the container and the container even ships a wrapper for
it, but the wrapper wants `$PDKPATH/libs.tech/gds3d/gds3d_tech.txt` and **no open
PDK here provides one** — not ihp-sg13g2, not sky130A, not gf180mcuD. So
`tech/sg13g2_gds3d.txt` is generated by `layout/build_gds3d_tech.py` from
`libs.tech/klayout/tech/d25/sg13g2_beol.lyd25`, which is the PDK's definition of
the same stack for KLayout. Two formats, one source of truth. It is committed —
it is a tool configuration, not a build artefact — and `make gds3d-tech`
regenerates it.

The two formats do not line up exactly. The KLayout stack computes some entries
with boolean algebra (a contact landing on poly versus one landing on active;
GatPoly split four ways by which resistor module sits on it) and GDS3D maps one
raw layer/datatype to one slab with no booleans. Those are flattened, and the
generator refuses to guess: an expression that is neither a plain `input()` nor
listed in its `FLATTEN` table is an error, so a PDK revision cannot silently
produce a wrong stack.

One entry is not from the PDK. The stack is BEOL only, so the NWell under the
PMOS would not be drawn at all — a conspicuous hole in a picture of two
transistors. It is added below the surface and labelled in the generated file as
illustrative rather than a process number. Nothing else is invented.

`gui.sh` passes `--device /dev/dri` when the render nodes exist. Without it Mesa
cannot load the platform driver and quietly falls back to `llvmpipe` — software
rendering, which works but crawls. With it, this machine reports
`Mesa Intel(R) Iris(R) Xe Graphics`. It also only passes `-t` when there is a
real terminal, so the GUI targets stay usable from scripts.

### If no window appears

`./gui.sh` checks the display before launching, because the native failure is
useless — Qt aborts with "could not load the Qt platform plugin xcb" and then
segfaults, which says nothing about the actual cause. The check reports which of
the two likely causes it is:

- **The mount arrives empty inside the container.** Snap-packaged Docker cannot
  see `/tmp`; snap confinement only lets paths under `$HOME` through, which is
  why the repo mount works and the X socket does not. If a snap `docker` and an
  apt `docker-ce` are both installed, the snap daemon wins `/var/run/docker.sock`.
  `sudo snap stop --disable docker && sudo systemctl restart docker` hands it
  back.
- **The socket is visible but refused.** Ordinary X access control: `xhost +local:`.

`make glb` is unaffected by any of this, which is the reason it exists.

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

**LVS net names must be on a `.text` purpose, one per metal layer.** The deck
reads `metal1_text = labels(8, 25)`, `metal3_text = labels(30, 25)`,
`metal4_text = labels(50, 25)` and so on. Labels anywhere else are silently
ignored and the extracted netlist comes back with unnamed nets. The analog nets
are named on Metal1, the digital ones on their Metal4 interface stubs.

**Strip the macro's own labels when merging it.** LibreLane names the macro's
nets, including `clk`, `rst_n` and its supplies, and the standard cells carry
pin labels of their own. Those are the same physical nets the tile labels from
outside, so leaving both in place puts two names on one net; LVS keeps whichever
it likes, and the top level then looks as though it is missing a port.

**Three netlists, three incompatible conventions.** The whole-tile LVS reference
has to reconcile the PDK standard cells (transistor-level, but written as
X-prefix subcircuit calls), the LibreLane macro netlist (right structure, but
every standard cell is an empty black box) and the xschem inverter (already in
the right form). `checks/build_tile_netlist.py` does the reconciling; the
X-versus-M trap above is the same one, met a second time.

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
