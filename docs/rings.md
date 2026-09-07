# The ring population

Eight slots, selected by `RING_SEL`. Only the selected ring is enabled; the
other seven are held stopped by their NAND gate. Every ring has the same
interface (`code[7:0]`, `enable`, `clk_out`), including the analog macro.

| slot | module | stages | cells | code interpretation | what it measures |
|---|---|---|---|---|---|
| 0 | `ring_21_min` | 21 | `nand2_1` + 20 × `inv_1` | ignored | baseline process monitor |
| 1 | `ring_21_min` | 21 | identical netlist | ignored | within-die matching: same netlist, different corner of the tile |
| 2 | `ring_21_min` | 21 | identical netlist | ignored | |
| 3 | `ring_21_min` | 21 | identical netlist | ignored | |
| 4 | `ring_21_hd` | 21 | `nand2_2` + 20 × `inv_8` | ignored | drive strength vs. frequency, tempco, supply pushing |
| 5 | `ring_11_min` | 11 | `nand2_1` + 10 × `inv_1` | ignored | frequency scales with stage count as predicted (expect ≈ 21/11 × slot 0) |
| 6 | `ring_tap` | 5..19 | `nand2_1` + 18 × `inv_1` + 2 × `mux4_1` + `mux2_1` | **bits [2:0]** select the feedback tap; 0 = 19 stages (slowest), 7 = 5 stages (fastest); bits [7:3] ignored | coarse cell-level trim: monotonicity and step size |
| 7 | `tt_analog_ring` | 11 | hand-drawn hard macro (`analog/`) | **all 8 bits**, binary weighted current DAC; no dead zone, 2 MHz at code 0 and 164 MHz at 255 post-layout | the headline ring, see `analog/README.md` |

Every ring's output goes through a `buf_1` so the mux never loads the loop
node directly.

## Expected frequencies

From the typical-corner Liberty (1.2 V, 25 °C) at about fanout-of-one, with
no wire load. Real numbers will be lower once layout adds wire; these are
for choosing `TAP_SEL` and sanity-checking, not predictions.

| slot | period | frequency |
|---|---|---|
| 0..3 | 2 × (65 + 20 × 55) ps = 2.33 ns | ≈ 430 MHz |
| 4 | 2 × (60 + 20 × 60) ps = 2.52 ns | ≈ 400 MHz |
| 5 | 2 × (65 + 10 × 55) ps = 1.23 ns | ≈ 810 MHz |
| 6 | 2 × (65 + (18 − 2·code) × 55 + 180 + 110) ps | 370 MHz (code 0) .. 870 MHz (code 7) |
| 7 | design target | 20 .. 400 MHz over the live codes |

`make test_rings` simulates the structural netlists with those same stage
delays and checks each ring hits exactly its closed-form period, so a
mis-wired netlist fails there.

## Simulation stand-ins

With `-DSIM` every slot is replaced by `sim/ring_model.v`. Slots 0..3 are
given 350, 343, 357 and 351 MHz so the sweep shows a population instead of
four identical lines; slot 4 is 380 MHz; slot 5 is 650 MHz; slot 6 maps
`code[2:0]` onto eight steps between 150 and 500 MHz; slot 7 gets the
unpleasant curve (dead below 20, 20 to 400 MHz, quadratic). Those numbers
live in the ring files and `ring_bank.v`, marked as simulation-only.

## Things that need doing at the physical stage

- **Region constraints** so each ring is placed compactly, and so slots
  1..3 land at separate corners of the tile. Wire delay is a real fraction
  of stage delay; a ring scattered by the placer is a different ring.
- **Don't-touch** on every ring instance and `set_disable_timing` on one
  arc per loop (the NAND's `B` input is the obvious place). See
  [constraints.md](constraints.md).
- **A ninth ring?** SG13G2 ships tri-state inverters (`sg13g2_einvn_2/4/8`,
  active-low enable `TE_B`) and enabled buffers (`sg13g2_ebufn_2/4/8`). A
  bank of `einvn` cells of mixed drive driving one shared node, each
  enabled by a code bit, is the analog ring's trick at cell granularity,
  and having both on one die would compare cell-level and transistor-level
  implementations of the same idea directly. There is no free slot: it
  would replace one of slots 1..3 (losing one matching sample) or slot 5.
  **Decision needed.**
