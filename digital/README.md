# Digital source for this tile

`ms_hello` — the RTL half of the mixed-signal tile. Everything runs inside the
`hpretl/iic-osic-tools` container via `./run.sh`, which already ships LibreLane
3.1 and the `ihp-sg13g2` PDK, so Docker is the only host dependency.

```bash
cd digital
make            # harden ms_hello and stage the artefacts in out/
make klayout    # open the hardened macro
```

The output is a **macro**, not a tile: `out/ms_hello.gds` plus its LEF and
netlists. `analog/layout/build_gds.py` reads that GDS and drops it into the tile
alongside the analog inverter. So the order is always digital first, then the
tile — `analog/Makefile` encodes that dependency, and `cd analog && make` does
the right thing on its own.

## What is here

```
../src/ms_hello.v     the RTL. Lives in src/ because Tiny Tapeout expects
                      source files there and info.yaml lists it
config.json           the LibreLane configuration
pin_order.cfg         all five signal pins on the north edge
out/                  staged results, committed: the tile build reads them
runs/                 LibreLane run directories, disposable and gitignored
```

## The design

```verilog
y_comb = ~a                          // combinational
y_reg  <= ~a  on posedge clk         // registered, cleared by rst_n
```

A purely combinational inverter would synthesise to one cell and exercise
neither clock tree synthesis nor timing analysis. The registered copy costs one
flip-flop and makes the flow do its whole job.

## Configuration, and why it is not the default

The macro is not a free-standing chip; it has to survive being dropped into a
tile that already has its own power grid and its own routing. Three settings
follow from that.

**`DIE_AREA` is absolute, 50 × 50 µm.** The tile has fixed empty space and the
macro has to fit in it. LibreLane's default margins are generous relative to a
die this small: the first attempt at 44 × 34 µm left a core area 3.76 µm tall
and floorplanning failed outright with `IFP-0002`, because a standard cell row
is 3.78 µm.

**The PDN is Metal1 rails plus vertical Metal4 straps, and nothing else.** The
PDK default puts straps on TopMetal1 and TopMetal2, which is exactly where the
tile's own power stripes and analog routing live. `FP_PDN_MULTILAYER: false`
drops the horizontal layer and the core ring, leaving supply that the tile can
reach with an ordinary via stack.

**`RT_MAX_LAYER` is Metal3.** Signals stop below the PDN so the two never
compete for Metal4 inside the macro, and the pins land on Metal2 where the tile
can pick them up.

**All five pins on the north edge** (`pin_order.cfg`). The tile's digital
interface stubs are along its top edge, so pins anywhere else would mean routing
around the macro.

## The interface the tile depends on

`analog/layout/build_gds.py` hard-codes pin positions read out of the LEF:

| | |
|---|---|
| die | 50 × 50 µm |
| signal pins | Metal2, 400 nm wide, north edge at y = 49.6–50.0 µm |
| pin x | `clk` 5.28, `rst_n` 14.88, `a` 24.48, `y_comb` 34.08, `y_reg` 43.68 |
| VPWR straps | Metal4, x = 15.66–17.86 and 35.66–37.86 µm |
| VGND straps | Metal4, x = 21.86–24.06 and 41.86–44.06 µm |
| strap extent | y = 14.9–34.24 µm |

Change the die size, the pin order or the PDN pitch and those numbers move.
`build_gds.py` checks the die size and fails loudly if it changes, but it cannot
catch a moved pin — if the flow is re-run with a different configuration, re-read
`out/ms_hello.lef` and update the constants in the `digital macro` section.
Tile-level LVS will catch it either way.

## Signoff

LibreLane runs its own DRC, LVS and antenna checks on the macro, and all three
pass. That is not the end of it: the merged tile is checked again from
`analog/`, because nothing in the macro's own signoff knows about the tile
around it.
