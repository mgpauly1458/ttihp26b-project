# Analog block verification

How the analog block (`analog/`, ring slot 7) was simulated beyond the typical-corner sweep in `analog/README.md`. The generated tables are [analog_verification_results.md](analog_verification_results.md) (`make -C analog verify`, ~1 h on 14 cores, plus `sim-post verify-ring-post verify-env verify-env-post`); the figures are `verify_*.png` here. The layout side is [analog_layout_notes.md](analog_layout_notes.md).

## Strategy

- The block is a sensor, not a clock: the tile measures whatever it runs at. Questions: oscillates and stops everywhere; code-to-frequency map monotonic (what binary DACs lose under mismatch); scale over PVT and die to die (the divided ring must stay under 250 MHz, `constraints.md`); noise below one code step, jitter below the counter's +-1 count; each block doing its own job.
- Two netlists, both LVS-proven against the GDS, nothing hand-edited: block tests run on the xschem sub-sheets (`verify/netlist_blocks.py`, proven by `make lvs-sch`), whole-block tests on the generator's `spice/tt_analog_ring.spice` (`make lvs`).
- Models: PSP 103.6 via `cornerMOSlv.lib`. `mos_tt/ss/ff/sf/fs` for corners; `mos_tt_mismatch` (per-device Vt and mobility `agauss` scaled by 1/sqrt(WL), enabled by `mm_ok=1`) for local mismatch; `mos_tt_stat` (one global parameter draw per run) for die to die. Each Monte Carlo sample is its own ngspice process with its own `.option seed`.
- PVT box: 5 corners x {-40, 27, 125} C x {1.08, 1.20, 1.32} V = 45 points. The three STA signoff corners (tt 27 C 1.20 V, ss 125 C 1.08 V, ff -40 C 1.32 V) are shown in full, the rest as extremes.
- One `.dc` walks all 256 codes: eight B-sources derive the bits from one swept voltage (`verify/common.py`), which makes 200-sample Monte Carlo over the full range affordable.
- Transients sized per code: `enable` low for 2 nominal periods, released, 40 periods run, last 16 measured, step = period / 150. Same cycles and resolution at every code; start-up time comes free.
- Post-layout: kpex 2.5D (`make pex`) extracts the flat macro's capacitances against the LVS netlist; `layout/build_sim_post.py` rewrites them into the pre-layout netlist's place (same subcircuit, ports and labelled internal nets). The whole-block, environment and Liberty runs repeat on it (`--fscale 0.5`; `make lib`).
- Each script writes a CSV and a Markdown table into `analog/out/verify/`; `verify/report.py` assembles the results document.

## What is simulated

| test (`analog/verify/`) | netlist | corners, 45 PVT | mismatch MC | process MC | noise | post-layout |
|---|---|---|---|---|---|---|
| DAC (`dac.py`) | `csro_dac`, drain held at 0.6 V (also 0.46 and 0.85 V) | I(code): unit, code-0, full scale, DNL, INL, monotonic | 200: worst DNL and its code, monotonic count, unit sigma | 100: unit current spread | | |
| bias chain (`bias.py`) | DAC + MPD + MPM + MND + 11 replica starve devices at mid-rail | `vbp`, `vbn`, I_dac, I_stage vs code | 200: spread of the 11 stage currents, MPD/MPM ratio | | `.noise` at `vbp`, `vbn`, 1 kHz-1 GHz, 1 Hz-1 GHz, 1 kHz-1 MHz at codes 1, 16, 128, 255, as % of one code step | |
| stage (`stage.py`) | `csro_stage` between identical stages, real bias | tPLH, tPHL, slew at codes 0, 16, 128, 255; 1 / (22 delays) | | | `.noise` at the trip point / output slope = sigma_td per transition; x sqrt(22) per period, / sqrt(N) per count | |
| NAND (`nand.py`) | `csro_nand` | hold: `enable` 0, feedback swept full rail, min V(out); gate: delay vs a stage | | | | |
| buffer (`buffer.py`) | `csro_inv` + the 2/1 um inverter | 332 MHz, 100 ps edges into 15 and 108 fF: levels, 20-80 % edges, delay | | | | |
| whole block (`ring.py`) | `spice/tt_analog_ring.spice` | f at 10 codes; Idd running and disabled; `clk_out` held; start-up; monotonic; pushing %/V and ppm/C | 64: f at 0, 15, 16, 127, 128, 255; count of f(16) <= f(15), f(128) <= f(127) | 32: f(0), f(16), f(255), span | white bias-node current noise (`.noise` / `ac` impedance) injected as `trnoise`, 600 periods; quiet run = numerical floor | `verify-ring-post`: all of it again |
| PEX (`pex.py`) | extracted netlist | typical, codes 0, 16, 128, 255: capacitance per net and block; stage, NAND, buffer delay pre vs post; bias ripple; code bus settling through 500 ohm | | | | `sim-post` |
| environment (`environment.py`) | whole block | codes 16 and 255, 300 periods: 50 MHz ripple 10, 30, 100 mV pp; 10 mV rms broadband; 50 mV step; 30 mV pp ground bounce; full-swing 50 MHz aggressor via 20 fF onto `code[0]`, `code[7]`, `enable` (victims through 500 ohm) and 5, 10, 20, 30 fF onto `clk_out`; 5 ns `enable` edge | | | | `verify-env-post` |

