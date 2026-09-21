# Register map

Eight write addresses (`ADDR`) and eight read selects (`RSEL`), 8 bits each;
wider values are split into bytes. Pins and protocol: [pinmap.md](pinmap.md).

## Write (ADDR)

| ADDR | name | bits | reset | meaning |
|---|---|---|---|---|
| 0 | `TRIM_CODE` | [7:0] | 0 | broadcast to every ring; meaning per ring in [rings.md](rings.md) |
| 1 | `RING_SEL` | [2:0] | 0 | ring slot enabled and measured |
| 2 | `TAP_SEL` | [2:0] | 0 | divide by `2^TAP_SEL` (1..128) |
| 3 | `TARGET_N` low | [7:0] | 0x00 | divided-ring periods per window |
| 4 | `TARGET_N` high | [15:8] | 0x01 | reset 256 in total; 0 behaves as 65536 |
| 5 | `TIMEOUT` low | [7:0] | 0xFF | give up after this many reference cycles |
| 6 | `TIMEOUT` high | [15:8] | 0xFF | reset 65535; 0 gives up immediately, on purpose |
| 7 | `CONTROL` | bit 0 | - | `START`, self-clearing pulse |

## Read (RSEL)

| RSEL | name | meaning |
|---|---|---|
| 0 | `STATUS` | bit 0 `done`, 1 `busy`, 2 `timeout_error`, 3 `write_ignored`, 7:4 zero |
| 1..4 | `RESULT[7:0]` .. `[31:24]` | reference-cycle count, low byte first |
| 5 | `TRIM_CODE` | readback |
| 6 | `{2'b0, TAP_SEL, RING_SEL}` | readback |
| 7 | `ID` | constant `0xA5`; read it first on new silicon |

## Statistics page (`ui_in[7]` = 1, index on `uio_in[4:0]`)

`stats_observer.v` watches every measurement that ends without
`timeout_error` and keeps running statistics of `RESULT`. It drives nothing
in the instrument; with `ui_in[7]` = 0 the chip behaves as if it were absent.

| index | name | meaning |
|---|---|---|
| 0..1 | `COUNT` | good measurements since the last configuration write; saturates at 65535 and freezes the rest |
| 2..3 | `MIN` | smallest `RESULT`; `0xFFFF` while `COUNT` = 0 |
| 4..5 | `MAX` | largest `RESULT`; `MAX - MIN` is the peak-to-peak spread |
| 6..9 | `SUM` | 32-bit sum; `SUM / COUNT` is the average, and the +-1 count error averages down about `sqrt(COUNT)` |
| 10 | `DICE` | free-running 8-bit LFSR, each `RESULT` bit 0 folded in; a random byte for whoever reads it |
| 11 | signature | constant `0x5A` |
| 12..25 | text | ASCII `RING METER 26B` |
| 26..31 | - | zero |

All little-endian. 16 bits hold any good `RESULT`: `TIMEOUT` is 16 bits and
covers the whole measurement, so a count that did not time out is below 65536. Cleared by reset and by any accepted write to `ADDR`
0..6 (rewrite `TRIM_CODE` with the same value to clear on purpose); `START`
does not clear. Use: configure once, write `START` and poll `done` N times
without reading `RESULT`, then read the page once.

## Status bits

| bit | set when | cleared by |
|---|---|---|
| `done` | a measurement ends, by success or timeout | next accepted `START` |
| `busy` | `START` accepted | `done` |
| `timeout_error` | fewer than `TARGET_N` divided edges within `TIMEOUT` cycles; `RESULT` is not valid (expected for a dead trim code) | next accepted `START` |
| `write_ignored` | a write arrived while `busy` and was dropped | next accepted `START` |

## Rules

- While `busy` every write is ignored, including `START`: `RING_SEL` and
  `TAP_SEL` would glitch a clock mux mid-count, `TRIM_CODE` would change
  the frequency mid-count, `TARGET_N` crosses into the ring domain
  unsynchronised and is safe only while static, `TIMEOUT` is blocked for
  uniformity.
- `RESULT` is a shadow latched when `done` rises and held until the next
  `done`, so its four byte reads cannot straddle two measurements.

## Formula

    f_ring = TARGET_N * 2^TAP_SEL * f_ref / RESULT

`RESULT` counts reference rising edges inside a window exactly `TARGET_N`
divided-ring periods long. Only error: reference-edge quantisation at each
end, +-1 count, the same for every ring (`measure_core.v` header).
Resolution `1/RESULT`; time `RESULT` reference cycles.

## Suggested settings, 50 MHz reference

| ring | `TAP_SEL` | `TARGET_N` | `RESULT` | time | resolution |
|---|---|---|---|---|---|
| 400 MHz | 3 | 1000 | ~1000 | 20 us | 0.1 % |
| 100 MHz | 1 | 1000 | ~1000 | 20 us | 0.1 % |
| 20 MHz | 0 | 400 | ~1000 | 20 us | 0.1 % |
| unknown | 3 | 200 | 50..2000 | < 50 us | first look, then refine |

`TIMEOUT`: a few times the expected `RESULT`. `TARGET_N` = 200, tap 3, a
20 MHz ring: 4000 counts; 16000 is safe and a dead code costs 320 us.
