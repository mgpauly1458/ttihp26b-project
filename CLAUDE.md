# Tiny Tapeout IHP 26b — working notes

Submission repo for the **TTIHP 26b** shuttle (IHP SG13G2 130 nm, open-source
`ihp-sg13g2` PDK). Not sky130 — there is a separate `tinytapeout-sky-26b`
shuttle, so "26b" alone is ambiguous.

**Shuttle closes 2026-09-21.** Allocation is **2 tiles**.

## What this is

**A digital tile with a hand-drawn analog block inside it.** The Verilog top
level is the whole tile; LibreLane hardens it and places the analog inverter
into it as a hard macro. Digital on top, analog imported — not the other way
round.

Because no `ua[]` pin is used, `analog_pins` is `0` and this is a **digital
submission**: Tiny Tapeout's ordinary `tt-gds-action` builds it, and the repo
never contains a GDS of the tile. That is the whole point of the arrangement.

## Three branches

A Tiny Tapeout repo is *one* project. The alternatives are kept on branches;
merging into `main` is what commits to one.

| branch | project | state |
|---|---|---|
| `main` | the stock digital Verilog template, plus a Basys3 harness in `fpga/` | CI green |
| `digital-top` | **this**: digital tile importing the analog inverter as a macro | hardens, precheck passes, RTL tests pass, all locally |
| `analog-inverter` | the earlier arrangement: analog custom-GDS tile with a LibreLane macro merged *into* it | DRC/LVS/precheck clean; kept as a fallback |

`analog-inverter` is the inverse design and is deliberately preserved. If
something about the macro flow turns out to be unacceptable to the shuttle, it
is a working submission that needs no rework.

## Why the hierarchy can be this way round at all

Tiny Tapeout's digital flow generates `src/user_config.json` from `info.yaml`
and merges it **over** `src/config.json` — but only for the seven keys it owns
(`DESIGN_NAME`, `VERILOG_FILES`, `DIE_AREA`, `FP_DEF_TEMPLATE`, `VDD_PIN`,
`GND_PIN`, `RT_MAX_LAYER`; see `tt-support-tools/project.py:486`). For
`ihp-sg13g2`, `tech.librelane_config` is empty. Everything else you put in
`src/config.json` — `MACROS`, `PDN_MACRO_CONNECTIONS`, halos — survives into
the LibreLane run untouched.

**What is not possible:** a project with analog pins cannot use this flow.
`create_user_config` always picks `tt_block_<tiles>_pgvdd.def` as the floorplan
template, and that template has no `ua[]` pins at all, while `check_ports`
starts *requiring* an `inout ua[8]` port the moment `analog_pins > 0`. Analog-pin
projects must deliver their own GDS through the `custom_gds` action. That is the
constraint that shaped the `analog-inverter` branch, and sidestepping it is
exactly what `analog_pins: 0` buys.

## Tile budget: it is `1x2`, not `2x1`

Two tiles is `tiles: "1x2"` — 202.08 × 313.74 µm, one wide and two tall.
`tt-support-tools/tech/ihp-sg13g2/tile_sizes.yaml` also lists `2x1`, `3x1` etc.,
but there is no matching `tt_block_<size>_pgvdd.def` template for any `Nx1`, so
they cannot be hardened and CI rejects them. Buildable set:
`1x1 1x2 2x2 3x2 3x4 4x2 4x4 5x4 6x2 6x4 8x2 8x4`.

Note also that the 167×108 µm tile quoted throughout Tiny Tapeout's
documentation is *sky130*. On IHP a 1x1 tile is 202.08 × 154.98 µm.

## You never upload a GDS

Push → GitHub Actions builds and checks everything → iterate until green.
Separately, before the deadline, submit the repo **URL** at app.tinytapeout.com;
TT clones and rebuilds it themselves. Green CI *is* the readiness check.

---

# The flow

```
analog/                          the block            xschem, ngspice, KLayout
  xschem/inverter.sch            schematic
  layout/build_tt_analog_inverter.py  layout generator -> macro/*.gds + *.lef
  char/characterize.py           ngspice sweep        -> lib/*.lib
  macro/  lib/                   COMMITTED artefacts

src/                             the tile             LibreLane, via tt-support-tools
  project.v                      TT top level, instantiates the macro
  ms_hello.v                     the logic around it
  tt_analog_inverter.v           blackbox + behavioural model
  config.json                    MACROS, placement, PDN hookup

test/                            cocotb, RTL and gate level
```

