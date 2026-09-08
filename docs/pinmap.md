# Pin map and readout protocol

Register contents: [registers.md](registers.md).

| pin | name | dir | meaning |
|---|---|---|---|
| `clk` | f_ref | in | reference clock, the only thing that must be accurate; 50 MHz assumed |
| `rst_n` | reset | in | active low |
| `ena` | master enable | in | 1 while this project is selected; all rings off otherwise |
| `ui_in[2:0]` | `ADDR` | in | write address 0..7 |
| `ui_in[3]` | `WE` | in | write strobe: one rising edge = one write |
| `ui_in[6:4]` | `RSEL` | in | which byte appears on `uo_out` |
| `ui_in[7]` | spare | in | unused |
| `uio_in[7:0]` | `WDATA` | in | write data; all bidirectionals are inputs (`uio_oe = 0`) |
| `uo_out[7:0]` | `RDATA` | out | byte selected by `RSEL`, registered |

## Protocol

| op | steps |
|---|---|
| write | set `ADDR`, `WDATA`; raise `WE`; hold >= 4 `clk`; lower `WE`; keep `ADDR`, `WDATA` until `WE` has been low >= 4 `clk` |
| read | set `RSEL`; wait >= 3 `clk`; read `uo_out` |
| measure | write `RING_SEL`, `TAP_SEL`, `TRIM_CODE`, `TARGET_N` (2 bytes), `TIMEOUT` (2 bytes); write 1 to `CONTROL`; poll `STATUS` until `done`; if `timeout_error` is clear read the 4 `RESULT` bytes |

The host is asynchronous to `clk`. `WE` passes a two-flop synchroniser
and edge detect; `ADDR` and `WDATA` are sampled on that edge, 2..3 `clk`
after the host raised `WE`, so they need no synchronisers of their own.
`RSEL` is sampled directly into the output register, so a read during an
`RSEL` change may return one wrong byte. A write costs about 200 ns at
50 MHz.

## Parallel strobe vs SPI

| | parallel strobe (built) | SPI-like on `uio` |
|---|---|---|
| pins | all 24 | 4, 20 free; nothing here needs them |
| debug | every signal is a level a probe can see | framing can be misread both ways |
| logic | one `WE` synchroniser, one output register | shift register, bit counter, frame decoder, `MISO` enable; `SCK` is a third clock domain crossing into `clk`; about 3x the logic |
| portability | Tiny-Tapeout-shaped | drops into any chip or FPGA |

Recommendation: parallel for this tapeout; first-silicon debuggability
dominates. The register map is independent of the pins, so an SPI front
end can replace `regfile.v`'s pin decode later without touching the
instrument or a sweep script written against write/read-register
primitives.
