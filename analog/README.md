# The analog block

The hand-drawn CMOS inverter that the digital tile imports as a hard macro.
This directory owns the block and nothing else: the tile is hardened by
LibreLane from the repository root (`make -C .. harden`), and the only things
it needs from here are three committed files.

| committed | is | built by |
|---|---|---|
| `macro/tt_analog_inverter.gds` | the layout | `make gds` |
| `macro/tt_analog_inverter.lef` | its abstract, for placement and routing | the same script, from the same constants |
| `lib/tt_analog_inverter.lib` | its timing, for synthesis and STA | `make lib` |

They are in git because CI has no KLayout, no PDK PCell library and no ngspice.
Everything else here is scratch and lives in the gitignored `out/`.

Everything runs inside the `hpretl/iic-osic-tools` container via `./run.sh`, so
Docker is the only host dependency.

```bash
cd analog
make help       # every target, one line each
make macro      # gds + lib + drc + lvs: what the tile needs
make design     # netlist + sim + gds + drc + lvs: is the block right?
```

| step | does |
|---|---|
| `make netlist` | xschem → SPICE, both the simulation and the LVS netlist |
| `make sim` | ngspice DC sweep + transient |
| `make plot` | waveform figure → `../docs/inverter_sim.png` |
| `make gds` | layout → `macro/*.gds` and `macro/*.lef` |
| `make lib` | ngspice characterisation → `lib/*.lib` |
| `make drc` | KLayout DRC, sg13g2 maximal rule set |
| `make lvs` | KLayout LVS, layout vs schematic |
| `make png` | render the layout |
| `make xschem` / `make klayout` / `make shell` | GUIs and a container prompt |
| `make ci` | latest GitHub Actions results for this branch |

Both PDK runners exit non-zero on failure, so `make` genuinely stops rather than
printing errors and continuing.

Every target takes `CELL=<name>`, so the same commands work for the next block
you add: `layout/build_<cell>.py` builds `out/<cell>.gds`, `xschem/<cell>.sch`
is its schematic and `xschem/<cell>_tb.sch` its testbench.

## What is here

```
xschem/inverter.sch          the circuit: two transistors
xschem/inverter_tb.sch       its testbench: DC sweep and transient
xschem/tt_analog_inverter.sch  the macro wrapper - renames the pins to A, Y,
                             VPWR, VGND, which is what the LEF and the tile use
layout/build_tt_analog_inverter.py   the layout AND the LEF, from one set of
                             constants, so the two cannot drift apart
char/characterize.py         ngspice sweep -> Liberty NLDM tables
sim/plot.py                  waveform figures
layout/render.py             layout figures
layout/build_glb.py          glTF export, for looking at it in 3D
layout/build_gds3d_tech.py   generates GDS3D's process file from the PDK's own
                             KLayout 2.5D stack
```

## Shaped like a standard cell

The macro is 20.16 × 22.68 µm — 42 CoreSite widths by 6 rows — so it lands
row-aligned in the tile's floorplan.

**It has no Metal1 power rails.** The obvious idea, rails on every row boundary
so the PDN's own rails abut them, does not survive contact with a block this
size: a full-width rail crosses the core, and LVS extracts one merged `VPWR|Y`
net. The supplies are instead two horizontal Metal4 bars spanning the full
width, which `PDN_MACRO_CONNECTIONS` vias up to the tile's TopMetal1 grid.
Horizontal, because a vertical strap only meets a vertical grid where the pitch
happens to line up — and when it did not, IR analysis failed on VPWR while VGND
was fine.

**It is shielded and boxed in.** A continuous p+ guard ring tied to VGND
surrounds the core, and the LEF declares the whole footprint as an obstruction
on Metal1 through Metal4, so no tile route crosses the block on any signal
layer. Only the power grid passes over it, on TopMetal1.

`A` and `Y` are Metal2 pins on the west and east edges, brought in from the
core's Metal1 pads by a via stack.

## Characterisation is measured, not asserted

`char/characterize.py` runs the real transistor-level netlist through ngspice on
a 4 × 4 grid of input slew against output load, using the PDK's own axes and its
own 50 % / 20-80 % thresholds, and writes the result as an NLDM table. It also
measures input capacitance by integrating the current into the gate over a slow
ramp.

