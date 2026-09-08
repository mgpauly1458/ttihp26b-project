# Analog block: current-starved ring oscillator with an 8-bit current DAC

Hand-generated hard macro for ring slot 7 of the frequency meter. Every port is a rail-to-rail digital signal; everything analog is inside. Everything runs in the `hpretl/iic-osic-tools` container via `./run.sh`; Docker is the only host dependency.

## Files

| file | role |
|---|---|
| `macro/tt_analog_ring.gds`, `.lef` | layout and abstract, committed (CI cannot regenerate them); `make gds` writes both from one connectivity table |
| `lib/tt_analog_ring.lib` | Liberty for synthesis and STA, committed; `make lib` characterises it on the post-layout netlist |
| `spice/tt_analog_ring.spice`, `.lvs.spice` | finger-by-finger netlist the generator writes: what ngspice simulates and what LVS compares |
| `layout/build_tt_analog_ring.py` | the generator: GDS, LEF and both netlists from one set of constants |
| `layout/build_sim_post.py`, `render.py`, `lvs_diff.py` | kpex output rewritten for ngspice; layout PNGs; LVS mismatch lister |
| `layout/build_glb.py`, `build_gds3d_tech.py`, `tech/` | 3D views (`make glb`, `d25`, `view3d`, `gds3d-tech`) |
| `xschem/*.sch`, `*.sym`, `make_sch.py`, `wrap_flat.py` | schematic: `tt_analog_ring` top with `csro_dac`, `csro_nand`, `csro_stage`, `csro_inv` sub-sheets, generated from the layout's constants |
| `char/sweep_codes.py`, `plot_sweep.py`, `characterize.py` | f and I vs code sweep; its plot; Liberty characterisation |
| `verify/*.py` | corners, Monte Carlo, noise, PEX attribution, environment (`docs/analog_verification.md`) |
| `run.sh`, `gui.sh` | container wrappers, batch and with display |
| `out/` | build products, committed (waveforms via Git LFS, `out/.gitattributes`) so `VERIFY_REUSE=1 make verify ...` re-analyses stored runs in seconds instead of simulating; only `out/.cache` and `out/tile_3d.glb` are ignored |

Outside this directory: `src/rings/tt_analog_ring.v` (blackbox, slot 7), `src/config.json` (placement, halo, PDN), `docs/constraints.md` (the clock it becomes), `docs/analog_layout_notes.md`, `docs/analog_verification.md` and the generated `docs/analog_verification_results.md`.

## Make targets

| target | does |
|---|---|
| `make help` | every target, one line each |
| `make macro` | `gds lib drc lvs`: what the tile needs |
| `make gds`, `make png` | generator -> GDS, LEF, netlists; layout figures -> `../docs/` |
| `make drc`, `make drc-density` | KLayout, maximal rule set, `--no_density`; density rules alone (informational, a tile-level matter) |
| `make lvs`, `make lvs-diff` | KLayout LVS against the generator's netlist; list what did not match |
| `make sch`, `make sch-png`, `make xschem` | write the sheets; render `../docs/sch_*.png`; open (needs a display) |
| `make lvs-sch` | netlist the drawing flat, LVS it against the GDS |
| `make sim`, `make plot` | f and I vs code (`CODES= CORNER= TEMP= VDD=`) -> `../docs/analog_ring_sweep.png` |
| `make lib` | Liberty from the post-layout netlist (runs `pex` first) |
| `make pex`, `make sim-post` | kpex 2.5D capacitances; per-block attribution and pre/post side by side -> `../docs/analog_ring_sim_post.png` |
| `make verify` | every block then the whole macro: corners, Monte Carlo, noise (~1 h, `VERIFY_JOBS=14`; `verify-dac`, `-bias`, `-stage`, `-nand`, `-buffer`, `-ring`, `-report`) |
| `make verify-ring-post` | the whole-block run on the extracted netlist (~1.3 h) |
| `make verify-env`, `make verify-env-post` | the tile as sources: supply ripple, ground bounce, crosstalk; pre and post layout |
| `make all` | `macro lvs-sch sim plot png sch-png` |
| `make glb`, `d25`, `view3d`, `gds3d-tech` | 3D views; `klayout`, `shell`, `clean` |