Figures: `verify_dac.png`, `verify_bias.png`, `verify_stage.png`, `verify_ring_corners.png`, `verify_ring_mc.png`, `verify_ring_post_corners.png`, `verify_ring_post_mc.png`, `verify_env.png`, `verify_env_post.png`, `analog_ring_sim_post.png`.

## Key results

Generated 2026-09-07. Pre / post layout where both exist.

| question | result |
|---|---|
| oscillates and stops | runs at all 45 PVT points x 10 codes; `clk_out` never below 100 % of VDD with `enable` 0; NAND output >= 99.9 % of VDD over a full-rail feedback sweep; start-up <= 230 ns pre, 430 ns post (ss/125 C/1.08 V, code 0; 2-4 ns at code 255); buffer reaches both rails into 108 fF, edges <= 400 ps |
| monotonic | in code at 45 / 45 PVT points pre and post; DAC 200 / 200 mismatch samples, worst DNL -0.39 LSB at code 128 (then 64); whole block 64 / 64 pre, 63 / 64 post (below) |
| scale over PVT | f(255) 184 / 332 / 544 MHz pre, 89.7 / 164 / 274 MHz post at ss-hot-low / tt / ff-cold-high; span per code x2.75-2.96 pre, x2.86-3.06 post; stage delay alone x2.8-3.0; per-stage current x3.7-4.0 |
| die to die | sigma 5.3-5.7 % pre, 5.6-6.2 % post at every code; f(255)/f(0) 76-93 pre, 75-89 post |
| supply pushing, tt, codes 16 / 128 / 255 | 64 / 135 / 155 %/V pre; 75 / 136 / 154 post (the DAC's triode units follow the supply through the diode) |
| temperature, tt, codes 16 / 128 / 255 | -3859 / -2589 / -2124 ppm/C pre; -3582 / -2569 / -2193 post |
| DAC alone | DNL 0.000 at every corner with the drain held; current follows the drain by +-10 % over 0.46-0.85 V (the compression) |
| bias chain | I_dac / I_stage 41-47 against nominal 48 (different drain voltages); under mismatch the 11 stage PMOS currents differ 1.7 % rms at code 255, 7.4 % at code 1 (NMOS 5 %, 19 %): duty cycle, second order in f |
| NAND | 1.14-1.24x a stage's delay at every corner and code |
| stage vs whole block | 1 / (22 delays) runs 8-15 % above the transient: the NAND and the buffer's load on stage 10 |

The tap rule: the divided ring must stay under 250 MHz, so tap 3 is safe everywhere.

Noise, typical corner:

| term | codes | value | per reciprocal count |
|---|---|---|---|
| stage thermal noise, per transition (small-signal estimate) | 255 / 16 / 0 | 1.0 / 35 / 680 ps rms; 1640 / 6600 / 14000 ppm of the period | 116 / 468 / 990 ppm over 200 periods (code 0 is flicker from 1 kHz, a conservative bound that does not average as sqrt(N)) |
| white bias-node noise injected, period jitter | 16 / 128 | 10.2 / 0.84 ps pre (372 / 181 ppm); 14.1 / 1.27 ps post (255 / 134 ppm); numerical floor 4-13 ppm | 45 / 27 ppm pre, 47 / 14 ppm post on 50-period means |
| slow (1 kHz-1 MHz) noise on `vbn`, a code error within one measurement | 1 / 255 | 124 / 120 uV rms = 1.1 / 28 % of a `vbn` code step (`vbp`: 16 / 14 uV, 0.13 / 2.4 %); the step shrinks with code, the noise does not | ~0.1 LSB of f at the top codes, a few hundred ppm of scatter; from flicker of MND and MPM |

The counter's own resolution is +-1 count = 1 / 241 = 4100 ppm (200 periods, tap 3, code 255). Every term above is below it; a longer window (higher `TARGET_N`) buys resolution until the slow bias noise at a few hundred ppm is the floor.

## Post-layout findings

| item | pre-layout | post-layout |
|---|---|---|
| parasitic C (kpex, 334 capacitors) | | 721 fF: DAC and code buses 478, bias nodes 255, stage outputs 24, `enable` 11, starved rails 5, buffer 3 |
| stage output load | ~1 fF of device | +1.7 fF of wiring each (strap, Metal1 jog, coupling to neighbours and the `vbp`, `vbn`, `enable` lines) |
| f at codes 0 / 16 / 128 / 255, tt | 3.81 / 36.6 / 216 / 332 MHz | 1.97 / 18.1 / 105 / 164 MHz (-48 to -51 %) |
| f(255) at ss/125 C/1.08 V, ff/-40 C/1.32 V | 184, 544 MHz | 89.7, 274 MHz |
| stage / NAND / buffer delay at code 255 | 133 / 180 / 230 ps | 270 / 341 / 381 ps |
| code bus load | 9.6 fF (bit 0) to 1.30 pF (bit 7) | +8.5 fF (+89 %) to +210 fF (+16 %); settling through 500 ohm 1.53 -> 1.77 ns on bit 7; the Liberty carries it |
| bias ripple from the running ring, `vbp` / `vbn` | 0.3-0.6 / 5-7 mV | 0.8-1.7 / 5-8 mV |
| mismatch sigma of f at code 255 | 2.8 % | 2.1 % |
| f(128) - f(127), 64 mismatch samples | 0.13 .. 2.24 MHz, mean 1.2, 0 reversed | -0.12 .. 1.21 MHz, mean 0.58, 1 reversed |

- The one changed conclusion: parasitics halved every frequency step, finger mismatch did not shrink, so the 127->128 carry sits ~1.2 sigma from a reversed step (1.5 pre-layout). Expect a percent or two of dies to show a ~0.1 % reversed step there: a measurable feature of a binary DAC, not a fault, since the map is measured anyway. Fix: thermometer-code the top two bits, or dummies and common-centroid rows.
- Monotonic in code at all 45 PVT points; the stopped ring holds; relative spreads unchanged. RTL model, cocotb tests, constraints and datasheet use the post-layout values; the divider's tap rule only gets easier.
- The layout lesson (`analog_layout_notes.md`): the minimum-size stage inverters should have been 2-3x wider.

## Environment results

Pre and post layout, typical corner, codes 16 and 255 (`verify_env.png`, `verify_env_post.png`).

| injection | shift of mean f | period jitter | note |
|---|---|---|---|
| 50 mV supply step | -3.4 / -3.9 % at code 16, -7.9 / -7.8 % at 255 (pre / post) | | settles in 4-34 ns: no loop filter, the ring follows the supply at once, as the static pushing predicts |
| 50 MHz ripple 10 / 30 / 100 mV pp | -15 / -150 / -1800 ppm pre; -13..-29 / -200..-350 / -1600..-4000 ppm post (the curvature of f against VDD) | 12-45 / 35-130 / 120-460 ps | 25-period means 0.5-43 ps |
| 10 mV rms broadband supply noise | +50 to +500 ppm | 9-28 ps | |
| 30 mV pp ground bounce | -140 to -350 ppm | 30-130 ps | |
| 20 fF aggressor onto `code[0]`, `code[7]` | <= 15 ppm | | gate moves 33-61 mV around its rail |
| 20 fF aggressor onto `enable`, running / stopped | <= 80 ppm / 0 edges | | dips to 1.14 V / lifts to 60 mV: the ring stays stopped |
| 5 ns `enable` edge | 0 | | first period full length, no runt |
| 5 / 10 / 20 fF aggressor onto `clk_out` | <= 190 ppm | | undershoot to -0.15 V, 0 extra edges at the divider's 0.6 V threshold, both netlists |
| 30 fF aggressor onto `clk_out` | | | pre clean (min -0.17 V); post, code 16: one extra edge per run (min -0.29 V, GLITCH); code 255 clean |

- Supply is the sensitivity. Measure with the digital side quiet (only the reference clock running, the code changed between measurements); expect a few hundred ppm of supply-driven scatter otherwise. The pushing number converts an observed shift into millivolts.
- 30 fF is a neighbour at minimum spacing for a few hundred um; the tile's route to the mux is tens of um and the LEF obstruction and halo keep other nets off. The sharpest edge in the block; a wider last buffer stage next time.

## Caveats

- Noise in transient is injected, not intrinsic: ngspice has no device noise in transient. The bias white noise is injected, the stage thermal jitter is analytic; together they bracket the jitter.
- Flicker noise is in `.noise` (the 1 Hz-1 GHz vs 1 kHz-1 GHz columns) but not injected: below 10 MHz the bias node's own time constant turns it into slow drift that a reciprocal count averages and a bench repeats.
- Systematic mismatch (stress, well proximity, the partial rows of bits 3..0) is not in the PDK models, so not in the Monte Carlo; the random DNL margin covers a systematic term of the same size (`analog_layout_notes.md`).
- PEX is capacitance only, from a 2.5D BEOL model, not silicon-correlated; metal resistance is argued in `analog_layout_notes.md`.
- The environment is sources at chosen amplitudes, not the tile's real current profile or routing; the results are bounds.
- The Liberty is characterised at the typical corner only: no timing arc, and gate capacitances move little with corner.

## Design changes, in order

Wider stage inverters (the halving); thermometer-coded top bits or dummies with common centroid (the 127->128 carry); larger MND and MPM (bias flicker); a wider output stage (crosstalk); a cascode on the DAC's drain (compression and pushing). None is needed for what the tile asks.
