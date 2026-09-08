# Timing constraints

`src/constraints.sdc` sources LibreLane's `base.sdc` (`clk` at 20 ns,
Tiny Tapeout's pin delays) and adds the ring domains. `src/config.json`
names it as `PNR_SDC_FILE` and `SIGNOFF_SDC_FILE`. Last clean run: 0 setup,
0 hold at tt 25 C 1.20 V, ss 125 C 1.08 V, ff -40 C 1.32 V.

## Clocks

| clock | created on | period | clocks |
|---|---|---|---|
| `clk` | tile clock pin | 20 ns | `regfile`, `measure_core` FSM and counters, reference-side synchronisers |
| `ring0`..`ring6` | `u_rings.u_ringN.u_out/X`, each cell ring's `(* keep *)` output buffer | 1.6 ns (0.8 ns for ring 5) | only the mux |
| `ring7` | `u_rings.u_ring7/clk_out` | 1.6 ns (fast corner code 255: 544 MHz pre-layout, 275 MHz extracted) | only the mux |
| `ring_sel` | `u_mux.u_selout/X` | 0.8 ns | `u_div.q1`, the fastest flop |
| `div_ring` | `u_div.u_divout/X` | 4.0 ns | `measure_core` window logic and its `arm` synchroniser |

- `set_clock_groups -asynchronous`, every clock in its own group; the
  two-flop `cdc_sync` synchronisers are the only crossings.
- Each cell ring's loop is broken at its NAND's feedback input
  (`set_disable_timing u_en -from B -to Y`), not by OpenSTA's loop breaker.
- `u_selout` and `u_divout` are `(* keep *)` `sg13g2_buf_1` instances in
  `ring_mux` and `ring_divider` (plain assigns under `-DSIM`): synthesis
  renames nets, kept instances keep their name, so the SDC has pins to
  hang `ring_sel` and `div_ring` on.
- Why `div_ring`: with clocks only at the ring sources they propagated
  through the divider's tap-0 path into the 16-bit window counter, which
  STA timed at the raw 11-stage rate (0.9 ns) and failed by 1.5 ns at the
  slow corner. A clock created on a pin stops the upstream clock there.

## Usage rule

The divided ring must not exceed 250 MHz. STA passes the window logic at
3.0 ns at the slow corner (331 MHz); 4.0 ns is the constraint with margin.

| tap | safe for rings below |
|---|---|
| 3 (div 8) | 2 GHz: every ring at every corner |
| 2 | 1 GHz |
| 1 | 500 MHz |
| 0 | 250 MHz: slow rings, e.g. the analog ring at low codes (2 MHz at code 0) |

Analog ring at code 255, fast corner: 275 MHz extracted (544 MHz
pre-layout, still covered); 11-stage ring about 1 GHz. Testbenches use
taps 3 and 4, the cocotb bench tap 3. `q1` at 0.8 ns passes with margin
(period_min 0.54 ns at the slow corner).

## Knowingly unconstrained

- Ripple stages `q2`..`q7`: no generated clocks (six unclocked register
  pins reported). Each runs at half the previous stage's rate with the
  same one-flop structure, so cannot fail where `q1` passes.
- Region constraints for the rings: not applied; slots 0..3 are matched
  in netlist, not in placement. First thing to add for a second submission.
- Resizer immunity: `(* keep *)` does not stop OpenROAD repair resizing a
  ring cell. None was touched in the clean run; not enforced.

## Lint

`RUN_LINTER` on, warning-free. Three waivers at the line that provokes
each: the blackbox's unused inputs and undriven output
(`tt_analog_ring.v`), the simulation-only parameter (`ring_21_min.v`),
`reset` used both synchronously and asynchronously (`project.v`; the
divider's clock may not be running).

## Gate-level simulation

Cell rings are zero-delay at gate level and a zero-delay loop does not
advance simulation time. `test/test.py` keeps `ena` low, which gates every
ring enable, until ring 7 is selected; the macro's model is compiled in
beside the netlist (`test/Makefile`). Tiny Tapeout's `gl_test` runs it
with iverilog 13 (12 leaves the PDK's flops at X; 14 cannot parse the
cell models).
