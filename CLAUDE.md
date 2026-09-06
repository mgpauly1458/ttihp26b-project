# Tiny Tapeout IHP 26b — working notes

Submission repo for the **TTIHP 26b** shuttle (IHP SG13G2 130 nm, open-source
`ihp-sg13g2` PDK). Not sky130 — there is a separate `tinytapeout-sky-26b`
shuttle, so "26b" alone is ambiguous.

**Shuttle closes 2026-09-21.** Allocation is **2 tiles**.

## Two branches, one slot

A Tiny Tapeout repo is *one* project, and digital and analog submissions are
mutually exclusive. Both options are kept alive on separate branches; merging
`analog-inverter` into `main` is what commits to analog.

| branch | project | state |
|---|---|---|
| `main` | digital Verilog (`ttihp-verilog-template`), plus a Basys3 harness in `fpga/` and a cocotb bench in `test/` | CI green |
| `analog-inverter` | **mixed-signal** custom-GDS: a hand-drawn CMOS inverter *and* a LibreLane-hardened RTL inverter in one tile | DRC, LVS and local precheck clean; CI not yet run on the mixed-signal tile |

Only `main` has `test/` and `fpga/`; only `analog-inverter` has `analog/`,
`digital/`, `gds/` and `lef/`. Don't be surprised when a file is missing —
check the branch.

Note the branch name predates the digital half and is now a bit narrow. It is
still a *custom GDS* submission — TT's own digital hardening flow never runs;
LibreLane is invoked locally and its macro is merged into a hand-built tile.

## Tile budget: it is `1x2`, not `2x1`

Two tiles is `tiles: "1x2"` — 202.08 × 313.74 µm, one wide and two tall.
`tt-support-tools/tech/ihp-sg13g2/tile_sizes.yaml` also lists `2x1`, `3x1` etc.,
but there is no matching `tt_block_<size>_pgvdd.def` template for any `Nx1`, so
they cannot be hardened and CI rejects them. Buildable set:
`1x1 1x2 2x2 3x2 3x4 4x2 4x4 5x4 6x2 6x4 8x2 8x4`.

Note also that the 167×108 µm tile quoted throughout Tiny Tapeout's
documentation is *sky130*. On IHP a 1x1 tile is 202.08 × 154.98 µm.

## You never upload a GDS

Push to the repo → GitHub Actions builds and checks everything → iterate until
green. Separately, before the deadline, submit the repo **URL** at
app.tinytapeout.com; TT clones and rebuilds it themselves. Green CI *is* the
readiness check.

---

# The flow (`analog-inverter` branch)

Two halves, two directories, one tile.

| | builds | with |
|---|---|---|
| `digital/` | `ms_hello`, a standard-cell macro, from `src/ms_hello.v` | LibreLane 3.1 |
| `analog/` | the inverter, **and the merged tile** | xschem, ngspice, KLayout |

Both run inside the `hpretl/iic-osic-tools` container via their own `run.sh`,
which mounts the repo root at `/work`. **Docker is the only host dependency** —
the image already ships the `ihp-sg13g2` PDK, LibreLane, xschem, ngspice,
KLayout, magic, netgen and kpex.

```bash
cd analog
make help      # every target, with one-line descriptions
make all       # both pipelines end to end, RTL and schematic through to signoff
```

`analog/Makefile` has a file dependency on `digital/out/ms_hello.gds`, so
`make` in `analog/` builds the digital half first if it is missing. It does not
rebuild it when the RTL changes — run `make macro` (or `cd digital && make`)
after editing `src/ms_hello.v`.

## Two pipelines, deliberately separate

**`make design`** — *is the circuit right, and does the layout match it?*
`netlist → sim → gds → drc → lvs`

**`make tt`** — *will Tiny Tapeout accept it?*
`drc → lvs → precheck`

They overlap on DRC and LVS but answer different questions. A design can be
perfectly correct and still be rejected by precheck, which is exactly what
happened here: the circuit was DRC and LVS clean well before precheck passed,
and every remaining failure was about how the GDS is *written*.

