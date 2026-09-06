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
| `analog-inverter` | analog custom-GDS, a hand-drawn CMOS inverter | CI green, all 10 prechecks pass |

Only `main` has `test/` and `fpga/`; only `analog-inverter` has `analog/`,
`gds/` and `lef/`. Don't be surprised when a file is missing — check the branch.

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

# The analog flow (`analog-inverter` branch)

Everything lives in `analog/` and runs inside the `hpretl/iic-osic-tools`
container via `analog/run.sh`, which mounts the repo root at `/work`. **Docker
is the only host dependency** — the image already ships the `ihp-sg13g2` PDK,
xschem, ngspice, KLayout, magic, netgen and kpex.

```bash
cd analog
make help      # every target, with one-line descriptions
make all       # both pipelines end to end
```

## Two pipelines, deliberately separate

**`make design`** — *is the circuit right, and does the layout match it?*
`netlist → sim → gds → drc → lvs`

**`make tt`** — *will Tiny Tapeout accept it?*
`drc → lvs → precheck`

They overlap on DRC and LVS but answer different questions. A design can be
perfectly correct and still be rejected by precheck, which is exactly what
happened here: the circuit was DRC and LVS clean well before precheck passed,
and every remaining failure was about how the GDS is *written*.

Individual steps: `netlist`, `sim`, `plot`, `gds`, `drc`, `lvs`, `precheck`,
`png`. Interactive: `xschem`, `klayout`, `shell`, `ci`.

Both PDK runners exit non-zero on failure (verified empirically with a
deliberately shorted layout and a mismatched netlist), so `make` genuinely
gates rather than printing errors and carrying on.

## What the current design is

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
interconnect is hand-drawn. `analog/layout/build_gds.py` builds the core and
the tile and emits the LEF **from the same constants**, so the LEF can never
describe geometry the GDS does not have.

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

**LVS net labels must be `Text` on layer 8/25.** The deck reads them via
`metal1_text = labels(8, 25)` and attaches them with
`connect(metal1_con, metal1_text)`. Labels on any other layer are silently
ignored and the extracted netlist comes back with unnamed nets.

**The PMOS and NMOS symbols have opposite D/S pin order.** The PMOS puts its
source at the top — the sensible convention, but the reverse of the NMOS.
Placing both at the same rotation silently gives a PMOS with its source on the
output node. Read the netlist, not the picture.

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
- `analog/checks/tt_valid_layers.txt` is vendored from tt-support-tools at the
  commit the shuttle pins; refresh it if the shuttle moves.
- Don't hand-edit `lef/` — it is generated by `make gds`.
- The tile geometry in `analog/tech/tt_analog_1x2.def` is TT's file, vendored so
  the build is reproducible offline.
