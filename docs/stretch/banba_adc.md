# Banba bandgap + digital-only readout

Independent stretch block, separate from ring slot 7. Goal: on-chip bandgap reference (Banba topology), readable with zero analog pins — this tile is digital-only.

## Readout options

| readout | analog cost | digital cost | accuracy | verdict |
|---|---|---|---|---|
| RC 1-bit sigma-delta | comparator, R, C, mux | 1 flop + counter (reuse existing counter) | best, self-calibrating | **chosen** |
| single-slope ramp | current source, C, reset switch, comparator | reuse reciprocal counter | good, ratiometric | needs a clean current source |
| resistor-string DAC + comparator | 64-256 resistors, switch tree | none | ~8b | most area, slowest |
| bandgap -> V/I -> ring -> counter | reuse ring IP | none | poor | ring V-to-f nonlinear, not worth it |

## Sigma-delta readout, how it works

```
      mux --> [comparator]--+--> D flop (50MHz) --+--> feedback inverter --> R --+
       ^            -            Q                                              |
   Vin candidates    \_____________________________________________ C (to GND) _+
   (see below)                          cap node = comparator - input
```

- Feedback inverter output through R into cap C sets cap node; comparator compares cap node (-) to Vin (mux, +).
- Flop output = 1 -> feedback node driven high -> cap charges up. 0 -> driven low -> discharges.
- Steady state: average cap current = 0, so **ones density = Vin / VDD** exactly. Ratiometric to VDD (a feature: VDD is bench-measurable).
- Counter over 2^N clocks -> N-bit count. N=16 -> ~12 useful bits after comparator noise/offset.
- Offset cancellation: swap mux inputs + invert decision each half of the measurement window, average the two counts.

## Mux inputs (Vin candidates)

| signal | source | why |
|---|---|---|
| `vref` | Banba output (~0.6V, mid-supply for 1.2V core) | the measurement |
| `vbe` | one PNP's Vbe | CTAT (~-1.7mV/C); `vbe/vref` cancels VDD -> free temp sensor |
| `vdd/2` tap | resistor divider | gain self-check |
| shorted pair | tie both comparator inputs | offset self-check |
| ring's `vbp`/`vbn` (optional) | existing ring slot 7 bias nodes | debug: read the ring DAC bias directly |

## Bandgap trim

Standard Banba: R1/R2/R3 set PNP ratio + Vref target. Put a 3-4b trim on R2 or R3, driven from the register file (same WDATA/ADDR bus as everything else). The sigma-delta measures the result of each code -> trim curve is a firmware loop, no extra analog.

## SG13G2-specific notes

- BJT: `pnpMPA`. Large R: `rhigh`. Branch current 5-10uA -> resistors tens of um long; fits in 202x314um tile alongside the 91x57um ring macro (slot 7).
- Opamp input pair sits at Vbe (0.55-0.75V over temp): NMOS pair. Opamp offset multiplies directly into Vref -> size the pair up; chopping is a later refinement.
- Comparator common mode ~0.6V: PMOS input pair, or 5T preamp + StrongARM latch.
- Feedback-node driver: plain inverter, R >> its output resistance so high/low levels are true rails.
- Needs a start-up circuit (Banba has a zero-current stable point) + opamp compensation cap.

## Verification plan (mirrors `analog/verify/*.py` pattern)

- ngspice: temp sweep (bandgap curvature), Monte Carlo (opamp offset, R ratio mismatch -> Vref spread), VDD sweep (line regulation, ratiometric check).
- Sigma-delta as its own testbench: ideal Vin -> count -> back out Vin, sweep offset/mismatch, confirm cancellation scheme works.
- Bonus/demo: route the raw 1-bit stream to a spare `uo` pin; external RC or scope averaging reconstructs Vbg scaled to I/O voltage.

## Status

Idea + netlist skeleton only (`analog_stretch/spice/tt_banba_adc.spice`). Not sized, not simulated, not in `info.yaml` (`analog_pins: 0`, tile is `1x2` for slot 7 already). No layout.
