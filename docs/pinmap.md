# Pin map and readout protocol

Tiny Tapeout gives every project 8 dedicated inputs, 8 dedicated outputs and
8 bidirectionals, plus `clk`, `rst_n` and `ena`. This is how the instrument
uses them.

| pin | name | direction | meaning |
|---|---|---|---|
| `clk` | f_ref | in | the reference clock. **The only thing that must be accurate.** Drive it from a lab source; the demo board's programmable clock works for bring-up. 50 MHz assumed throughout the docs. |
| `rst_n` | reset | in | active low, as the shuttle defines it |
| `ena` | master enable | in | 1 while this project is selected; all rings are off otherwise |
| `ui_in[2:0]` | `ADDR` | in | write address, 0..7 |
| `ui_in[3]` | `WE` | in | write strobe: one rising edge = one write |
| `ui_in[6:4]` | `RSEL` | in | which byte appears on `uo_out` |
| `ui_in[7]` | spare | in | unused |
| `uio_in[7:0]` | `WDATA` | in | write data. All eight bidirectionals are configured as inputs (`uio_oe = 0`). |
| `uo_out[7:0]` | `RDATA` | out | the byte selected by `RSEL`, registered |

The register contents are in [registers.md](registers.md).

## Protocol

**Write.** Put `ADDR` and `WDATA` on the pins. Raise `WE`. Hold everything
for at least 4 `clk` periods. Lower `WE`. Leave `ADDR` and `WDATA` alone
until `WE` has been low for at least 4 periods.

**Read.** Put `RSEL` on the pins. Wait at least 3 `clk` periods. Read
`uo_out`.

**Measure.** Write `RING_SEL`, `TAP_SEL`, `TRIM_CODE`, `TARGET_N` (two
bytes), `TIMEOUT` (two bytes). Write `1` to `CONTROL`. Poll `STATUS` until
`done`. If `timeout_error` is clear, read the four `RESULT` bytes and compute

    f_ring = TARGET_N * 2^TAP_SEL * f_ref / RESULT

Every one of those waits is there because the host is asynchronous to
`clk`. `WE` goes through a two-flop synchroniser and its rising edge is
detected; `ADDR` and `WDATA` are sampled on that detected edge, which is 2
to 3 `clk` periods after the host raised `WE`, so by then they have been
stable for that long. That is the entire reason they can be sampled
without synchronisers of their own. `RSEL` is sampled directly into the
output register: a read taken while `RSEL` is mid-change may return one
wrong byte, which the 3-period wait avoids. `uo_out` is registered so it
never glitches while the host is looking at it.

At 50 MHz a write costs about 200 ns and a measurement's worth of register
traffic about 2 µs. The measurement itself is the long part.

## Why a parallel address/data strobe and not SPI

The brief asked for the tradeoff, not a choice, so here it is.

**Parallel strobe (what is built).**

- Every signal is a level you can see with a logic probe. Debugging on the
  demo board is "set these pins, read those pins" with no framing to get
  wrong. When the first silicon does something odd, this matters more than
  anything else.
- No bidirectional turnaround. `uio` is input-only, so there is no
  possibility of two drivers on a pin, no `uio_oe` timing to think about.
- One `WE` synchroniser and one output register are the whole interface.
  There is very little to be wrong.
- Cost: it uses all 24 pins, and it is a Tiny-Tapeout-shaped interface. A
  future chip with different pin budgets would need it redrawn.

**SPI-like on the bidirectionals.**

- Four pins (`SCK`, `MOSI`, `MISO`, `CS`) instead of 24, leaving 20 free.
  Nothing in this project needs them, so that is not a win here.
- Ports cleanly: the same register map behind an SPI slave would drop into
  a future chip, a different shuttle or an FPGA unchanged, and every
  microcontroller has an SPI master. This is the genuine argument for it.
- Cost: an SPI slave is a shift register, a bit counter, a frame decoder
  and a `MISO` output enable, all clocked by `SCK`, which is a *third*
  clock domain. The register writes then cross from the `SCK` domain to
  `clk`, with the same held-level rules as everything else. Roughly three
  times the interface logic, and a framing protocol that can be misread in
  both directions. `MISO` needs `uio_oe` driven high on one pin, which is
  fine but is one more thing.

**Recommendation.** Parallel for this tapeout: the instrument is the point,
the interface is plumbing, and debuggability on first silicon dominates.
The register map is defined independently of the pins, so an SPI front
end can replace `regfile.v`'s pin decode later without touching the
instrument. If the sweep script is written against "write register /
read register" primitives, it will not notice.
