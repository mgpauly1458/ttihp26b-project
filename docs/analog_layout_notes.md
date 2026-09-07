# The analog block's layout: strategy, concerns, mitigations

How `analog/macro/tt_analog_ring.gds` was laid out and why, what could go
wrong with a block like this on a digital tile, and what was done about each
item. The companion documents are `analog/README.md` (the circuit and how to
build it) and [analog_verification.md](analog_verification.md) (how it was
simulated). Figures: `macro_layout.png` (the whole block),
`ring_row_layout.png` and `dac_rows_layout.png` (close-ups).

![](macro_layout.png)

## 1. What the layout has to be

The block is a **hard macro inside a digital tile**. That decides most of it:

| the tile's flow needs | so the layout is |
|---|---|
| a LEF abstract that LibreLane can place in its rows | 90.72 x 56.7 um: exactly 189 CoreSite widths (0.48 um) by 15 rows (3.78 um), so the macro lands flush in the standard-cell rows with no half-row gaps around it |
| supplies its PDN can reach | two horizontal Metal4 bars spanning the full width, VPWR on top, VGND under; the tile's TopMetal1 straps run vertically and every one that crosses the block meets both |
| pins on the edges, on routing layers | `code[7:0]` and `enable` on Metal2 at the south edge, `clk_out` on Metal3 at the east edge |
| to know where it may not route | the LEF declares Metal1..Metal4 obstructed over the whole footprint except the pin windows and the power bars |
| a netlist it can trust | the same script that draws the GDS writes the LEF and the SPICE netlist, from one connectivity table (below) |

Two things it does *not* have to be: a standard cell (no Metal1 rails at the
row boundaries: a full-width Metal1 rail inside a macro short-circuits with
the tile's own rails and merged with a signal net in LVS on the earlier
inverter block) and dense (metal density is checked by the tile's own
signoff DRC over the whole tile, where the standard cells and the PDN supply
most of the metal; the block on its own is deliberately sparse).

## 2. One script, one description

`analog/layout/build_tt_analog_ring.py` places every transistor through a
`Mos` object that records what each source/drain column and the gate are
connected to, then writes the GDS, the LEF and both netlists (one for
ngspice, one in the device-line form KLayout LVS reads) from those records.

This is the central layout-quality decision. The netlist LVS compares against
is *what the script meant to draw*, so LVS becomes a check that the drawn
metal and poly implement the intent, and it cannot be fooled by a netlist
that was edited to match. It caught a real connectivity error during the
build: a PMOS internal strap drawn along the wrong edge of the device, which
shorted the wrong diffusion columns and which no DRC rule objects to.

The devices are the PDK's PCells (`nmos`, `pmos`, `via_stack` from the
`SG13_dev` library), never hand-drawn polygons, so their internal geometry is
the foundry's. Everything that connects to a PCell reads the PCell's actual
shapes back to find the diffusion and gate positions rather than assuming
them: the PCell's `w` is the total width, `ng` the finger count, and the
contact positions move with both.

The xschem schematic (`analog/xschem/`) is generated from the same size
constants and LVS-checked against the GDS separately (`make lvs-sch`), so the
human-readable drawing and the layout are proven to be the same circuit.

## 3. Floorplan

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

**The DAC is at the bottom, pins-side.** Its eight gate buses are the only
signals the tile drives into the block, and they are DC controls, so they
go straight to the south edge on Metal2 with no crossings. The ring is at
the top, its output leaves east. Nothing analog crosses a digital control.

**The ring row is one row.** All eleven stages, the bias devices and the
buffer share one NMOS strip and one PMOS strip, standard-cell style: VGND
rail under, VPWR rail over, gates vertical. This puts every stage's starve
device at the same distance from the wells and rails, in the same
orientation, at the same pitch, which is what gives them matched currents
from the common `vbp`/`vbn` lines (see 5).

## 4. The DAC array

**Unit-identical fingers.** All 257 DAC transistors (255 weighted, 2
always-on) are the *same* PCell finger, 0.15 um x 8 um, same orientation,
same pitch, same neighbours to left and right within a row. Weighting is by
count only. This is the only way a binary-weighted array can hope to be
monotonic: any systematic difference between "a bit-7 finger" and "a bit-0
finger" would be multiplied by the weight ratio. The layout has no such
difference by construction.

**Rows of eight, in mirrored pairs.** A row is eight fingers on one
diffusion strip with a common poly gate bar. Two rows face each other across
a shared Metal1 `vbp` bar (their drains) and each has a Metal1 VGND bar on
its outside (sources). Bits 7..4 fill 16, 8, 4 and 2 full rows; bits 3..0
are one row each of 8, 4, 2 and 1 fingers.

**Why L = 8 um.** A rail-to-rail gate is either fully on or off, so the
current per finger is set by W/L alone. At minimum length a 0.15 um finger
sinks ~100 uA and 255 of them would burn 25 mW; at L = 8 um it is ~2.3 uA
and the whole array at full scale is ~0.6 mA. The long channel also makes
the finger's current less sensitive to lithographic length error (2 nm on
8 um is 0.025 %) - the array's matching is by W and by Vt, not by L. It
costs area: the DAC is roughly two thirds of the block.