Two commands, from the repository root:

```bash
make macro      # analog/: layout, characterisation, DRC, LVS      (Docker)
make harden     # LibreLane the tile around it                     (host venv + Docker)
make precheck   # Tiny Tapeout's own precheck on the result        (Docker)
make test       # cocotb against the RTL                           (host)
make all        # all four
```

`make -C analog help` lists the block-level targets.

## Two toolchains, deliberately

| | runs in | why |
|---|---|---|
| the block (`analog/`) | `hpretl/iic-osic-tools` via `analog/run.sh` | xschem, ngspice and the PDK's KLayout DRC/LVS decks are all there |
| the tile (`make harden`) | host `venv` + LibreLane's **own** container | this is exactly what `tt-gds-action` does in CI, and matching CI is the point |

**Do not harden with the container's LibreLane.** It is a dev build (3.1.0.dev3)
whose OpenSTA disagrees with its own scripts: every STA corner fails with
`_b01c32d530560000_p_Scene is not the name of a scene` before placement even
starts. `pip install librelane==3.0.5` in the venv and let it run dockerized, as
CI does. This cost an hour of chasing a Liberty file that was never the problem.

## The macro's artefacts are committed

`analog/macro/*.gds`, `analog/macro/*.lef` and `analog/lib/*.lib` are **in git**.
CI has no KLayout, no PDK PCell library and no ngspice, so LibreLane has to find
them in the repository. Everything else in `analog/out/` is scratch and ignored.

Rebuild them with `make macro` after touching the layout generator or the
schematic, and commit the result.

---

# What the design is

## The block

A single CMOS inverter, 20.16 × 22.68 µm, shaped so the digital flow can treat
it like an oversized standard cell:

| | |
|---|---|
| devices | `sg13_lv_pmos` W=2 µm, `sg13_lv_nmos` W=1 µm, both L=130 nm |
| supply | 1.2 V |
| trip point | 618 mV vs. ideal 600 mV; peak gain −17.2 |
| input capacitance | 5.98 fF, measured |
| delay | 17 ps into a minimum load, 53 ps into 23 fF |
| footprint | 42 CoreSite widths × 6 rows, so it lands row-aligned |
| pins | `A`, `Y` on Metal2 at the west and east edges; `VPWR`, `VGND` as horizontal Metal4 bars |
| shielding | continuous grounded p+ guard ring; Metal1–Metal4 declared OBS across the whole footprint |

`layout/build_tt_analog_inverter.py` emits the GDS **and** the LEF from the same
constants, so the LEF can never describe geometry the GDS does not have.

`char/characterize.py` measures the Liberty model rather than asserting it: it
sweeps the transistor-level netlist over a 4×4 input-slew × output-load grid on
the PDK's own axes and with the PDK's thresholds, and writes an NLDM table.
Without timing LibreLane cannot synthesise, place or sign off around the macro.

## The tile

`ui_in[0]` drives the macro's gate. Its output returns to the digital domain and
appears on `uo_out[0]` (combinational), `uo_out[1]` (registered on `clk`),
alongside `uo_out[2]` = `~ui_in[0]` in standard cells and `uo_out[3]` = the two
disagreeing. That last pin is the built-in self-check on silicon.

Last clean run: 0 Magic DRC errors, LVS matched uniquely, 0 antenna violations,
setup slack +11.08 ns and hold slack +3.88 ns at a 20 ns period.

**Signoff LVS treats the macro as an empty placeholder** — 0 device instances.
That is correct and normal for a hard macro: the tile's LVS checks the wiring
*to* the macro's pins, and the macro's insides are checked separately by
`make -C analog lvs`, against its own schematic. Do not read "Circuits match
uniquely" as having verified the inverter.

---

# Traps, and what they cost

Each of these produced a confusing failure.

## Getting a macro through LibreLane

**A macro cannot carry standard-cell power rails at this size.** The first
version drew VPWR/VGND as Metal1 rails on every row boundary, hoping to abut the
PDN's own rails. A full-width rail crosses the core: LVS extracted a single
merged `VPWR|Y` net. A hard macro's supplies belong on the PDN layers.

