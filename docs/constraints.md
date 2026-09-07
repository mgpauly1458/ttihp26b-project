# Timing constraints: what the tile is told, and what that covers

`src/constraints.sdc` is the file. It sources LibreLane's `base.sdc` (the
reference clock `clk` at 20 ns and the pin delays Tiny Tapeout sets) and
adds the ring domains. `src/config.json` names it as both `PNR_SDC_FILE`
and `SIGNOFF_SDC_FILE`, so placement, CTS, routing repairs and the final
STA all see the same constraints. Last clean run: 0 setup and 0 hold
violations at all three signoff corners (tt 25 C 1.20 V, ss 125 C 1.08 V,
ff -40 C 1.32 V).

## Clock domains

| clock | created on | period | what it clocks |
|---|---|---|---|
| `clk` | the tile's clock pin | 20 ns | `regfile`, `measure_core`'s FSM and counters, the reference-side synchronisers |
| `ring0`..`ring6` | `u_rings.u_ringN.u_out/X`, each standard-cell ring's `(* keep *)` output buffer | 1.6 ns (0.8 ns for the 11-stage ring 5) | nothing directly: they only reach the mux |
| `ring7` | `u_rings.u_ring7/clk_out`, the analog macro's output pin | 1.6 ns (544 MHz simulated at the fast corner, code 255) | likewise |
| `ring_sel` | `u_mux.u_selout/X`, the named buffer on the selected ring | 0.8 ns | `u_div`'s first flop `q1`, the fastest flop in the design |
| `div_ring` | `u_div.u_divout/X`, the named buffer on the divided ring | **4.0 ns** | `measure_core`'s window logic and its `arm` synchroniser |

`set_clock_groups -asynchronous` puts `clk` and every one of these in its
own group: no path between them is timed. The two-flop synchronisers in
`cdc_sync` are the only crossings and are false by construction.

Each standard-cell ring's loop is broken for STA at its NAND's feedback
input (`set_disable_timing u_en -from B -to Y`), so the break is chosen
here rather than by OpenSTA's loop breaker.

## Why the two named buffers exist

Synthesis renames every net and gate it touches, so a clock cannot be
created on "the mux output" by name. `ring_mux` and `ring_divider` each
send their output through a `(* keep *)` `sg13g2_buf_1` instance
(`u_selout`, `u_divout`); a kept cell instance survives with its name, and
the SDC hangs the `ring_sel` and `div_ring` clocks on their `X` pins. In
simulation (`-DSIM`) the buffers are plain assigns.

The divided clock is the one that mattered. The first hardening run created
clocks only at the ring sources; they propagated through the mux and,
via the divider's tap-0 path, straight into `measure_core`'s 16-bit window
counter, which STA then timed at the raw 11-stage ring rate (0.9 ns) and
failed by 1.5 ns at the slow corner. A clock created on a pin stops the
upstream clock propagating past it, so the `div_ring` clock on `u_divout/X`
is where the window logic's rate is set.

## The one usage rule this creates

**The divided ring must not exceed 250 MHz.** STA reports the window logic
good to 3.0 ns at the slow corner (331 MHz), so 4.0 ns is the constraint
with margin. A ring faster than 250 MHz must be measured through a higher
tap: tap 3 (divide by 8) is safe for every ring at every corner (up to
2 GHz), tap 2 for anything under 1 GHz, tap 1 under 500 MHz. The analog
ring reaches 544 MHz at code 255 at the fast corner, the 11-stage ring
about 1 GHz. Tap 0 (divide by 1) exists for slow rings, such as the analog
ring at low codes (3.8 MHz at code 0). The testbenches use tap 3 and 4; the
cocotb bench uses tap 3.

The first divider flop `q1` is constrained at 0.8 ns (`ring_sel`) and
passes with margin (period_min 0.54 ns at the slow corner): it is one flop
with Q-bar back to D and nothing else, as `ring_divider.v` insists.

## What is left unconstrained, knowingly

- **The ripple stages `q2`..`q7`.** Each is clocked by the previous stage's
  output, at half its rate. No generated clocks are declared for them, so
  STA reports six unclocked register pins. Each runs at most at half the
  rate `q1` is checked at, with the same one-flop structure, so they cannot
  fail where `q1` passes.
- **Region constraints for the rings.** Not applied. The placer spread each
  ring's cells where density suited it, so the four "matched" 21-stage rings
  in slots 0..3 are matched in netlist but not in placement. Their measured
  frequencies will say as much about placement as about process. This is
  the first thing to add if a second submission is made.
- **Resizer immunity.** `(* keep *)` keeps a ring's cells but does not stop
  OpenROAD's repair from resizing one. In the clean run no ring cell was
  touched (the loops are not timing paths, so nothing asks for it); it is
  not enforced.

## Lint

`RUN_LINTER` stays on and the run is warning-free. The three warnings the
design provoked are waived at the line that provokes them, with the reason
beside each: the blackbox's unused inputs and undriven output
(`tt_analog_ring.v`), the simulation-only parameter (`ring_21_min.v`) and
`reset` used both synchronously and asynchronously (`project.v`; the divider
needs it asynchronous because its clock may not be running).

## Gate-level simulation

At gate level the standard-cell rings are real cells with zero delay, and
a zero-delay ring loop does not advance simulation time. The cocotb bench
(`test/test.py`) keeps `ena` low, which gates every ring enable, until it
has selected ring 7, the analog macro; the macro is a blackbox in the
gate-level netlist too, so its behavioural model is compiled in beside it
(`test/Makefile`). Tiny Tapeout's `gl_test` job runs that bench with
iverilog 13 (iverilog 12 leaves the PDK's flops at X; 14 cannot parse the
cell models).
