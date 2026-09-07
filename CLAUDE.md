# Ring oscillator meter — working notes

Branch `ring-osc-meter` of the TTIHP 26b submission repo (IHP SG13G2
130 nm, `ihp-sg13g2` PDK). **Shuttle closes 2026-09-21.** Allocation is
2 tiles (`1x2`).

## How to work on this

The owner reads every line and wants to be able to explain all of it.

- Build one module at a time: write it, write its testbench, run it, show
  the result, stop. Do not run ahead.
- Explain before writing: what it does, what its ports mean, how it works.
  If the explanation is hard, the design is too complicated.
- Boring beats clever. No generate loops where straight instantiation
  works, no parameters that were not asked for, no abstraction "for later".
- Comment the why, not the what. Every file has a header: what it does,
  which clock domain, what it assumes of its inputs.
- Stop and ask when a decision would change the design.
- Verilog-2001, synthesisable, `always @(posedge clk)` with non-blocking
  for sequential, `always @(*)` with blocking for combinational.
  Synchronous active-high reset unless there is a stated reason
  (`ring_divider.v` has one). iverilog `-g2005`; no SystemVerilog.

The full brief is the project's specification; `docs/design_notes.md`
records every decision taken against it and which ones still need the
owner's call.

## What it is

Reciprocal frequency counter + eight ring oscillator slots + register file
on the Tiny Tapeout pins. `src/project.v`'s header has the block diagram.
`f_ring = TARGET_N * 2^TAP_SEL * f_ref / RESULT`.

## Layout

```
analog/         the ring oscillator macro: generator, netlists, GDS/LEF/lib
src/            RTL (Tiny Tapeout needs src/; the brief's rtl/ is this)
src/rings/      structural ring netlists (cells by name) + the analog
                macro's blackbox (tt_analog_ring.v)
sim/            ring_model.v (ground truth), sg13g2_cells_sim.v (delay
                stand-ins), tb_*.v, tb_pins.vh (host protocol helpers)
scripts/        plot_sweep.py
docs/           registers, pinmap, rings, constraints, design_notes, plots
test/           cocotb smoke test for TT's CI
build/          iverilog output, logs, sweep.csv (ignored)
```

`make test` runs every testbench; `make sweep` is the exit criterion.
Each testbench prints `RESULT: PASS`/`FAIL` and the Makefile greps it.

## Two simulation modes

- `-DSIM`: every ring is a `sim/ring_model.v` instance with a known
  frequency. Used by `test_top`, `sweep` and `test/`. The instrument is
  checked against a known answer.
- no `-DSIM`: the rings are their structural netlists, simulated with the
  delay stand-ins in `sim/sg13g2_cells_sim.v` (the PDK's own models are
  zero-delay and a zero-delay ring loop hangs the simulator). Used only by
  `test_rings`. Checks each netlist is a real ring.

Enable a structural ring only after its chain has flushed its power-up X
(a few ns); an X pulse let into the loop circulates forever in simulation.

## Things learned building it

- **After a timeout, the ring domain can be left mid-window.** A restart
  before a slow ring had produced 2-3 edges would carry on from stale
  state and never close. Hence the FSM's CLEAR state (`measure_core.v`).
- **A level crossing domains must be held longer than one destination
  period.** The CDC testbench held some for 14.6 ns against a 20 ns clock
  and lost 64 of 500. The testbench was wrong, not the synchroniser, and
  it is now the comment that explains the rule.
- **Changing a clock-mux select while running makes runts.** Measured in
  `tb_ring_divider`: pulses down to 2.5 ns on a 10 ns clock. Every mux
  select is blocked while busy.
- **iverilog 12 and `-g2005`**: no `join_any`, no `output real` on tasks.
  A task-local `integer` reused by a caller's loop variable silently
  breaks the caller's loop (`tb_rings` tap loop ran once).
- Tiny Tapeout's tooling accepts `source_files` in subdirectories of
  `src/` (`os.path.join(src_dir, filename)`).

## Hardened

`make harden` (LibreLane 3.0.5 in the venv, PDK at `~/pdk`, as CI) is clean:
0 setup/hold violations at all three corners, Magic DRC 0, LVS clean,
antenna clean, lint clean; `make precheck` passes. `src/constraints.sdc`
carries the ring clocks (see `docs/constraints.md`); `src/config.json`
places and powers the analog macro. Slot 7 is `src/rings/tt_analog_ring.v`,
the blackbox of the macro in `analog/`.

The gate-level CI job runs the same cocotb bench on the netlist. It passes
because the bench keeps `ena` low until ring 7 (the macro, whose model is
compiled in beside the netlist) is selected: a zero-delay standard-cell
ring loop would otherwise hang iverilog. Never select slots 0..6 in that
bench.

## Not done yet

- Region constraints for the rings, especially slots 1..3 at corners. The
  placer put them where density suited it.
- Parasitic extraction of the analog block (`analog/README.md`).
- Decision: a ninth, tri-state-inverter ring (`sg13g2_einvn_*` exists).
- Decision: approve or change the pin map (`docs/pinmap.md`).

## The analog block (`analog/`)

The hand-generated macro for ring slot 7: a current-starved ring oscillator
whose current comes from an 8-bit binary array of long NMOS fingers
switched straight by the code bits. `analog/README.md` is the full story;
the short version:

- `make -C analog macro` builds `analog/macro/*.gds` + `.lef` and
  `analog/lib/*.lib` and runs the PDK's KLayout DRC and LVS. All three
  artefacts are committed (CI cannot regenerate them). DRC is clean at the
  maximal rule set without density; LVS matches.
- One generator (`analog/layout/build_tt_analog_ring.py`) writes the GDS,
  the LEF and the SPICE netlist from a single connectivity description, so
  LVS checks the drawn metal against what the script meant, and ngspice
  simulates the same netlist.
- Interface `code[7:0]`, `enable`, `clk_out`, `VPWR`, `VGND`; blackbox in
  `src/rings/tt_analog_ring.v`. Simulated 3.8 MHz (code 0) to 332 MHz
  (code 255), monotonic, 2 MHz/code at the bottom and compressing to 63 %
  of that line at the top, for reasons the README explains. `code[7]` presents 1.3 pF; the Liberty says so.
- `clk_out` has no timing arc: it is a clock source, `create_clock` it.
- The schematic is xschem (`analog/xschem/`, `make -C analog xschem`),
  generated by `make_sch.py` from the same constants as the layout and
  LVS-checked against the GDS by `make -C analog lvs-sch`. Renders in
  `docs/sch_*.png`.
- Density is not checked at block level; the tile's signoff does that.
- `make -C analog verify` runs the verification suite (`analog/verify/`):
  every block on its xschem sheet and then the whole netlist, over the 45
  PVT points, mismatch and process Monte Carlo, and `.noise`. Strategy in
  `docs/analog_verification.md`, generated results in
  `docs/analog_verification_results.md`. Layout strategy and concerns in
  `docs/analog_layout_notes.md`.

Things learned building it:

- **The other agent's `git clean`/checkout wiped untracked work.** Commit
  early when two agents share a working tree.
- **Long-L fingers are what make a rail-to-rail-gated DAC affordable.** A
  minimum-length unit sinks 100 µA; at L = 8 µm it is 2 µA. Power and area
  trade one for one at fixed gate drive - the only other knob is a lower
  gate bias, and that costs matching.
- **KLayout's DRC reports a via stack's lone Metal2 landing pad as a
  min-area violation** located at the PCell's own origin (-0.145,-0.1). Pad
  it out where a via stack passes through a layer nothing else uses.
- **LU.b (tie within 20 µm of every n+ finger) needs ties inside a 69 µm
  row**, not just a guard ring around it.
- **In the PDK's xschem symbols `w` is the total width, `ng` the finger
  count** (same as the PCells). Writing the per-finger width made the
  24-finger diode 2 µm instead of 48 µm and LVS caught it.
- **Wires that end on a pin box connect.** A bulk-tie wire run to the next
  transistor's gate position shorted gate to rail in two sheets; LVS
  caught that too. Keep device pitch larger than any stub you draw.
- **Device names in the generated netlist must be unique**: ngspice bails
  on duplicates with "device already exists"; KLayout LVS silently does not
  care.
- **ngspice `.noise` needs `ac 1` on its input source** or it aborts with
  "no AC value"; its `onoise_total` is the rms voltage (V), not V^2; and
  `meas ... deriv` is "currently not supported": take a slope from two
  threshold crossings instead.
- **One `.dc` can sweep all 256 codes**: eight B-sources turn the swept
  voltage into the code bits with `floor()` (`verify/common.py`).

Things learned integrating it:

- **Git LFS breaks the shuttle build.** Tiny Tapeout's action checks out
  without LFS; the macro GDS arrived as a pointer file and Magic failed
  with "Error while reading cell (UNNAMED)". Binaries are plain blobs now.
- **The ring clocks reach the 16-bit window counter through tap 0.** With
  clocks only at the ring sources, STA timed measure_core at the raw
  11-stage ring rate and failed by 1.5 ns. Named `(* keep *)` buffers in
  ring_mux and ring_divider give the SDC pins to put the selected and the
  divided clock on; the divided one is constrained to 250 MHz, which is
  the instrument's usage rule (fast rings through tap >= 1).
- **A PDN strap clipped by the macro edge gets no via** (PDN-0110). Place
  the macro so its edges clear the TopMetal1 straps (16.48 + 38.87n um for
  VPWR, 6.2 um further for VGND, 2.2 um wide).
- **`flow/run.sh` gives the container a HOME under analog/out**; the
  image's login shell needs a `.bashrc` there or exits with code 2 before
  running anything.

## Tiny Tapeout flow

`make tools` clones `tt/` and builds the venv; `make harden` (about three
minutes), `make precheck`, `make cocotb`. `main`'s CLAUDE.md has the full
local-hardening story (LibreLane 3.0.5 in the venv, not the container's
dev build; PDK at `~/pdk`). Push → CI builds (gds, precheck, gl_test,
viewer, test, docs) → submit the repo URL at app.tinytapeout.com before the
deadline. The only things `src/config.json` adds to the template are the
macro block and the SDC files; the SDC sources LibreLane's base.sdc.

## Conventions

- `docs/*.png` and `*.gds` are plain git objects, deliberately not LFS
  (`.gitattributes` says why).
- `tt/`, `venv/`, `build/`, `runs/`, `tt_submission/` are not committed.
- Cell stand-in delays in `sim/sg13g2_cells_sim.v` and the expected
  periods in `sim/tb_rings.v` must agree; both say so.