**The macro grid vias between `PDN_VERTICAL_LAYER` and `PDN_HORIZONTAL_LAYER`.**
With `FP_PDN_MULTILAYER: false`, `PDN_HORIZONTAL_LAYER` is used for *nothing
else* — the horizontal stripe and the core ring are both inside the multilayer
branch of `pdn_cfg.tcl`. So setting it to `Metal4` is how the macro's Metal4
power pins get vias up to the TopMetal1 grid, and it changes nothing else. Left
at its `TopMetal2` default, the macro has no layer in common with the grid and
PDN quits with `PDN-0232` then `PDN-0233`.

**Power straps across a macro must run *across* it.** Vertical straps only meet
the tile's vertical grid where the pitch happens to line up. One net connected,
the other did not, and IR analysis failed with `PSM-0069` on VPWR alone.
Horizontal bars spanning the full width are met by any grid strap that crosses
the macro at all. The placement is then chosen so a whole VPWR/VGND pair
(13.6 µm offset, 38.87 µm pitch, 4 µm apart) falls inside the macro's 20.16 µm
width.

**A `"//"` key is only stripped at the top level of the config.** Put one inside
the `MACROS` object and LibreLane rejects the whole file: `one or more keys
unrecognized for dataclass Macro: //`.

**Do not give a macro's Liberty an `operating_conditions` group.** OpenSTA
derives its corner ("scene") names from the libraries it reads, and a macro
library declaring its own conditions makes it look for a scene the PDK's corners
do not define. Every STA corner then fails before placement.

**Give the LEF pins antenna areas.** `ANTENNAGATEAREA` on the input,
`ANTENNADIFFAREA` on the output — measured off the devices, not guessed.
Without them OpenROAD warns that the pins "might not be connected to a gate" and
skips antenna checking on every net that reaches them.

## Signoff DRC, which the block-level deck never runs

**Strip `nBuLay` (32/0) that the `ntap1` PCell draws.** `ntap1` is the PDK's
well-tap *device* — it has `R` and `Rspec` parameters — and draws a 1.26 µm
buried-layer square as part of that device. A plain NWell tie does not need one,
and Magic's signoff DRC measures it against the PMOS's own p+ diffusion 0.34 µm
away: 33 `NBL.f` violations that nothing in the tie can move far enough to
satisfy. KLayout's deck never looks, so this only appears once the tile goes
through LibreLane.

**Write the GDS with `write_context_info` disabled.** KLayout otherwise emits a
hidden `$$$CONTEXT_INFO$$$` cell holding PCell parameters. It counts as a second
top-level cell: LibreLane's render step fails with "the layout has multiple top
cells", and Tiny Tapeout's precheck reads the wrong cell for its boundary and
analog-pin checks.

**Contacts must not meet at a right angle.** Two rows of guard-ring contacts
meeting at a corner merge into an L, and every contact rule (`Cnt.b`, `CntB.a`,
`CntB.a1`, `CntB.b2`, `M1.c1`) is written for a square. Let one direction own
the corners.

**An `Activ` with no `pSD` is n+.** A hand-drawn substrate tie needs the p+
implant drawn over it or it is the opposite of a tie.

## xschem and block-level LVS

**LVS needs a different netlist from simulation.** The IHP symbols carry two
format strings. The default emits `XM1 ... sg13_lv_pmos` — a *subcircuit call*,
correct for ngspice. LVS compares extracted *devices*, reads those X-lines as
subcircuit instances, and fails with no useful diagnostic. Select the
device-line form with `set lvs_netlist 1`; add `set top_subckt 1` to wrap the
top schematic in `.subckt/.ends`.

**Pass `--disable_tap_extraction` to `run_lvs.py`.** Otherwise the well and
substrate ties extract as `ntap1`/`ptap1` *resistors*, with both transistor bulk
terminals on unnamed nets routed through them.

**LVS net labels must be `Text` on a `.text` purpose, one per metal layer:**
`metal1_text = labels(8, 25)`, `metal2_text = labels(10, 25)`,
`metal4_text = labels(50, 25)`. Labels anywhere else are silently ignored and
the extracted netlist comes back with unnamed nets. The macro names `A`/`Y` on
Metal2 and the supplies on Metal4, matching where each net actually is.

**The PMOS and NMOS symbols have opposite D/S pin order.** The PMOS puts its
source at the top — the sensible convention, but the reverse of the NMOS.
Placing both at the same rotation silently gives a PMOS with its source on the
output node. Read the netlist, not the picture.