Individual steps: `macro`, `netlist`, `tile-netlist`, `sim`, `plot`, `gds`,
`drc`, `lvs`, `precheck`, `png`. Interactive: `xschem`, `klayout`, `shell`,
`ci`.

`make lvs` now checks the **whole tile** — both blocks and every net of the
merge — against a reference netlist assembled by
`analog/checks/build_tile_netlist.py`. That is the check that actually catches a
mis-wired merge; DRC never will. It runs in strict port mode with
`flag_missing_ports`, and it has been confirmed to have teeth: swapping
`uo_out[0]` and `uo_out[1]` in the reference makes it fail.

Both PDK runners exit non-zero on failure (verified empirically with a
deliberately shorted layout and a mismatched netlist), so `make` genuinely
gates rather than printing errors and carrying on.

## What the current design is

Two inverters that reach the same tile by different routes, sharing only the
supply and the substrate. No signal crosses between them — that is deliberate,
so each half stays independently verifiable.

### The digital half

`src/ms_hello.v`: `y_comb = ~a` combinational, `y_reg` the same inversion
registered on `clk`. The register earns its keep by forcing CTS and STA to run
instead of the design collapsing to one gate. Six logic cells survive — an
inverter, a reset flop and four buffers — in a 50 × 50 µm macro.

`digital/README.md` explains why the LibreLane config departs from the defaults
(absolute die, Metal4-only PDN, `RT_MAX_LAYER` Metal3, all pins north) and lists
the pin coordinates `analog/layout/build_gds.py` hard-codes.

### The analog half

A single CMOS inverter — the smallest circuit that still exercises every step.

| | |
|---|---|
| devices | `sg13_lv_pmos` W=2 µm, `sg13_lv_nmos` W=1 µm, both L=130 nm |
| supply | 1.2 V (`sg13g2_stdcell_typ_1p20V_25C.lib`) |
| trip point | 618 mV vs. ideal 600 mV |
| peak gain | −17.2 |
| t_PHL / t_PLH into 10 fF | 38.5 ps / 36.9 ps |
| pins | `ua[1]` = input (gate), `ua[0]` = output (drain) |

The devices are PDK PCells, so they are correct by construction; only the
interconnect is hand-drawn. `analog/layout/build_gds.py` builds the core, merges
the macro, routes the tile and emits the LEF **from the same constants**, so the
LEF can never describe geometry the GDS does not have.

### The merge

The routing works because the two directions are on different layers: Metal4
vertical from the top-edge interface stubs, Metal3 horizontal (one bus per net,
each at its own `y`), Metal2 vertical down to the macro pins. A vertical run may
then cross any bus. On one layer the ordering constraints do not always have a
solution; this is the whole trick. The supplies split the same way — VGND leaves
the macro on Metal4, VDPWR on Metal3 — because the macro's straps interleave and
a single-layer bar cannot reach one net without shorting the other.

The eighteen unused digital outputs are tied to VGND, which the analog spec
requires ("Connect any unused `uo_out`, `uio_out` and `uio_oe` pins to GND") and
no precheck tests for.

---

# Traps, and what they cost

Each of these produced a confusing failure. They will all recur on the next
block. `analog/README.md` has the same list with more context.

## xschem and LVS

**LVS needs a different netlist from simulation.** The IHP symbols carry two
format strings. The default emits `XM1 ... sg13_lv_pmos` — a *subcircuit call*,
correct for ngspice. LVS compares extracted *devices*, reads those X-lines as
subcircuit instances, and fails with no useful diagnostic. Select the device-line
form with `set lvs_netlist 1`; add `set top_subckt 1` to wrap the top schematic
in `.subckt/.ends`. `make netlist` produces both.

**Pass `--disable_tap_extraction` to `run_lvs.py`.** Otherwise the well and
substrate ties extract as `ntap1`/`ptap1` *resistors*, with both transistor bulk
terminals on unnamed nets routed through them. No hand-drawn schematic matches
that.