Both PDK runners exit non-zero on failure, so `make` stops.

## Circuit

```
 code[7:0] --> 255 unit NMOS, binary weighted ------+
              (+2 always-on units, gate on VPWR)    | I_dac
                                                    v
                          diode PMOS MPD (24 x 2/0.5) -- vbp --> PMOS starve of every stage
                          PMOS mirror MPM (1/0.5) --> diode NMOS MND (0.5/0.5) -- vbn --> NMOS starve of every stage

 enable --> starved NAND -> 10 starved inverters ---+
              ^                                     |
              +------------- feedback (s10) --------+
                                                    +-> inverter -> inverter -> clk_out
```

| block | devices | W / L um | why |
|---|---|---|---|
| DAC (`csro_dac`) | bit k = 2^k identical NMOS fingers, source VGND, drain `vbp`, gate on `code[k]`; +2 fingers gated on VPWR | 0.15 / 8 | no bias, reference or start-up. L = 8 um: ~2.4 uA per fully-on finger (100 uA, 25 mW for the array, at minimum L). Always-on units keep code 0 alive, so a dead ring is distinguishable |
| diode MPD | PMOS, 24 fingers, sets `vbp` | 2 / 0.5 | wide so its gate voltage, and the DAC's drain node, sag less with current |
| mirror MPM, diode MND | PMOS, NMOS, set `vbn` | 1 / 0.5, 0.5 / 0.5 | one DAC, eleven copies of the same current |
| stage (`csro_stage`) x10 | inverter between a PMOS starve on `vbp` and an NMOS starve on `vbn` | inverter 0.5, 0.3 / 0.13; starves 1 / 0.5, 0.5 / 0.5 | each stage gets I_dac / 48 |
| NAND (`csro_nand`) | starved, inputs `enable` and feedback | series NMOS 0.6 | `enable` = 0 holds the output high: the loop stops in a defined state |
| buffer (`csro_inv` x2) | unstarved inverters | last 2 / 1 | the tile's mux never loads the loop node |

![](../docs/sch_tt_analog_ring.png)
![](../docs/sch_csro_stage.png)

All sheets: `docs/sch_*.png` (`make sch-png`). Two netlists, both LVS-checked against the GDS: the generator's (`make lvs`, 333 fingers) and the xschem drawing's (`make lvs-sch`).

## Code to frequency

Typical (tt, 27 C, 1.2 V), `clk_out` into 15 fF, whole block from `docs/analog_verification_results.md`:

| code | f pre-layout MHz | f post-layout MHz | Idd running uA (post) |
|---|---|---|---|
| 0 | 3.81 | 1.97 | 6.7 |
| 1 | 5.80 | 2.97 | 9.7 |
| 2 | 7.82 | 3.97 | 12.7 |
| 4 | 11.89 | 5.99 | 18.6 |
| 8 | 20.11 | 10.03 | 30.5 |
| 16 | 36.53 | 18.04 | 53.8 |
| 32 | 68.35 | 33.51 | 99.3 |
| 64 | 125.64 | 61.27 | 185.4 |
| 128 | 215.66 | 105.23 | 341.3 |
| 255 | 331.97 | 164.04 | 599.3 |

![](../docs/analog_ring_sweep.png)

- 2.0 MHz per code at the bottom pre-layout (1.0 post); full scale at 63 % of that line. Causes: the triode DAC units follow the diode node, 0.84 V at code 1 to 0.46 V at 255 (1 um diode fingers: 0.36 V and 45 %); above ~15 uA per stage the inverters' own delay is the floor.
- Post-layout is half as fast at every code and corner: ~1.7 fF of wiring per stage output against ~1 fF of device (kpex 2.5D, `make pex`). Shape, monotonicity and noise unchanged; side by side in `docs/analog_ring_sim_post.png`. RTL model, Liberty and constraints use the post-layout numbers.
- Supply current is the DAC current (2.4 uA per unit at full scale) plus tens of uA for mirror and ring. It flows whenever the code is non-zero, `enable` or not: park the code at 0 between measurements.

