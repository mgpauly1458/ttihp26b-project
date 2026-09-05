# Tiny Tapeout IHP 26b — local workflow

Notes for this checkout. Upstream docs: <https://tinytapeout.com/hdl/>

## How Tiny Tapeout actually works

You are not running the ASIC toolchain locally. The flow is:

1. Write Verilog in `src/`, with a top module named `tt_um_<something>`.
2. Verify it with cocotb + Icarus in `test/` — this is where you spend your time.
3. Optionally prototype on the Basys3 (`fpga/basys3/`) for real-world I/O.
4. Push to **your own GitHub repo**. GitHub Actions runs LibreLane against the
   IHP SG13G2 PDK and produces the GDS, a datasheet, and a gate-level netlist.
5. Submit the repo URL through the Tiny Tapeout website before the deadline.
6. TT merges your tile into the shuttle with everyone else's and tapes it out.

The GDS build only happens in CI. If the `gds` workflow badge is green and
precheck passes, your design is submittable. Nothing on your machine produces a
chip.

## The pin interface

Every project has exactly this interface — you cannot add ports:

```verilog
input  wire [7:0] ui_in;    // dedicated inputs
output wire [7:0] uo_out;   // dedicated outputs
input  wire [7:0] uio_in;   // bidirectional, input path
output wire [7:0] uio_out;  // bidirectional, output path
output wire [7:0] uio_oe;   // bidirectional, 1 = drive out
input  wire       ena;      // 1 whenever powered; ignore it
input  wire       clk;
input  wire       rst_n;    // active low
```

Rules that bite people:

- **Every output must be assigned**, including `uio_out` and `uio_oe`. Tie
  unused ones to 0.
- **No tristates, no `inout`.** The `uio_oe` signal is the only way to turn a
  bidirectional pin around.
- **One clock, one reset.** No gated or divided clocks inside your design, no
  latches, no async resets. Use a clock enable if you need something slower.
- **No initial values on registers.** Silicon powers up unknown; reset everything
  you depend on via `rst_n`.
- Anything you don't drive gets flagged by the linter, which runs in CI and is
  not optional.

## Local development

### Simulation (the main loop)

`test/` uses cocotb 2.0.1, which is pinned in a project-local `venv/` because it
has breaking API changes relative to the cocotb 1.9.2 installed system-wide.
Always activate it first:

```bash
source venv/bin/activate
cd test && make -B
```

`-B` matters: the Makefile doesn't track Verilog dependencies properly, so
without it you can silently test a stale build.

Waveforms are written to `test/tb.fst`:

```bash
gtkwave test/tb.fst test/tb.gtkw
```

### Gate-level simulation

After CI produces a netlist, download `gate_level_netlist.v` from the GDS
workflow artifacts into `test/`, then:

```bash
cd test && make -B GATES=yes
```

This needs `PDK_ROOT` pointing at an `ihp-sg13g2` install and catches real
problems the RTL sim cannot — X-propagation out of reset, and logic that only
worked because of an initial value.

### FPGA prototype

See `fpga/basys3/README.md`. Useful for interactive bring-up and for anything
involving real timing against external hardware. It tells you nothing about
whether the design fits in a tile.

## Before you submit

- [ ] `info.yaml`: fill in `title`, `author`, `description`, `clock_hz`, `tiles`,
      and rename `top_module` to `tt_um_<yourgithubusername>_<project>`.
- [ ] Rename the module in `src/project.v` to match `top_module` exactly.
- [ ] List every source file in `info.yaml` **and** `test/Makefile`'s
      `PROJECT_SOURCES` **and** `fpga/basys3/build.tcl`'s `dut_sources`.
- [ ] Fill in the `pinout` section of `info.yaml` — it becomes your datasheet.
- [ ] Write `docs/info.md`; it is published as your project page.
- [ ] Set `CLOCK_PERIOD` in `src/config.json` to match your `clock_hz`. The
      default is 20 ns (50 MHz). Raise it if CI reports setup violations.
- [ ] Confirm the `gds` and `precheck` GitHub Actions are green.

## Tile budget

A 1x1 tile is roughly 167x108 µm. `tiles` in `info.yaml` accepts
`1x1, 1x2, 2x2, 3x2, 4x2, 6x2, 8x2`. Start at `1x1`; if global placement fails,
first try raising `PL_TARGET_DENSITY_PCT` in `src/config.json` (up to ~80 is
reported to work), and only then ask for more tiles.