Numbers at the typical corner, 1.2 V, 25 °C:

| | |
|---|---|
| trip point | 618 mV against an ideal 600 mV |
| peak gain | −17.2 |
| input capacitance | 5.98 fF |
| delay | 17 ps into a minimum load, 53 ps into 23 fF |

Only `mos_tt` is characterised, so the same table is handed to every STA corner.
A fuller job would emit slow and fast libraries from `cornerMOSlv.lib` and key
`MACROS.lib` by corner instead of `"*"`.

## Looking at it in 3D

Four, one of which you already have without doing anything. The three local ones
all show the same stack, because they all read the same layer heights.

| | needs a display | |
|---|---|---|
| Tiny Tapeout's viewer | no | already published by CI — see below |
| `make d25` | yes | KLayout's 2.5D view, driven by the PDK's own BEOL stack |
| `make view3d` | yes | GDS3D, a standalone 3D GDS viewer |
| `make glb` | **no** | writes `out/*.glb` for any glTF viewer, browser or phone |

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
it: the view renders the current selection.

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
ignored and the extracted netlist comes back with unnamed nets. The macro names
`A` and `Y` on Metal2 and its supplies on Metal4, matching the layer each net
actually sits on.

**The PMOS and NMOS symbols have opposite D/S pin order** — the PMOS puts its
source at the top, the sensible convention but the reverse of the NMOS. Placing
both at the same rotation silently gives a PMOS with its source on the output
node. Read the netlist, not the picture.

## Getting a macro through the digital flow

These are the failures that came from the block being *imported* rather than
being the top level. The tile's own traps are in `../CLAUDE.md`.

**Signoff DRC is stricter than this directory's.** `make drc` runs KLayout's
sg13g2 deck; the tile's signoff runs Magic's, and Magic checks rules KLayout
does not. The one that bit: the `ntap1` PCell draws a 1.26 µm `nBuLay` square —
it is the PDK's well-tap *device*, with `R` and `Rspec` parameters, not a plain
tie — and Magic measures it against the PMOS's own p+ diffusion 0.34 µm away.
33 `NBL.f` violations, none of them fixable by moving anything. The layout
generator strips `nBuLay`, the same way it strips `HeatTrans`.

**Write the GDS with `write_context_info` disabled.** KLayout otherwise emits a
hidden `$$$CONTEXT_INFO$$$` cell holding PCell parameters, which counts as a
second top-level cell. LibreLane's render step fails with "the layout has
multiple top cells", and Tiny Tapeout's precheck reads the wrong cell for its
boundary and analog-pin checks.

**Strip `HeatTrans` (51/0).** The device PCells draw it, it is not on Tiny
Tapeout's allowed layer list, and it plays no part in DRC or LVS.

**Contacts must not meet at a right angle.** Two rows of guard-ring contacts
meeting at a corner merge into an L, and every contact rule (`Cnt.b`, `CntB.a`,
`CntB.a1`, `CntB.b2`, `M1.c1`) is written for a square. The vertical edges own
the corners; the horizontal ones stop short.

**An `Activ` with no `pSD` over it is n+.** A hand-drawn p+ guard ring needs the
implant layer drawn explicitly, or it is the opposite of a substrate tie.

**The PMOS and NWell-tap PCells each draw their own NWell**, and where the two
meet the tie ends up only marginally enclosed, tripping `NW.d` (min NWell space
to external N+ Activ, 0.31 µm). One generous well over the whole p-side fixes
it.

**Give the LEF pins antenna areas.** `ANTENNAGATEAREA` on `A`,
`ANTENNADIFFAREA` on `Y`, measured off the devices. Without them OpenROAD warns
that the pins "might not be connected to a gate" and skips antenna checking on
every net that reaches them.

**Do not give the Liberty an `operating_conditions` group.** OpenSTA derives its
corner ("scene") names from the libraries it reads, and a macro library that
declares its own conditions makes it look for a scene the PDK's corners do not
define. Every STA corner then fails, before placement, with a message that names
a hash rather than anything you wrote.
