# Design notes: decisions, and the questions behind them

This file records the answers taken to the brief's open questions and the
decisions the brief said to ask about. They were taken to keep the build
moving; every one is revisable, and the ones that need a decision are
marked.

## Answers to the open questions (brief §10)

**SG13G2 supply and ring frequency range.** Core supply is 1.2 V nominal
(`nom_voltage : 1.2` in `sg13g2_stdcell_typ_1p20V_25C.lib`; slow corner
1.08 V at 125 °C, fast 1.32 V at −40 °C). From the same Liberty, `inv_1`
is about 20 ps unloaded and 50 to 60 ps at fanout-of-one, so a 21-stage
minimum-drive ring lands near 430 MHz before wire load and an 11-stage
one near 800 MHz. **Not confirmed on silicon; these are Liberty numbers.**
The model's 20 to 400 MHz span therefore covers the standard-cell rings
only after division, which is what the divider is for. Ring 5 at ÷16 and
the rest at ÷8 keep the divided clock under ~60 MHz.

**Tri-state inverters.** Yes: `sg13g2_einvn_2/4/8` (tri-state inverter,
enable `TE_B` active low) and `sg13g2_ebufn_2/4/8` (tri-state buffer).
The ninth ring is buildable. **Decision needed**, see rings.md.

**Reference clock.** 50 MHz assumed everywhere (`clock_hz` in `info.yaml`,
the testbenches, the tables in registers.md). It is only a scale factor;
any frequency the tile's `clk` pin can carry works, and the formula takes
it as an input.

**`TARGET_N` default and the resolution/time tradeoff.** Reset value 256.
Resolution is `1/RESULT` and time is `RESULT` reference cycles, so for a
given resolution the measurement time is fixed regardless of ring speed:
0.1 % costs 1000 cycles = 20 µs at 50 MHz. `TARGET_N` and `TAP_SEL` are
chosen to make `RESULT` land near that; the tables in registers.md give
starting points. The sweep uses `TARGET_N` = 200 because 2048 of them have
to run in simulation.

**Pin mapping and readout.** Parallel address/data strobe. Reasoning and
the SPI comparison in pinmap.md. **Built without waiting for approval, per
instruction; the choice is easy to reverse because the register map is
independent of the pins.**

**Unselected rings.** Disabled. The tradeoff is in `ring_mux.v`'s header:
seven free-running rings would burn power and inject noise into the one
under test. The settling cost is covered by enabling the selected ring
from the `RING_SEL` write, not from `START`, so it has been running for
the whole time the host spends writing the other registers. The FSM's ARM
state then opens the window on a clean edge. If the analog ring needs
milliseconds to start, the host waits between `RING_SEL` and `START`;
nothing in hardware changes.

**Mid-measurement register changes.** Blocked in hardware, all of them,
and flagged in `STATUS.write_ignored`. Details in registers.md.

## Decisions taken that the brief flagged

**Divider: seven flops, eight taps.** The brief says "eight cascaded
stages ... ÷1 through ÷128" and "eight explicit flip-flops". Those
disagree by one: ÷1 is the raw ring and needs no flop, so ÷1..÷128 is
seven flops plus a raw tap. Built as seven flops, eight taps, ratio
`2^TAP_SEL` exactly as the formula says. If ÷256 is wanted instead of ÷1,
it is one more flop and a changed case statement.

**The ±1 question.** Settled in `measure_core.v`'s header. The window is
exactly `TARGET_N` complete divided-ring periods (edge 0 to edge
`TARGET_N`), and `RESULT` is the number of reference edges inside it. The
only error term is the reference-edge quantisation at each end of the
window, ±1 count total, identical for every ring. Nothing multi-bit ever
crosses the clock boundary, so there is no freeze-then-read of a counter:
the counter that is read lives in the domain that reads it.

**A CLEAR state was added to the FSM.** IDLE → CLEAR → ARM → RUN → SETTLE
→ DONE. The measure_core testbench's recovery test found that after a
timeout on a slow ring, an immediate restart could catch the ring domain
still mid-window from the aborted run; it would then never close the
window and time out again. CLEAR holds `arm` low until the ring domain
reports itself cleared, under the same timeout. It costs one state and
makes "start whenever you like" true.

**The write-ignored status bit.** Adopted; see registers.md.

**Rings 0..3 are one module instantiated four times**, which is the
strongest possible statement of "identical netlists". A `SIM_F_HZ`
parameter exists on `ring_21_min` so the four simulation models can
differ; it affects nothing in the structural branch.

**`ena` is the master ring enable.** The template says to ignore it, but
it is 1 exactly while this project is selected on the shuttle's mux, so
using it means our rings are off while a neighbour's project is running.

**`ID` register.** Not in the brief. Added because on new silicon the
first question is "is the interface alive", and a constant that reads
back answers it before any measurement is attempted.

## Repository layout vs. the brief

The brief asked for `rtl/`. Tiny Tapeout requires the synthesisable
sources under `src/` (its tooling resolves `source_files` relative to
`src/`), so `src/` is the RTL directory and `src/rings/` holds the ring
netlists. `sim/`, `scripts/` and `docs/` are as specified.

## What the model's unpleasantness caught

- The nonzero offset and the ±1 analysis together made the window
  definition explicit; the first draft of the testbench was written in
  terms of "edges" and had to be rewritten in terms of periods.
- The dead zone exercised the timeout path 20 times per sweep and, more
  usefully, forced the timeout *recovery* path, which is where the CLEAR
  state came from.
- The nonlinear region contributed nothing beyond the linear one in
  simulation, because the instrument is linear in period by construction.
  It will matter on silicon, where the question becomes whether the
  *ring* is what the curve says.

## Gate-level simulation

Zero-delay ring loops hang a gate-level simulation. The cocotb bench
therefore keeps `ena` low (which gates every ring enable in ring_mux)
until it has selected ring 7, the analog macro, whose behavioural model is
compiled in beside the gate-level netlist because the macro is a blackbox
there too. It never selects a standard-cell slot. Tiny Tapeout's `gl_test`
job runs that bench on the hardened netlist with iverilog 13.

## The analog macro's arrival

Slot 7 stopped being a stub when the macro was integrated (see
`src/rings/tt_analog_ring.v`, `src/config.json`, `src/constraints.sdc`).
Its simulation model has no dead zone (two always-on DAC units keep it at
3.8 MHz at code 0) and runs to 332 MHz at code 255, so the "dead code"
tests became "slow code" tests: code 0 through tap 3 with N = 200 takes
421 us and a 40 us timeout reports, as it should. The sweep uses tap 1 for
this ring so both ends fit inside its timeout.