**Gate drive from the tile.** Each code bit is a Metal2 bus down the array
contacted to each of its rows' poly bar through a Metal1 jog at the row's
left end. A bit-7 bus therefore drives 128 gates of 0.15 x 8 um: 1.3 pF.
That is a lot for a standard cell to drive, and it is not hidden: the
Liberty file (`analog/lib/tt_analog_ring.lib`) carries the measured input
capacitance of every code pin, so LibreLane sizes and buffers the drivers
itself (it did: `buf_8` cells appear on the code nets in the hardened tile).
A slow edge on a code bit is harmless - the code is changed only between
measurements.

**Latch-up ties inside the array.** The PDK's LU.b rule wants a substrate
tie within 20 um of every n+ region, and a row is 69 um long. Each row is
split around a central column of p+ tie islands under the VGND bars, and
two more tie columns stand at the rows' left and right ends. The islands are
640 nm squares with two contacts each (a single long tie strip cannot meet
the contact-spacing rules where two rows meet: contacts must not merge at a
right angle), and every island carries the `pSD` implant - an `Activ` with
no `pSD` is n+, the opposite of a tie.

**Concern: the partial rows.** Bits 3..0 are rows of 8, 4, 2 and 1 fingers,
so their fingers see different neighbours at the row ends than a bit-7
finger in the middle of a full row does (stress and well-proximity effects
are systematic and not in the Monte Carlo models). *Mitigation:* the array
is arranged so that the smallest bits are at the LSB end where an error of
a fraction of a unit matters least to the frequency map (an LSB is ~2 MHz
of 332), the instrument measures the whole code-to-frequency curve on the
bench anyway, and the mismatch Monte Carlo puts the *random* DNL at the
major carries at a small fraction of an LSB with margin for a systematic
component of the same size. *Residual:* no dummy fingers at the row ends,
no common-centroid ordering of the rows. Both are the first two things to
add if measured DNL at the small bits is larger than simulated.

**Concern: IR drop along the bars.** A Metal1 VGND bar is 0.3 um wide and
serves two rows of eight fingers: 16 x 2.4 uA = 38 uA at full scale over
~35 um from the tie column to the row end - well under a millivolt of
drop, against a gate drive of 1.2 V. Not a concern in practice; the split
around the middle tie column halves the run anyway.

## 5. The ring row

**Order, left to right:** the two always-on units, the 24-finger diode MPD
with MND and MPM beside it, the NAND, the ten stages, the two buffer
inverters, and the Metal3 run east to `clk_out`.

**Each stage is `[NMOS starve | NMOS] / [PMOS starve | PMOS]`**, its output
strap on the right, so the Metal1 jog to the next stage's input pad crosses
nothing but poly. Between the NMOS and PMOS strips five horizontal slots
carry, bottom to top: the stage-to-stage Metal1 jogs, `vbn`, `vbp`, the
feedback and `enable`, the last four on Metal2. Every stage taps `vbp` and
`vbn` from the same two lines at the same relative position.

**The bias diode sits in the same row as the stages it biases.** MPD is 24
fingers of 2 um, the stages' starve PMOS is one finger of 1 um: same L,
same orientation, same well, same rail, with `vbp` a straight Metal2 line
between them. A mirror across a 70 um row is not a matched pair in the
analog-textbook sense (no interdigitation, no common centroid), and the
verification puts numbers on what that costs: the DC ratio I_dac/I_stage
sits at 41..47 against the nominal 48 across corners (the diode and the
stage device sit at different drain voltages, which the schematic has too),
and the stage-to-stage current spread under random mismatch is a few
percent at the codes that matter (`analog_verification_results.md`, bias
chain). Unequal stage currents change the duty cycle slightly and the
frequency to second order; nothing depends on the ratio being exactly 48.

**Concern: flicker noise of the small bias devices.** MND and MPM are single
0.5 um and 1 um fingers of L = 0.5 um. Their flicker noise appears directly
on `vbn`: the verification finds about 110-125 uV rms of slow (1 kHz-1 MHz)
noise on `vbn` at every code, which at the top codes is a quarter of one
code step of that node (the fast, white part is far larger but becomes
period jitter that the counter averages). *Assessment:* it is the largest
noise term in the block, worth roughly a tenth of an LSB in frequency at
the top codes and far less at the bottom, and it is slow enough that
repeated measurements average it. *Mitigation next time:* make MND and MPM
several times wider and longer at the same ratio (flicker noise scales as
1/WL, and the bias chain has area to spare beside the diode).

**The internal strap bug.** The PMOS PCell's source/drain columns are
strapped along one edge of the device; the first version strapped along the
edge that joins the *other* set of columns. DRC is silent about this: it is
legal metal. LVS found it as a mismatched net. This is the argument for
running LVS against a netlist the layout script did not write by hand.

