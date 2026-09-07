<!---
This file is published as your project page. Keep the section headings; the
docs workflow checks for them.
-->

## How it works

An on-chip frequency meter. Eight ring oscillators sit on the tile; the
instrument measures whichever one is selected and reports the result as a
number over the pins, so characterising a trimmable oscillator across 256
trim codes, several rings, four temperatures and thirty chips becomes an
overnight script instead of a month with a bench counter.

It is a **reciprocal counter**: it counts how many cycles of the reference
clock (`clk`, supplied from the bench) fit into exactly `TARGET_N` periods
of the ring, after a programmable divide-by-1..128. Then

    f_ring = TARGET_N * 2^TAP_SEL * f_ref / RESULT

The only thing that must be accurate is `f_ref`, and that is a clock on an
ordinary digital input. No voltage reference, no bandgap, nothing analog in
the measurement chain, which is why it fits on a digital tile.

Everything except the rings is shared: one divider, one counter, one
window state machine, one register file. Because every ring is measured by
the same instrument, a difference between two rings is a real difference.

The ring population: four identical 21-stage minimum-drive rings, a
high-drive 21-stage ring, an 11-stage ring, a tap-select trimmed ring, and
in slot 7 a hand-drawn analog block: an 11-stage current-starved ring whose
current comes from an 8-bit binary-weighted array of 255 long-channel
transistors switched directly by the trim code, plus two always-on units
so code 0 still runs. It is a hard macro placed inside the digital tile;
simulated it runs from 3.8 MHz at code 0 to 332 MHz at code 255 at the
typical corner, monotonically, and spans roughly a factor of three over
process, supply and temperature. One 8-bit trim code is broadcast to all
eight rings.

## How to test

Interface: `ui_in[2:0]` is a write address, `ui_in[3]` a write strobe,
`uio_in[7:0]` write data, `ui_in[6:4]` selects which byte appears on
`uo_out`. Drive `clk` from an accurate source; 50 MHz is assumed below.

1. Reset. Set `ui_in[6:4]` = 7 and read `uo_out`: it must be `0xA5`.
2. Write registers (put address and data on the pins, pulse `ui_in[3]`
   high for at least 4 clocks): address 1 `RING_SEL` = 0, address 2
   `TAP_SEL` = 3, address 3/4 `TARGET_N` = 200 (low byte 200, high byte
   0), address 5/6 `TIMEOUT` = 16000 (0x80, 0x3E).
3. Write 1 to address 7 (`START`).
4. Read `STATUS` (`ui_in[6:4]` = 0) until bit 0 (`done`) is set. Bit 2 is
   `timeout_error`; if set, the ring did not run.
5. Read `RESULT` bytes with `ui_in[6:4]` = 1..4. With a 350 MHz ring the
   count is about 229; `f = 200 * 8 * 50 MHz / RESULT`.
6. Repeat with `RING_SEL` 0..7 and `TRIM_CODE` (address 0) 0..255.

Two rules of use. The divided ring (after `TAP_SEL`) must stay below
250 MHz, which is what the window logic is timed for: `TAP_SEL` = 3 is
safe for every ring at every corner; 2 is enough below 1 GHz. And the analog
ring (slot 7) at low codes is slow: at code 0 it runs about 3.8 MHz, so
200 periods through tap 3 take 420 us, longer than a 16000-cycle timeout
at 50 MHz; use tap 0 or 1 for low codes, or raise `TIMEOUT` (up to 65535
cycles, 1.3 ms). Change the code only between measurements.

Full register map, pin map and the sweep script are in the repository's
`docs/` and `scripts/`.

## External hardware

An accurate clock source for `clk` (the demo board's clock is fine for
bring-up; a lab source for characterisation). A microcontroller or the
demo board's RP2040 to run the sweep.