| over PVT and dies, post-layout | |
|---|---|
| f(255) at ss/125 C/1.08 V, tt, ff/-40 C/1.32 V | 89.7, 164, 274 MHz (pre: 184, 332, 544) |
| span of f at any code over the 45 PVT points | x2.9 to x3.1 |
| die-to-die sigma (process Monte Carlo) | 5.6 to 6.2 % |
| supply pushing at codes 16 / 128 / 255 (tt) | 75 / 136 / 154 %/V |
| temperature coefficient at codes 16 / 255 (tt) | -3600 / -2200 ppm/C |
| monotonic in code | all 45 PVT points; every Monte Carlo sample but one (127->128, post-layout, 1 of 64: `docs/analog_verification.md`) |

## Interface

| pin | layer, edge | meaning | Liberty (post-layout) |
|---|---|---|---|
| `code[7:0]` | Metal2, south | DAC code, DC control; bit 7 = 128 fingers | 18 fF on bit 0, doubling per bit to 1.52 pF on bit 7 |
| `enable` | Metal2, south | 1 = oscillate; 0 holds the loop, `clk_out` rests high | 13 fF |
| `clk_out` | Metal3, east | free-running output; no timing arc, so the tile must `create_clock` it on the macro instance | `max_capacitance` 108 fF |
| `VPWR`, `VGND` | Metal4 bars, full width | for the tile's PDN to via down to (`PDN_HORIZONTAL_LAYER: Metal4`) | |

A slow edge on a code bit is harmless; LibreLane sizes and buffers the drivers from the Liberty.

## Layout

90.72 x 56.7 um = 189 CoreSite widths x 15 rows, so it lands row-aligned. Figures: `docs/macro_layout.png`, `docs/ring_row_layout.png`, `docs/dac_rows_layout.png`. Strategy, concerns and PEX findings: `docs/analog_layout_notes.md`.

- DAC: 34 rows of unit fingers in mirrored pairs (bit 7: 16 rows of 8; bits 6..4: 8, 4, 2 rows; bits 3..0: one row of 8, 4, 2, 1). A pair shares a Metal1 `vbp` bar, VGND bars between pairs. One poly gate bar per row, jogged in Metal1 to a Metal2 code bus straight to the south pins. p+ tie islands mid-row and at both ends (LU.b: a tie within 20 um; rows are 69 um).
- Ring row: one oversized standard cell, NMOS strip bottom, PMOS top, five slots between them (Metal1 stage jogs, then `vbn`, `vbp`, feedback, `enable` on Metal2). Left to right: always-on units, MPD with MND and MPM, NAND, ten stages, buffer, Metal3 out east.
- Supplies: Metal1 rails under 3 x 3 via stacks to full-width Metal4 bars; NWell ties under VPWR, substrate ties under VGND.
- Grounded p+ guard ring; the LEF obstructs Metal1..Metal4 except the pin windows and the power bars.

## Signoff

| check | result |
|---|---|
| `make drc` (maximal rule set, `--no_density`) | 0 violations |
| `make lvs` (tap extraction off) | netlists match, 333 fingers |
| `make lvs-sch` | match |
| density | not checked at block level (`make drc-density` fails, expectedly); the tile's signoff DRC checks it |
| Liberty | typical corner only: no timing arc, and gate capacitances move little with corner |

## Not done

- Parasitic resistance: kpex 2.5D is capacitance only; the DAC's Metal1 bars are argued in `docs/analog_layout_notes.md`.
- Wider stage inverters (2-3x) or shorter output straps: the fix for the post-layout halving.
- Thermometer coding of the top DAC bits, or dummies and a common-centroid row order: the 127->128 carry.
- A cascode on the DAC's drain node: removes the compression and most of the supply pushing at the price of a real bias loop.
- The schematic is generated by `xschem/make_sch.py`; edit the `.sch` files directly only if you stop running `make sch`.