## Gate-level simulation

**It needs Tiny Tapeout's iverilog 13.** Ubuntu's 12 leaves every flop at X;
the container's 14 will not parse the PDK's cell models. See `test/README.md` —
including why `-gno-specify` makes it worse, not better.

**Stimulus must not land on a clock edge.** `ClockCycles` returns on an edge, so
assigning an input straight afterwards trips `$setuphold` and the flop's
notifier goes X for the rest of the run. RTL simulation does not care, which is
how a test passes at RTL and fails at gate level.

---

# Seeing it

| | needs a display | |
|---|---|---|
| TT's hosted viewer | no | published by CI, links in the Actions summary |
| `make view` | **no** | glTF export of the hardened tile |
| `make -C analog d25` | yes | KLayout 2.5D view, PDK's own BEOL stack |
| `make -C analog view3d` | yes | GDS3D |

`docs/tile_layout.png` is the hardened tile, `docs/macro_layout.png` and
`docs/inverter_layout.png` the block.

All three local viewers read the same layer heights: KLayout's from
`libs.tech/klayout/tech/d25/sg13g2_beol.lyd25`, and GDS3D's process file is
*generated* from that same file by `analog/layout/build_gds3d_tech.py`, because
no open PDK in the container ships one.

## X11 out of the container: fixed, and how it broke

**Snap-packaged Docker cannot see `/tmp`.** Both a snap `docker` and an apt
`docker-ce` were installed, and the snap daemon owned `/var/run/docker.sock`.
Snap confinement only lets paths under `$HOME` through, so
`-v /tmp/.X11-unix:/tmp/.X11-unix` silently mounted an *empty* directory. Qt's
account of this is worthless: "could not load the Qt platform plugin xcb", then
a segfault.

Resolved on 2026-09-06 with:

```
sudo snap stop --disable docker
sudo systemctl restart docker.socket docker.service
```

The second command matters: stopping the snap daemon deletes `/run/docker.sock`,
and `docker.socket` goes on reporting itself active while the file is gone.

**Pass `--device /dev/dri`**, or Mesa falls back to `llvmpipe` software
rendering. `analog/gui.sh` does this, and probes the display first so a failure
says which of the two causes it was.

---

# Not done yet

- **Parasitic extraction.** The container has kpex 0.3.15, which supports this
  PDK: `kpex --pdk ihp-sg13g2 --gds ... --2.5D`. The intended shape is a
  `make pex` producing `*_pex.spice` and a `make sim-post` running the existing
  testbench against it. On this block it will barely matter — the inverter is a
  few µm across — but it is the missing step before a block with real internal
  routing.
- **Corners.** Only `mos_tt` is characterised, so the Liberty is a typical-corner
  model used at every STA corner. `cornerMOSlv.lib` also provides slow and fast;
  a proper job emits three `.lib` files and keys `MACROS.lib` by corner instead
  of `"*"`.
- **The macro is not in the tile's LVS.** See above. Making it so would mean
  handing `MACROS.spice` a transistor-level view and getting magic to extract
  the macro's GDS rather than its abstract.
- **Density / fill.** Block DRC runs with `--no_density`. The flow's own signoff
  DRC passes on the tile, which is the run that counts, but the block on its own
  has never been checked against density rules.
- **Deleting a stray repo.** `mgpauly1458/ihp-sg13g2-inverter` was created early
  on and is superseded. Private but not deleted; `gh` lacks the scope:
  `gh auth refresh -h github.com -s delete_repo && gh repo delete mgpauly1458/ihp-sg13g2-inverter --yes`

---

# Conventions

- `analog/macro/`, `analog/lib/` and `docs/*.png` are committed; `analog/out/`,
  `runs/`, `tt_submission/` and `tt/` are not.
- `tt/` is *cloned*, not vendored, so that what runs locally is what runs in CI.
  `make tools` sets it up along with the venv.
- The RTL lives in `src/`, because Tiny Tapeout expects it there and
  `info.yaml` lists it.
- Don't hand-edit `analog/macro/*.lef` — it is generated by `make -C analog gds`
  from the same constants as the GDS.
- `src/config.json` is the template's file with a mixed-signal block appended.
  The "do not edit" banner at its top applies to the values above that block.
