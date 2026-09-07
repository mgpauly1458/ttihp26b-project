# Register map

Eight write addresses (`ADDR`) and eight read selects (`RSEL`). Everything
is 8 bits wide on the pins; the wider values are split into bytes.

## Write (ADDR)

| ADDR | name | bits | reset | meaning |
|---|---|---|---|---|
| 0 | `TRIM_CODE` | [7:0] | 0 | broadcast to every ring. Each ring interprets it its own way; see [rings.md](rings.md). |
| 1 | `RING_SEL` | [2:0] | 0 | which ring slot is enabled and measured |
| 2 | `TAP_SEL` | [2:0] | 0 | divider tap: divide by `2^TAP_SEL`, so 1, 2, 4, ... 128 |
| 3 | `TARGET_N` low | [7:0] | 0x00 | number of *divided-ring* periods to measure over |
| 4 | `TARGET_N` high | [15:8] | 0x01 | (reset value 256 in total). 0 behaves as 65536. |
| 5 | `TIMEOUT` low | [7:0] | 0xFF | give up after this many reference cycles |
| 6 | `TIMEOUT` high | [15:8] | 0xFF | (reset value 65535). 0 gives up immediately, on purpose. |
| 7 | `CONTROL` | bit 0 | - | `START`. Self-clearing: a pulse, not a stored bit. |

## Read (RSEL)

| RSEL | name | meaning |
|---|---|---|
| 0 | `STATUS` | bit 0 `done`, bit 1 `busy`, bit 2 `timeout_error`, bit 3 `write_ignored`, bits 7:4 zero |
| 1 | `RESULT[7:0]` | the reference-cycle count, low byte |
| 2 | `RESULT[15:8]` | |
| 3 | `RESULT[23:16]` | |
| 4 | `RESULT[31:24]` | |
| 5 | `TRIM_CODE` | readback |
| 6 | `{2'b0, TAP_SEL, RING_SEL}` | readback |
| 7 | `ID` | constant `0xA5`. Read this first on new silicon: if it does not come back, nothing else will. |

## Status bits

- `done` is set when a measurement ends, by success or timeout, and is
  cleared by the next accepted `START`.
- `busy` is high from an accepted `START` until `done`.
- `timeout_error` means `RESULT` is **not valid**: the ring produced fewer
  than `TARGET_N` divided edges within `TIMEOUT` reference cycles. This is
  the expected outcome for a dead trim code, and it is the difference
  between a dead ring and a broken interface.
- `write_ignored` is set when a write arrived while `busy` and was
  dropped. It stays set until the next accepted `START`, so a sweep script
  that checks `STATUS` after each measurement will catch its own race
  instead of getting a mysterious wrong number. Proposed in the brief as a
  question; adopted because it costs one flop.

## Rules

**While `busy`, every write is ignored**, including `START`. `RING_SEL` and
`TAP_SEL` were the brief's two, because they switch clock muxes and would
glitch the ring clock mid-count. `TRIM_CODE` would change the ring's
frequency mid-count. `TARGET_N` crosses into the ring clock domain without
a synchroniser and is only safe because it does not move while a
measurement runs. `TIMEOUT` is harmless but is blocked for uniformity: one
rule is easier to remember than a list. Enforced in hardware, flagged in
`STATUS`.

**`RESULT` is a shadow.** It is latched at the moment `done` rises and
holds until the next `done`, so reading its four bytes can never straddle
two measurements. A `START` between byte reads does not corrupt them.

## The formula

    f_ring = TARGET_N * 2^TAP_SEL * f_ref / RESULT

`RESULT` is the number of reference-clock rising edges inside a window that
is exactly `TARGET_N` divided-ring periods long. The window's opening and
closing edges each land somewhere between two reference edges, so `RESULT`
is the true ratio rounded to an integer: **±1 count**, no other systematic
term. The relative resolution is therefore `1/RESULT`. For 0.1 % choose
`TARGET_N` and `TAP_SEL` so `RESULT` is around 1000; the measurement takes
`RESULT` reference cycles. See `measure_core.v`'s header for where the ±1
comes from and why it is the same for every ring.

## Suggested settings, 50 MHz reference

| ring speed | `TAP_SEL` | `TARGET_N` | `RESULT` about | time | resolution |
|---|---|---|---|---|---|
| 400 MHz | 3 (÷8) | 1000 | 1000 | 20 µs | 0.1 % |
| 100 MHz | 1 (÷2) | 1000 | 1000 | 20 µs | 0.1 % |
| 20 MHz | 0 (÷1) | 400 | 1000 | 20 µs | 0.1 % |
| unknown | 3 | 200 | 50..2000 | < 50 µs | first look, then refine |

`TIMEOUT` should be a few times the expected `RESULT`. With `TARGET_N` = 200
and tap 3, 20 MHz gives 4000 counts; 16000 is a safe timeout and a dead
code costs 320 µs.