**LVS net labels must be `Text` on a `.text` purpose, one per metal layer.**
The deck defines `metal1_text = labels(8, 25)`, `metal2_text = labels(10, 25)`,
`metal3_text = labels(30, 25)`, `metal4_text = labels(50, 25)`,
`topmetal1_text = labels(126, 25)`, and attaches each with
`connect(<layer>_con, <layer>_text)`. Labels anywhere else are silently ignored
and the extracted netlist comes back with unnamed nets. The analog nets are
named on Metal1, the digital ones on their Metal4 interface stubs.

**The PMOS and NMOS symbols have opposite D/S pin order.** The PMOS puts its
source at the top — the sensible convention, but the reverse of the NMOS.
Placing both at the same rotation silently gives a PMOS with its source on the
output node. Read the netlist, not the picture.

## Merging a LibreLane macro into a hand-built tile

**Strip the macro's labels, or the top level loses ports.** LibreLane names the
macro's nets — `clk`, `rst_n`, the supplies — and the standard cells carry pin
labels of their own, on 8/25, 10/25, 30/25 and 50/25. Those are the same
physical nets the tile labels from outside, so leaving both in place puts two
names on one net; LVS keeps whichever it likes and the top level then looks as
though a port is missing. `build_gds.py` clears them from the macro cell and
every cell it calls.

**Strip the macro's `prBoundary` too.** It would otherwise sit inside the tile's
own boundary as a second, smaller boundary rectangle — exactly what TT's
boundary precheck inspects.

**Three netlists, three incompatible conventions.** A whole-tile LVS reference
has to reconcile the PDK standard cells (transistor-level, but written as
`X`-prefix subcircuit calls), the LibreLane macro netlist (right structure, but
every standard cell is an *empty black-box* subcircuit) and the xschem inverter
(already right). `checks/build_tile_netlist.py` rewrites the first to `M`-prefix
device lines, drops the black boxes from the second so the real cells are
picked up, and writes a new top level. The `X`-versus-`M` trap is the same one
xschem sets, met a second time.

**Don't leave the unused digital outputs floating.** The analog spec says to tie
`uo_out`, `uio_out` and `uio_oe` to GND. Nothing in DRC, LVS or precheck checks
this, so it is silent until it is silicon.

**Configure the macro's PDN away from the defaults.** The PDK default puts
straps on TopMetal1 and TopMetal2, which is where the tile's own power stripes
and analog routing live. `FP_PDN_MULTILAYER: false` with
`PDN_VERTICAL_LAYER: Metal4` gives Metal1 rails plus Metal4 straps and nothing
else, which the tile can reach with an ordinary via stack.

**Mind LibreLane's floorplan margins on a small die.** The default left/right
margin is 12 site widths and top/bottom 4 site heights. At 44 × 34 µm that left
a core 3.76 µm tall and floorplanning failed with `IFP-0002`, because a row is
3.78 µm. 50 × 50 µm is comfortable.

## DRC

**The PMOS and NWell-tap PCells each draw their own NWell**, and where the two
meet the tie ends up only marginally enclosed, tripping `NW.d` (min NWell space
to external N+ Activ, 0.31 µm). One generous well over the whole p-side fixes it.

## Tiny Tapeout precheck

**Every LEF port must also be a polygon on the matching `<layer>.pin`** — 50/2
for Metal4, 126/2 for TopMetal1 — containing the LEF rectangle.

**The LEF must declare all 51 interface pins**, not just the ones used: `clk`,
`ena`, `rst_n`, every `ui_in`/`uo_out`/`uio_*`, and all eight `ua[]`. They are
parsed out of `analog/tech/tt_analog_1x2.def` so names, layers and positions
cannot disagree with the shuttle.

**Power goes on TopMetal1, at least 2.1 µm wide.** The published analog spec
says Metal4 and 1.2 µm — that is the *sky130* guidance. Precheck is the
authority for IHP.

**The boundary layer is `prBoundary.boundary` (189/4)**, not `.drawing` (189/0),
which is not on the allowed layer list.

**Strip `HeatTrans` (51/0).** The device PCells draw it; it is not allowlisted
and plays no part in DRC or LVS.

