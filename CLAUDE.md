# Ring oscillator meter: working notes

Branch `ring-osc-meter` of the TTIHP 26b repo (IHP SG13G2, `ihp-sg13g2`
PDK). Shuttle closes 2026-09-21. Allocation `1x2`.

## How to work on this

The owner reads every line and must be able to explain all of it.

- One module at a time: write it, test it, show the result, stop.
- Explain before writing. If the explanation is hard, the design is too complicated.
- Boring beats clever: no generate loops, no unasked-for parameters, no abstraction for later.
- Comment the why. Every file header: what, clock domain, input assumptions.
- Stop and ask when a decision would change the design.
- Verilog-2001, iverilog `-g2005`, no SystemVerilog. Synchronous active-high reset unless stated (`ring_divider.v`).

`docs/design_notes.md` records every decision against the brief and which still need the owner's call.

## What it is

Reciprocal frequency counter + eight ring slots + register file on the Tiny Tapeout pins. Block diagram in `src/project.v`'s header. `f_ring = TARGET_N * 2^TAP_SEL * f_ref / RESULT`.

## Layout

```
analog/         ring oscillator macro: generator, netlists, GDS/LEF/lib
src/            RTL (Tiny Tapeout needs src/; the brief's rtl/)
src/rings/      ring netlists + analog blackbox tt_analog_ring.v
sim/            ring_model.v (ground truth), sg13g2_cells_sim.v (delay
                stand-ins), tb_*.v, tb_pins.vh (host protocol helpers)
scripts/        plot_sweep.py
docs/           registers, pinmap, rings, constraints, design_notes, plots
test/           cocotb smoke test for TT's CI
build/          iverilog output, logs, sweep.csv (ignored)
```

`make test` runs every testbench (each prints `RESULT: PASS`/`FAIL`); `make sweep` is the exit criterion.

| mode | rings | used by |
|---|---|---|
| `-DSIM` | `sim/ring_model.v`, known frequencies | `test_top`, `sweep`, `test/` |
| no `-DSIM` | structural netlists with `sim/sg13g2_cells_sim.v` delays | `test_rings` |

- PDK cell models are zero-delay and a zero-delay ring loop hangs the simulator; hence the stand-ins.
- Enable a structural ring only after its chain has flushed power-up X (a few ns); an X in the loop circulates forever.

## Lessons: instrument

