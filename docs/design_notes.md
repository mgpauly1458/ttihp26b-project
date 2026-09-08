# Design notes: decisions against the brief

All revisable; those needing the owner's call are marked.

## Open questions (brief section 10)

| question | answer |
|---|---|
| SG13G2 supply, ring range | core 1.2 V (slow 1.08 V 125 C, fast 1.32 V -40 C). Liberty `inv_1` 50..60 ps at FO1: 21-stage ring ~430 MHz, 11-stage ~800 MHz before wire load; not confirmed on silicon. The divider brings these into the model's 20..400 MHz span. |
| tri-state inverters | yes: `sg13g2_einvn_2/4/8` (`TE_B` active low), `sg13g2_ebufn_2/4/8`. Ninth ring buildable; decision needed ([rings.md](rings.md)). |
| reference clock | 50 MHz everywhere (`clock_hz` in `info.yaml`, testbenches, tables); only a scale factor. |
| `TARGET_N` default, resolution vs time | reset 256. Resolution `1/RESULT`, time `RESULT` cycles: 0.1 % = 1000 cycles = 20 us regardless of ring speed. The sweep uses 200 because 2048 runs must simulate. |
| pin mapping | parallel address/data strobe ([pinmap.md](pinmap.md)). Built without approval per instruction; reversible, the register map is pin-independent. |
| unselected rings | disabled (`ring_mux.v` header): free-running rings burn power and inject noise. The selected ring is enabled by the `RING_SEL` write, not `START`, so it settles while the host writes the other registers; a slow starter needs the host to wait between the two. |
| mid-measurement writes | all blocked and flagged in `STATUS.write_ignored` ([registers.md](registers.md)). |

## Decisions the brief flagged

- Divider: seven flops, eight taps. "Eight stages, div 1..128" disagrees
  by one; div 1 is the raw ring. Div 256 instead of div 1 is one more flop.
- The +-1 question: settled in [registers.md](registers.md) and
  `measure_core.v`'s header. Nothing multi-bit crosses a clock boundary;
  the counter read lives in the domain that reads it.
- CLEAR state added (IDLE, CLEAR, ARM, RUN, SETTLE, DONE): after a timeout
  on a slow ring an immediate restart caught the ring domain mid-window
  and timed out again. CLEAR holds `arm` low until the ring domain reports
  cleared, under the same timeout.
- `write_ignored` status bit adopted; one flop.
- Rings 0..3 are one module instantiated four times; `SIM_F_HZ` lets the
  four models differ and affects nothing structural.
- `ena` is the master ring enable: it is 1 exactly while this project is
  selected, so the rings are off while a neighbour runs.
- `ID` register (`0xA5`), not in the brief: "is the interface alive"
  before any measurement.
- Layout: the brief asked for `rtl/`; Tiny Tapeout requires `src/`
  (`source_files` resolve relative to it).

## What the model's unpleasant curve caught

- The offset forced the window to be defined in periods, not edges; the
  first testbench draft was rewritten.
- The dead zone exercised the timeout recovery path, which is where CLEAR
  came from.
- The nonlinear region added nothing in simulation (the instrument is
  linear in period); on silicon it asks whether the ring matches the curve.

## The analog macro's arrival

Slot 7 is the macro (`src/rings/tt_analog_ring.v`, `src/config.json`,
`src/constraints.sdc`). Its model has no dead zone (2 MHz at code 0,
164 MHz at 255), so dead-code tests became slow-code tests: code 0 through
tap 3 with N = 200 takes 800 us and a short timeout reports. The sweep
uses tap 1 for this ring so both ends fit its timeout. Gate-level
simulation: [constraints.md](constraints.md).
