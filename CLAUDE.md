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
src/            RTL (Tiny Tapeout needs src/; the brief's rtl/ is this)
src/rings/      structural ring netlists (cells by name) + analog stub
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

## Not done yet

- Hardening. Nothing has been through LibreLane on this branch. Expect
  Verilator `UNOPTFLAT` on the rings and unconstrained ring clocks; see
  `docs/constraints.md` for the plan.
- Gate-level CI job (`gl_test`) will hang on zero-delay ring loops.
- Region constraints for the rings, especially slots 1..3 at corners.
- The analog ring macro (slot 7). Import it the way `main` imports its
  inverter: `(* blackbox *)` + `MACROS` in `src/config.json`. `main`'s
  CLAUDE.md lists every trap that cost time doing that.
- Decision: a ninth, tri-state-inverter ring (`sg13g2_einvn_*` exists).
- Decision: approve or change the pin map (`docs/pinmap.md`).

## Tiny Tapeout flow

Unchanged from the template. `make tools` clones `tt/` and builds the
venv; `make harden`, `make precheck`, `make cocotb`. `main`'s CLAUDE.md
has the full local-hardening story (LibreLane 3.0.5 in the venv, not the
container's dev build; PDK at `~/pdk`). Push → CI builds → submit the repo
URL at app.tinytapeout.com before the deadline.

## Conventions

- `docs/*.png` and `*.gds` go through Git LFS (`.gitattributes`).
- `tt/`, `venv/`, `build/`, `runs/`, `tt_submission/` are not committed.
- Cell stand-in delays in `sim/sg13g2_cells_sim.v` and the expected
  periods in `sim/tb_rings.v` must agree; both say so.
