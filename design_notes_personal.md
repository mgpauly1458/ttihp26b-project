# Personal notes: die area / are we maxed out

Own notes for the report, not part of the project docs set.

## Numbers

| quantity | value | source |
|---|---|---|
| TT allocation | 1x2 tile | README.md |
| Die area | 202.08 x 313.74 um = 63,400.6 um^2 | `src/user_config.json` `DIE_AREA`; confirmed in `runs/wokwi/13-openroad-floorplan/or_metrics_out.json` (`design__die__area`) |
| Core area (die minus margin) | 60,109.3 um^2 | same floorplan metrics file, `design__core__area` |
| Real logic+macro area (pre-filler) | 28,809 um^2, 1544 instances | `runs/wokwi/52-openroad-fillinsertion/or_metrics_out.json`, the metrics snapshot taken *before* that stage's filler-cell insertion |
| Placement density / utilization | **47.9%** of core area | `design__instance__utilization` in the same pre-filler snapshot |
| Post-filler instance area | 57,970.1 um^2, 4483 instances (~96.5% of core) | same file, *after* filler/decap insertion |
| Analog macro (slot 7) footprint alone | 90.720 x 56.700 um = 5,143.8 um^2 (~8.6% of core) | `analog/macro/tt_analog_ring.lef`, `SIZE` line |

## How I found this

- `src/user_config.json` carries the literal `DIE_AREA` LibreLane was told to use (`FP_SIZING: absolute` in `src/config.json`, so this is fixed, not auto-sized).
- Each LibreLane flow stage under `runs/wokwi/<N>-<stage>/` writes an `or_metrics_out.json` snapshot. `13-openroad-floorplan` is right after the floorplan step, so its die/core area numbers are the ground truth for the chip's physical size.
- `52-openroad-fillinsertion` conveniently contains *two* metrics snapshots in one file: the design state right before filler cells go in (real logic only: 28,809 um^2, 47.9%) and right after (57,970.1 um^2, ~96.5%). The jump between them is filler/decap cells the flow is required to insert to meet PDK tap/density DRC rules — that's not usable space, so it's not a meaningful "how full are we" number.
- The analog macro's own size comes straight from its LEF (`analog/macro/tt_analog_ring.lef`), which is the hard-macro footprint LibreLane's floorplanner treats as a fixed placed block.

## Answer: are we maxed out?

**No, not on standard-cell density.** Real placed-instance utilization is ~48% of the core area — LibreLane/OpenROAD flows are typically kept well under 100% (headroom is needed for routing, so pushing density much past ~70-80% usually blows up routing congestion/DRC before you'd ever hit "full"). There's room left for more logic if the design grew.

**What actually is fixed:**
- The **die size itself** (202.08 x 313.74 um) is not something this project controls — it's set by the TT `1x2` tile allocation. "More space" means buying/requesting a bigger allocation from Tiny Tapeout, not something solvable in the RTL/config.
- The **analog macro** is a fixed hard-macro block (8.6% of core) plus a PDN keepout margin around its edges (macro edges must stay clear of the TopMetal1 power straps, see CLAUDE.md's PDN-0110 lesson) — so its footprint effectively costs a bit more than its raw LEF size once you add that clearance.
- Open items in `CLAUDE.md`/`docs/design_notes.md` ("Not done yet") mention **region constraints for the corner rings (slots 1-3)** still being unresolved — that's a placement/floorplan-correctness gap, not a density/capacity one.

So: plenty of raw core area headroom by the numbers, but the die size is a hard allocation limit set outside this repo, and the fixed-footprint analog macro is the single biggest real consumer of the used area.
