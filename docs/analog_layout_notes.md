# Analog block layout notes

How `analog/macro/tt_analog_ring.gds` is laid out, what can go wrong for an analog macro on a digital tile, and what was done about each item. Companions: `analog/README.md` (circuit, build) and [analog_verification.md](analog_verification.md) (simulation). Figures: `macro_layout.png` (whole block), `ring_row_layout.png` and `dac_rows_layout.png` (close-ups).

![](macro_layout.png)

## Strategy

- A hard macro in a digital tile: 90.72 x 56.7 um = 189 CoreSite widths (0.48 um) x 15 rows (3.78 um), so it sits flush in the standard-cell rows. Pins on routing layers at the edges; two full-width Metal4 supply bars for the PDN; the LEF obstructs Metal1..Metal4 except pin windows and power bars.
- One script, one description: `analog/layout/build_tt_analog_ring.py` places every transistor through a `Mos` object recording its connections and writes GDS, LEF and both netlists (ngspice, KLayout LVS) from those records, so LVS checks drawn metal against intent. It caught a PMOS internal strap on the wrong device edge: legal metal, wrong diffusion columns, silent in DRC.
- Devices are the PDK's PCells (`nmos`, `pmos`, `via_stack` from `SG13_dev`), never hand polygons. Connections read the PCell's actual shapes: `w` is total width, `ng` the finger count, and the contacts move with both.
- The xschem schematic (`analog/xschem/`) is generated from the same constants and LVS-checked against the GDS separately (`make lvs-sch`).
- Not a standard cell: no full-width Metal1 rails at row boundaries (they short with the tile's rails; on the earlier inverter block one merged with a signal net in LVS). Not dense: density is a tile-level check where the standard cells and PDN supply the metal.
- Floorplan: the DAC at the bottom, its eight Metal2 code buses straight to the south pins with no crossings (DC controls); the ring row at the top, output east on Metal3. Nothing analog crosses a digital control.

```
   VPWR Metal4 bar ------------------------------------------------------
   [ ring row: always-on | MPD diode (24f) MND MPM | NAND | stage x10 | buffer ]--> clk_out (M3, east)
   VGND Metal4 bar ------------------------------------------------------
   [ DAC pair 1: row  (8 x bit7)  / vbp bar / row (8 x bit7)  ]   ties
   [ DAC pair 2 ...                                          ]   ties
   ... 17 pairs = 34 rows: 16 rows bit7, 8 rows bit6, 4 bit5, 2 bit4,
       then 8, 4, 2, 1 fingers for bits 3..0                        ...
   Metal2 code buses run straight down to the pins on the south edge
   p+ guard ring around everything
```

DAC array:

- All 257 fingers (255 weighted + 2 always-on) are the same PCell finger, 0.15 x 8 um, same orientation, pitch and in-row neighbours; weighting by count only. Any systematic difference between a bit-7 and a bit-0 finger would be multiplied by the weight ratio.
- A row is eight fingers on one diffusion strip with a common poly gate bar. Rows come in mirrored pairs sharing a Metal1 `vbp` bar (drains), with a Metal1 VGND bar (sources) between pairs. Bits 7..4 fill 16, 8, 4, 2 rows; bits 3..0 are one row of 8, 4, 2, 1 fingers.
- L = 8 um: a fully-on 0.15 um finger sinks ~2.3 uA (~100 uA at minimum L, 25 mW for the array). A 2 nm length error on 8 um is 0.025 %, so matching is by W and Vt. Cost: the DAC is ~2/3 of the block.
- Gate drive: one Metal2 bus per bit, contacted to each of its rows' poly bar through a Metal1 jog at the row's left end. Bit 7 = 128 gates = 1.3 pF (1.5 pF with its bus); the Liberty carries it and LibreLane buffers the drivers itself (`buf_8` on the code nets).
- Latch-up ties (LU.b: a tie within 20 um of every n+; rows are 69 um): each row splits around a central column of p+ tie islands under the VGND bars, plus columns at both row ends. Islands are 640 nm squares with two contacts (a long strip breaks contact spacing where rows meet) and carry `pSD` (an `Activ` without `pSD` is n+).

Ring row:

- One standard-cell-style row: NMOS strip bottom, PMOS top, VGND rail under, VPWR over, gates vertical. Left to right: the always-on units, MPD (24 fingers) with MND and MPM, the NAND, ten stages, two buffer inverters, the Metal3 run east.
- A stage is `[NMOS starve | NMOS] / [PMOS starve | PMOS]` with its output strap on the right, so the Metal1 jog to the next input crosses nothing but poly.
- Five horizontal slots between the strips, bottom to top: Metal1 stage jogs, `vbn`, `vbp`, feedback, `enable` (the last four Metal2). Every stage taps `vbp` and `vbn` at the same relative position.
- MPD sits in the same row, well and rail as the 1 um starve PMOS it mirrors, with `vbp` a straight Metal2 line between them. No interdigitation, no common centroid.

Supplies, wells, isolation:

- Two Metal1 rails along the ring row, 3 x 3 via stacks up to full-width Metal4 bars. The tile's PDN is TopMetal1 vertical straps (2.2 um wide, VPWR at 16.48 + 38.87n um, VGND 6.2 um beside); `PDN_HORIZONTAL_LAYER: Metal4` makes pdngen via where a strap crosses a bar. Two VPWR and two VGND straps cross the 90.72 um macro.
- NWell ties under VPWR, substrate ties under VGND, covered by the rails' own Metal1. `ntap1` is drawn without its `nBuLay` square: Magic's tile DRC measures it against the PMOS p+ (`NBL.f`); KLayout's block deck never checks it.
- A grounded p+ guard ring around the footprint, contacted along its length (contacts in one direction own the corners so no two contact rows meet at a right angle). The LEF obstruction plus the tile's 8 um placement halo (`src/config.json`) keep cells and routes off; only the PDN's TopMetal1/2 straps cross.

## Concerns

| concern | mitigation | residual risk |
|---|---|---|
| bits 3..0 are partial rows: different neighbours at the row ends (systematic, not modelled) | smallest bits at the LSB end (1 LSB ~1 MHz of 164 post-layout); the bench measures the whole curve; random DNL -0.39 LSB worst of 200 | 1 of 64 post-layout mismatch samples reverses the 127->128 step by 0.1 % (`analog_verification.md`): parasitics halved the step, mismatch did not shrink. No dummies, common centroid or thermometer top bits yet: first additions next time |
| IR drop along the 0.3 um Metal1 bars | a VGND bar serves 16 fingers = 38 uA over ~35 um from the tie column: well under 1 mV against 1.2 V of gate drive; the mid-row split halves the run | not simulated (kpex is capacitance only) |
| stage wiring as large as the devices (0.5 / 0.3 um minimum-length inverters) | none yet | half speed post-layout (164 vs 332 MHz at code 255); scale does not matter, monotonicity and noise unchanged, Liberty is post-layout. Next: inverters 2-3x wider (the starves set the current, so f barely moves), jog slot beside the NMOS strip |
| `clk_out` is a 15 fF node beside a digital tile | 2 / 1 um output inverter; LEF obstruction and halo keep routes off; the tile's route to the mux is tens of um | 20 fF aggressor clean; 30 fF gives one extra edge at the divider threshold at code 16 post-layout. Next: a wider last stage or a Schmitt receiver |
| MPD to stage mirror across a 70 um row, no common centroid | same L, orientation, well, rail; straight `vbp` | I_dac / I_stage 41-47 against 48; stage currents spread a few % rms under mismatch: duty cycle, second order in f |
| flicker noise of MND and MPM (single 0.5 and 1 um fingers, L 0.5 um) on `vbn` | none yet | 110-125 uV rms slow noise = 28 % of a `vbn` step at code 255, ~0.1 LSB of f; averages over repeats. Next: several times wider and longer at the same ratio |
| feedback and `enable` edges beside `vbp`, `vbn` at minimum Metal2 spacing | bias nodes are low impedance (1/gm: tens of kohm at low code, ~1 kohm at full scale); coupling is periodic at the ring frequency: a fixed shift, not jitter | bias ripple 0.8-1.7 mV on `vbp`, 5-8 mV on `vbn` post-layout; inside the calibration |
| a PDN strap clipped by the macro edge gets no via (PDN-0110) | the placement x in `src/config.json` clears both edges by 1.7 um; its comment records the strap arithmetic | tile-level knob; redo if the macro moves |
| no separate analog supply: ~4500 cells, seven rings and a 50 MHz clock share it | guard ring, obstruction, halo; pushing measured (75-154 %/V) so a shift can be attributed; the always-on units keep the DAC's drain node from floating | measure with only the reference clock running (`analog_verification.md`, environment) |

## PEX findings (kpex 2.5D: `make pex sim-post`)

| where | parasitic C | effect |
|---|---|---|
| total | 721 fF, 334 capacitors | |
| DAC and code buses | 478 fF | +8.5 fF (bit 0, +89 %) to +210 fF (bit 7, +16 %) on the gate loads; bus settling through 500 ohm 1.53 -> 1.77 ns on bit 7; DC controls, Liberty updated |
| bias nodes | 255 fF (`vbp` 238, mostly to VGND and `code[7:6]`) | lower impedance; harmless |
| stage outputs s1..s10 | 1.7 fF each (strap, jog, neighbours, bias lines) against ~1 fF of device | every stage delay doubles: f halves at every code and corner |
| `enable`, buffer, `clk_out` | 11, 3, 1.6 fF | none |
| resistance | not extracted | argued above |

## Signoff

| check | tool | result |
|---|---|---|
| block DRC, maximal rule set, density off | KLayout, PDK deck (`make -C analog drc`) | 0 violations |
| block LVS against the generator's netlist | KLayout, PDK deck (`make -C analog lvs`) | match, 333 fingers |
| block LVS against the xschem schematic | same (`make -C analog lvs-sch`) | match |
| tile DRC with the macro placed | Magic, in LibreLane | 0 errors |
| tile LVS | Netgen, in LibreLane | match (the macro as an abstract: the tile's LVS checks the wiring to it) |
| antenna | OpenROAD | 0 violating nets (the LEF pins carry gate and diffusion areas; the flow added 3 diodes) |
| density | Magic, tile level | passes (the block alone is sparse on purpose) |
| Tiny Tapeout precheck | `make precheck` | passes |

Not done: dummies and common centroid in the DAC; a cascode on the DAC's drain node (the compression, full scale at 63 % of the low-code line, is monotonic and simulated, and a cascode costs a real bias loop); parasitic resistance.