**Write the GDS with `write_context_info` disabled.** KLayout otherwise emits a
hidden `$$$CONTEXT_INFO$$$` cell holding PCell parameters. `gdstk`, which
precheck uses, counts it as a second top-level cell and fails the boundary
check — and because `analog_pin_check` inspects `top_level()[0]`, it was
examining that cell instead of the tile and wrongly reported `ua[0]` as
unconnected. One flag, two unrelated-looking failures.

**An unused `ua[]` pin must have no metal within 0.5 µm.** The check builds a
ring 0.1–0.5 µm outside each pad and treats any TopMetal1 there as a connection,
cross-referenced against `analog_pins` and the pinout descriptions in
`info.yaml`. Drawing the pad rectangle itself is fine; overhanging it by more
than 0.1 µm counts as wired.

`make precheck` reproduces the last four locally. Worth it — a CI round trip is
about seven minutes.

---

# Not done yet

Deliberately left for a future session. Nothing below has been run, so treat the
commands as starting points rather than known-good.

## Parasitic extraction and post-layout simulation

The container has **kpex 0.3.15**, which supports this PDK directly:

```
kpex --pdk ihp-sg13g2 --gds ../gds/<TOP>.gds --cell <TOP> \
     --schematic out/<TOP>.spice --out_spice out/<TOP>_pex.spice --2.5D
```

Modes are `--2.5D` (analytic, fast), `--fastercap`/`--fastcap` (field solver),
and `--magic`; `--mode {CC,RC,R}` selects what gets extracted. The PDK also
ships `libs.tech/parasitics/itf` for other extractors.

The intended shape once it works: a `make pex` target producing an
`*_pex.spice` netlist, then a `make sim-post` that runs the existing testbench
against it instead of the schematic netlist, so pre- and post-layout numbers can
be compared. That needs a testbench variant which `.include`s the extracted
subcircuit rather than `inverter.sch`'s — not yet written.

On this particular design it will barely matter: the inverter is a few µm across
and its own parasitics are tiny next to the ~24 µm TopMetal1 runs out to the
pads. It becomes worth doing on a block with real internal routing.

## Other open items

- **Fill / density rules.** DRC runs with `--no_density` locally. The tile is
  mostly empty, so density rules would likely fail on a real run. The PDK ships
  `libs.tech/klayout/tech/scripts/filler.py`; TT's own flow may handle this.
  Untested either way.
- **No output buffer.** `ua[0]` drives the analog pad directly, so measured
  edges will be far slower than the simulated on-chip figures. Fine for a static
  sweep, not for measuring the delays above.
- **Corners.** Only `mos_tt` is simulated. `cornerMOSlv.lib` also provides the
  slow/fast corners.
- **Deleting a stray repo.** A standalone `mgpauly1458/ihp-sg13g2-inverter` repo
  was created early on and has since been superseded by this branch. It is set
  to private but not deleted; `gh` lacks the scope. To finish it:
  `gh auth refresh -h github.com -s delete_repo && gh repo delete mgpauly1458/ihp-sg13g2-inverter --yes`

---

# Conventions

- Generated artefacts go in `analog/out/`, which is gitignored. Anything that
  must be committed (`gds/`, `lef/`, `docs/*.png`) is written outside it.
- `digital/runs/` is gitignored; `digital/out/` **is committed**, because
  `analog/layout/build_gds.py` reads the macro GDS from there and the tile must
  be rebuildable without re-running LibreLane.
- The RTL lives in `src/ms_hello.v`, not under `digital/`, because Tiny Tapeout
  expects source files in `src/` and `info.yaml` lists it. `digital/config.json`
  reaches back up to it.
- `analog/checks/tt_valid_layers.txt` is vendored from tt-support-tools at the
  commit the shuttle pins; refresh it if the shuttle moves.
- Don't hand-edit `lef/` — it is generated by `make gds`.
- The tile geometry in `analog/tech/tt_analog_1x2.def` is TT's file, vendored so
  the build is reproducible offline.