- After a timeout the ring domain can be left mid-window and a restart never closes; hence the FSM CLEAR state (`measure_core.v`).
- A level crossing domains must be held longer than one destination period: 14.6 ns against 20 ns lost 64 of 500 (testbench bug, now the rule's comment).
- Changing a clock-mux select while running makes runts (2.5 ns on a 10 ns clock); every mux select is blocked while busy.
- iverilog 12 `-g2005`: no `join_any`, no `output real` on tasks; a task-local `integer` shared with a caller's loop variable silently breaks the caller's loop.
- Tiny Tapeout accepts `source_files` in subdirectories of `src/`.

## Hardened

`make harden` (LibreLane 3.0.5 in the venv, PDK at `~/pdk`, as CI): 0 setup/hold violations at all three corners, DRC 0, LVS clean, antenna clean, lint clean; `make precheck` passes. `src/constraints.sdc` carries the ring clocks ([docs/constraints.md](docs/constraints.md)); `src/config.json` places and powers the macro; slot 7 is `src/rings/tt_analog_ring.v`, the blackbox of `analog/`.

Gate-level CI passes only because the cocotb bench keeps `ena` low until ring 7 (model compiled in beside the netlist) is selected. Never select slots 0..6 there: a zero-delay cell ring hangs iverilog.

## Not done yet

- Region constraints for the rings, especially slots 1..3 at corners.
- Decision: a ninth, tri-state-inverter ring (`sg13g2_einvn_*`).
- Decision: approve or change the pin map (`docs/pinmap.md`).

## Analog block (`analog/`)

Current-starved ring for slot 7, current from an 8-bit binary array of long NMOS fingers switched by the code bits. Full story: `analog/README.md`; layout `docs/analog_layout_notes.md`; verification `docs/analog_verification.md` and generated `docs/analog_verification_results.md`.

- `make -C analog macro`: GDS, LEF, Liberty, KLayout DRC (maximal rules, no density) and LVS. All three artefacts are committed; CI cannot regenerate them.
- One generator (`analog/layout/build_tt_analog_ring.py`) writes GDS, LEF and SPICE from one connectivity description; the xschem schematic (`make_sch.py`) is LVS-checked against the GDS by `make -C analog lvs-sch`.
- Interface `code[7:0]`, `enable`, `clk_out`, `VPWR`, `VGND`. Post-layout 2.0 MHz (code 0) to 164 MHz (code 255), monotonic. `code[7]` presents 1.3 pF.
- `clk_out` has no timing arc: it is a clock source, `create_clock` it.
- `make -C analog verify` (`analog/verify/`): each block, then the whole netlist, over 45 PVT points, Monte Carlo and `.noise`.

## Lessons: analog

- Commit early when two agents share a working tree; a `git clean`/checkout wiped untracked work.
- Long-L fingers make a rail-to-rail-gated DAC affordable: a minimum-L unit sinks 100 uA, at L = 8 um 2 uA.
- KLayout DRC reports a via stack's lone Metal2 landing pad as min-area at the PCell origin (-0.145,-0.1); pad it out where a stack passes through an otherwise unused layer.
- LU.b (tie within 20 um of every n+ finger) needs ties inside a 69 um row, not only a guard ring.
- PDK xschem symbols: `w` is total width, `ng` the finger count (as the PCells).
- Wires ending on a pin box connect; keep device pitch larger than any stub.
- Device names in the generated netlist must be unique: ngspice bails on duplicates, KLayout LVS silently does not.
- ngspice `.noise` needs `ac 1` on its input source; `onoise_total` is rms V, not V^2; `meas ... deriv` is unsupported, take a slope from two threshold crossings.
- One `.dc` sweeps all 256 codes: eight B-sources make the code bits with `floor()` (`verify/common.py`).
- The container's ngspice runs 8 threads per process and a 14-wide sweep thrashes; a run-dir `.spiceinit` with `set num_threads=1` replaces the container's, so it must also carry `set ngbehavior=hsa` and the PDK `osdi` lines (`common.SPICEINIT`).
- kpex 2.5D writes `M` lines naming PDK subcircuits, an unwrapped `.SUBCKT`, `$`-named nets and a VSUBS node; `layout/build_sim_post.py` rewrites them.
- Post-layout the ring is half as fast (~1.7 fF wiring vs ~1 fF devices per stage): 164 MHz not 332 MHz at code 255. Pre-layout numbers in older notes are 2x optimistic; the Liberty is from the extracted netlist.

## Lessons: integration

- Git LFS breaks the shuttle build: TT's action checks out without LFS and Magic fails on the pointer file. Binaries the build reads are plain blobs; LFS is used only under `analog/out` (sim data, `analog/out/.gitattributes`), which CI never reads (verified green).
- Ring clocks reach the 16-bit window counter through tap 0; with clocks only at ring sources STA failed by 1.5 ns. `(* keep *)` buffers in ring_mux and ring_divider give the SDC pins; the divided clock is constrained to 250 MHz.
- A PDN strap clipped by the macro edge gets no via (PDN-0110): keep macro edges clear of the TopMetal1 straps (VPWR at 16.48 + 38.87n um, VGND 6.2 um further, 2.2 um wide).
- `flow/run.sh` gives the container a HOME under analog/out; the image's login shell needs a `.bashrc` there or exits 2.

## Tiny Tapeout flow

`make tools` (clones `tt/`, builds the venv), `make harden` (~3 min), `make precheck`, `make cocotb`. Push; CI builds gds, precheck, gl_test, viewer, test, docs; submit the repo URL at app.tinytapeout.com. `src/config.json` adds only the macro block and the SDC files to the template; the SDC sources LibreLane's base.sdc. `main`'s CLAUDE.md has the local-hardening details.

## Conventions

- `docs/*.png` and `*.gds` are plain git objects, not LFS (`.gitattributes` says why). `VERIFY_REUSE=1 make -C analog verify ...` re-analyses the stored runs (a run is reused only if its deck text is byte-identical, so never change string literals in `analog/verify/*.py`).
- `tt/`, `venv/`, `build/`, `runs/`, `tt_submission/` are not committed.
- Cell stand-in delays in `sim/sg13g2_cells_sim.v` and expected periods in `sim/tb_rings.v` must agree.
