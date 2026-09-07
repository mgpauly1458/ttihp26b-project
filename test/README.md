# Testbench

[cocotb](https://docs.cocotb.org/en/stable/) drives the tile and checks the
pins. `test.py` holds the tests; `tb.v` just instantiates the design and dumps
waveforms to `tb.fst`.

The analog inverter is a hard macro, so in simulation it is the behavioural
model in `src/tt_analog_inverter.v` that responds — compiled in by `-DSIM`,
which this Makefile passes in both modes. What these tests can prove is that
the tile is *wired* correctly: that `ui_in[0]` reaches the macro, that its
output reaches the pins and the flop, and that the logic reference agrees with
it. Whether the silicon inverter switches at the right threshold is an ngspice
question, and lives in `analog/`.

## Running

RTL:

```sh
make -B
```

Gate level, against the netlist the flow produced:

```sh
make -C .. test-gl        # copies the netlist in and runs it
```

## Gate level needs Tiny Tapeout's iverilog

Use the iverilog 13 build Tiny Tapeout ships, which is what CI installs:

```sh
wget https://github.com/TinyTapeout/iverilog/releases/download/v13.0/iverilog_13.0-1_amd64.deb
sudo apt-get install -y ./iverilog_13.0-1_amd64.deb
```

The IHP cell models take their flop inputs from the `delayed_*` signals that a
`$setuphold` timing check produces, and drive an X onto `Q` through a
`notifier`. Two versions get this wrong in opposite directions:

- **iverilog 12** (Ubuntu's package) leaves the notifier X and every flop
  output reads X for the whole run.
- **iverilog 14** (in the `iic-osic-tools` container) will not parse the
  models at all: `sorry: ifnone with an edge-sensitive path is not supported`.

Do not reach for `-gno-specify` to silence it. Dropping the specify blocks also
drops the `delayed_*` assignments the models depend on, so every flop goes X
for a different reason.

RTL simulation is unaffected and runs on any of them.

## Stimulus has to stay off the clock edges

`ClockCycles` returns *on* an edge, so assigning an input immediately afterwards
puts the data change at the same instant as `CLK` and trips `$setuphold`. The
`drive()` helper in `test.py` waits half a period first. Reset is released off
the edge for the same reason. None of this matters at RTL, which is exactly why
it is easy to write a test that passes there and fails at gate level.