**Feedback and enable.** The feedback from stage 10 back to the NAND runs
the length of the row on its own Metal2 slot; `enable` likewise. Both are
digital and full swing; they run beside `vbp`/`vbn` at minimum Metal2
spacing. *Concern:* coupling from the feedback edge into the bias lines.
*Mitigation and assessment:* the bias nodes are low impedance (the diode's
1/gm, tens of kohm at low codes falling to ~1 kohm at full scale) and the
coupling is periodic at the ring frequency itself, so it can shift the
frequency by a fixed small amount but cannot add jitter; the effect is
inside the transient simulation of the whole block, which uses the same
nets. Parasitic extraction has not been run (see 8), so the wire-to-wire
capacitance is not in that simulation; the effect is expected in the low
percent of frequency at most, and it is in the calibration.

## 6. Supplies, wells and the tile's PDN

Two Metal1 rails run the length of the ring row, and 3 x 3 via stacks lift
each to a full-width Metal4 bar. The tile's PDN is TopMetal1 vertical straps
(2.2 um wide, VPWR at 16.48 + 38.87n um, VGND 6.2 um beside it); with
`PDN_HORIZONTAL_LAYER: Metal4` in the tile config, pdngen drops vias where a
strap crosses a bar. The macro is 90.72 um wide, so two VPWR and two VGND
straps cross it and each bar is fed at two points.

**Concern: a strap clipped by the macro edge gets no via.** The first
placement put the left edge 0.8 um into a VPWR strap; pdngen warned
(PDN-0110) and fed the bar from the other straps only. *Mitigation:* the
placement x in `src/config.json` was chosen so neither edge falls on a
strap, with 1.7 um clearance. That is a tile-level knob, and the comment in
the config records the strap arithmetic so a future move can redo it.

**NWell ties under the VPWR rail, substrate ties under the VGND rail**, all
covered by the rails' own Metal1, so the wells are tied along the whole row.
The `ntap1` PCell draws a buried-layer (`nBuLay`) square as part of its
device; Magic's signoff DRC measures that against the PMOS p+ diffusion and
fails (`NBL.f`), so the ties are drawn without it. KLayout's block-level
deck never checks this; it appears only when the tile goes through
LibreLane - which it now has, with 0 Magic DRC errors.

## 7. Isolation from the digital tile

The block shares the tile's supply and substrate with ~4500 standard cells,
seven other ring oscillators and a 50 MHz reference clock. There is no
separate analog supply in a Tiny Tapeout digital tile, so the question is
how much of that reaches the ring's frequency.

- **A grounded p+ guard ring** surrounds the whole footprint, contacted
  along its length (contacts along one direction own the corners, so no two
  contact rows meet at a right angle).
- **The LEF obstructs Metal1..Metal4 over the footprint**, and the tile
  config adds an 8 um placement halo, so no standard cell abuts the guard
  ring and no tile route crosses the block on those layers. TopMetal1 and
  TopMetal2 straps of the PDN do cross it; they are supplies.
- **Supply pushing is measured, not assumed:** `df/dVDD` in
  `analog_verification_results.md` (whole block, typical corner). A
  current-starved ring is supply sensitive by nature - the stage current
  is set by a gate voltage referred to the rails - and the DAC's long
  fingers in triode follow the diode voltage. The number is there so that
  a measured frequency shift when the digital side is busy can be
  attributed. *Mitigation available on the bench:* measure with the
  reference clock as the only other activity, which is how the instrument
  is meant to be used (one ring enabled at a time, the code changed
  between measurements).
- **The always-on units mean the DAC's drain node is never floating**, so
  there is no high-impedance node to pick up digital switching.

## 8. Signoff, and what was not done

| check | tool | result |
|---|---|---|
| block DRC, maximal rule set, density off | KLayout, PDK deck (`make -C analog drc`) | 0 violations |
| block LVS against the generator's netlist | KLayout, PDK deck (`make -C analog lvs`) | match, 333 fingers |
| block LVS against the xschem schematic | same (`make -C analog lvs-sch`) | match |
| tile DRC, with the macro placed | Magic, in LibreLane | 0 errors |
| tile LVS | Netgen, in LibreLane | match (the macro as an abstract: the tile's LVS checks the wiring *to* it) |
| antenna | OpenROAD | 0 violating nets (the LEF pins carry gate/diffusion areas; the flow added 3 diodes) |
| density | Magic, tile level | passes (the block alone is sparse on purpose) |
| Tiny Tapeout precheck | `make precheck` | passes |

**Not done: parasitic extraction.** The row is dense enough that wire
capacitance on the stage nodes will shift the frequency by some percent,
and the coupling in section 5 is not in the simulation. kpex is in the
container and supports this PDK; the earlier block's notes on `main`
describe the shape of a `make pex`. The instrument calibrates the
code-to-frequency map on the bench, so the missing percent is a
correction, not a failure mode.

**Not done: dummies and common-centroid in the DAC** (section 4).

**Not done: a cascode on the DAC's drain node.** The compression of the
code-to-frequency curve (full scale at 63 % of the low-code line) is the
DAC units in triode following the sagging diode voltage. It is monotonic
and simulated, and a cascode would cost a real analog bias loop. Left as
the first design change if linearity turns out to matter more than
simplicity.
