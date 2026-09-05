# Basys3 prototype

Runs the Tiny Tapeout design (`src/project.v`) unchanged on a Digilent Basys3
(Artix-7 `xc7a35tcpg236-1`). The wrapper only maps the TT pin interface onto
board peripherals — it never modifies the design — so what you validate here is
the same RTL that gets hardened for the shuttle.

## Board mapping

| TT signal    | Board                     | Notes |
|--------------|---------------------------|-------|
| `ui_in[7:0]` | `sw[7:0]`                 | dedicated inputs |
| `uio_in[7:0]`| `sw[15:8]`                | only read where `uio_oe` is 0 |
| `uo_out[7:0]`| `led[7:0]`                | dedicated outputs |
| `uio_out`    | `led[15:8]`               | masked by `uio_oe`, so an undriven pin reads dark |
| `rst_n`      | `btnC`                    | pressed = reset; release is synchronised |
| `clk`        | divided 100 MHz           | see below |
| `ena`        | tied high                 | matches silicon, where it is 1 whenever powered |
| —            | 7-segment                 | `{uio_out, uo_out}` as four hex digits |

`btnL` and `btnR` are constrained but unused, free for your own design.

## Clocking

The 100 MHz oscillator is divided by `2**CLK_DIV_LOG2` (set in `build.tcl`,
default 24 → about 6 Hz) so state changes are visible on the LEDs. Set it to 0
to run the design at the full 100 MHz.

Hold `btnD` to switch to **single-step** mode: each press of `btnU` advances the
design one clock edge. Changing mode can clip a cycle, so press `btnC` to reset
after switching.

`build.tcl` emits a `create_generated_clock` matching `CLK_DIV_LOG2`, which is
why the divide factor lives there rather than in the Verilog — change it in one
place and the timing constraints follow.

## Build

```bash
source /tools/Xilinx/Vivado/<version>/settings64.sh

make lint    # Icarus elaboration check, no Vivado needed
make bit     # synth + place + route + bitstream -> build/tt_basys3_top.bit
make prog    # load onto an attached board over JTAG (volatile)
```

`make bit` exits non-zero if the design misses timing rather than handing you a
bitstream that silently doesn't work. Reports land in `build/`:
`timing_summary.rpt`, `utilization.rpt`, `drc.rpt`.

## Keeping it in sync with the shuttle

- `build.tcl` reads `../../src/project.v` directly. If you add source files,
  list them in **three** places: `info.yaml`, `test/Makefile`
  (`PROJECT_SOURCES`), and the `dut_sources` list in `build.tcl`.
- If you rename the top module from `tt_um_mgpauly1458_scratch`, update the `dut`
  instantiation in `tt_basys3_top.v` to match.

## What the FPGA will not tell you

The Basys3 has vastly more resources than a TT tile, so a design that fits here
can still be far too large for the shuttle. Utilisation on Artix-7 LUTs is not a
proxy for tile area — the GDS build in CI is the real check. Likewise, timing
here is against the 100 MHz board clock, not the ASIC's `CLOCK_PERIOD`.
