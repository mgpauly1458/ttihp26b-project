# The ring population

Eight slots selected by `RING_SEL`; only the selected ring is enabled, the
rest are held stopped by their NAND. Every ring has the interface
`code[7:0]`, `enable`, `clk_out` and drives the mux through a `buf_1` so
the loop node is never loaded directly.

| slot | module | stages | cells | code | measures |
|---|---|---|---|---|---|
| 0 | `ring_21_min` | 21 | `nand2_1` + 20 x `inv_1` | ignored | baseline process monitor |
| 1..3 | `ring_21_min` | 21 | identical netlist | ignored | within-die matching |
| 4 | `ring_21_hd` | 21 | `nand2_2` + 20 x `inv_8` | ignored | drive strength: frequency, tempco, supply pushing |
| 5 | `ring_11_min` | 11 | `nand2_1` + 10 x `inv_1` | ignored | stage-count scaling (expect ~21/11 x slot 0) |
| 6 | `ring_tap` | 5..19 | `nand2_1` + 18 x `inv_1` + 2 x `mux4_1` + `mux2_1` | bits [2:0] select the feedback tap: 0 = 19 stages, 7 = 5 stages | cell-level trim: monotonicity, step size |
| 7 | `tt_analog_ring` | 11 | hard macro (`analog/`) | all 8 bits, binary-weighted current DAC; 2 MHz at code 0, 164 MHz at 255 post-layout | the headline ring, `analog/README.md` |

## Expected frequencies

Typical Liberty (1.2 V, 25 C), fanout-of-one, no wire load; for choosing
`TAP_SEL`, not predictions. `make test_rings` checks each netlist hits its
closed-form period with these stage delays.

| slot | period | frequency |
|---|---|---|
| 0..3 | 2 x (65 + 20 x 55) ps = 2.33 ns | ~430 MHz |
| 4 | 2 x (60 + 20 x 60) ps = 2.52 ns | ~400 MHz |
| 5 | 2 x (65 + 10 x 55) ps = 1.23 ns | ~810 MHz |
| 6 | 2 x (65 + (18 - 2 x code) x 55 + 180 + 110) ps | 370 MHz (code 0) .. 870 MHz (code 7) |
| 7 | design target | 20 .. 400 MHz over the live codes |

## Simulation stand-ins (`-DSIM`)

`sim/ring_model.v` per slot; values in the ring files and `ring_bank.v`.

| slot | model |
|---|---|
| 0..3 | 350, 343, 357, 351 MHz |
| 4 | 380 MHz |
| 5 | 650 MHz |
| 6 | `code[2:0]` onto eight steps, 150..500 MHz |
| 7 | 2..164 MHz, no dead zone |

## Still open

- Region constraints: each ring compact, slots 1..3 at separate corners.
  Wire delay is a real fraction of stage delay; a scattered ring is a
  different ring.
- Don't-touch on every ring and `set_disable_timing` on one arc per loop:
  [constraints.md](constraints.md).
- Ninth ring, decision needed: a bank of `sg13g2_einvn_2/4/8` (tri-state
  inverters, `TE_B` active low) of mixed drive on one node, each enabled
  by a code bit, is the analog ring's trick at cell granularity. It would
  replace one of slots 1..3 or slot 5.
