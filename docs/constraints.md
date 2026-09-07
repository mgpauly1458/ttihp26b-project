# Synthesis and timing constraints this design will need

Nothing here is applied yet. This phase is simulation only. The list exists
so the hardening phase starts from a plan instead of a surprise.

## Clock domains

| clock | source | what it clocks |
|---|---|---|
| `clk` | the tile's clock pin, 50 MHz | `regfile`, `measure_core`'s FSM and counters, the reference-side synchronisers |
| `ring_sel_clk` | whichever ring is selected, up to ~900 MHz | `ring_divider` stage 1 |
| `q1..q7` | the divider stages, each half the previous | the next stage |
| `divided_ring` | the tap mux output | `measure_core`'s window logic and its `arm` synchroniser |

The ring clocks are asynchronous to `clk` and to each other in phase. Tell
STA so, or it will try to close timing between them and report nonsense:

    create_clock -name ring -period 1.1 [get_pins u_mux/ring_out]   ; # fastest ring, 11-stage
    create_generated_clock ... on each divider stage, or simply
    set_clock_groups -asynchronous -group {clk} -group {ring ...}

The reference-domain synchroniser inputs (`s1` in each `cdc_sync`) are the
only paths between the groups, and they are false by construction.

## The rings

Each ring is a combinational loop, which synthesis and STA both dislike.

- `(* keep *)` is already on every instance and net so yosys does not
  remove or merge them.
- Mark the ring instances **don't-touch** so the resizer does not upsize an
  inverter for "timing" and change the ring's frequency.
- `set_disable_timing` on one arc per loop (e.g. `u_en/B` to `u_en/Y`) so
  STA does not report a timing loop. OpenSTA breaks loops itself with a
  warning, but the break should be chosen, not left to it.
- **Region constraints**: each ring in a compact area; slots 1..3 at
  separate corners. Without this the placer will spread a ring's 21 cells
  wherever density is convenient, and its frequency will say more about
  the placer than the process.

## The first divider stage

`u_div/q1` is the only flop that sees the raw ring and is the fastest thing
in the design. It should be a plain `sg13g2_dfrbp_1` with `Q_N` wired to
`D` and nothing else on that path. If the resizer inserts buffers in the
`Q_N` to `D` path, forbid it there.

## Lint

The rings will produce combinational-loop warnings from Verilator
(`UNOPTFLAT`). They are correct warnings about intended loops. Waive them
for `src/rings/` rather than globally.

## Gate-level simulation

At gate level the rings are real cells with zero delay unless SDF is
back-annotated, and a zero-delay ring loop does not advance simulation
time. Tiny Tapeout's `gl_test` job will need either SDF from the hardened
run or a `-DGL_TEST` path in `test/test.py` that limits itself to the
interface (ID readback, register readback, a timeout with the rings
disabled). Not addressed yet.
