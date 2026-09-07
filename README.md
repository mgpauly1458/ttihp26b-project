![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg)

# On-chip ring oscillator frequency meter — TTIHP 26b

A small all-digital instrument that measures how fast a ring oscillator is
running and reports the result as a number over a handful of pins. Eight
ring slots (standard-cell rings of several kinds, plus a slot for a custom
analog macro) share one reciprocal counter, so ring-to-ring differences are
real differences. Built for characterising trimmable oscillators on real
silicon: sweep 256 codes × 8 rings × temperatures × chips from a script.

**This branch is the simulation phase.** The measurement chain is verified
against a behavioural ring model with a deliberately unpleasant transfer
curve (dead zone, offset, nonlinear), so that any strange number from real
silicon will be a statement about the silicon.

- [docs/info.md](docs/info.md) — what it is, how to use it (the project page)
- [docs/registers.md](docs/registers.md) — register map, the formula, settings
- [docs/pinmap.md](docs/pinmap.md) — pins, protocol, parallel-vs-SPI tradeoff
- [docs/rings.md](docs/rings.md) — the ring population
- [docs/design_notes.md](docs/design_notes.md) — decisions and open questions
- [docs/constraints.md](docs/constraints.md) — what hardening will need
- [CLAUDE.md](CLAUDE.md) — working notes

![sweep](docs/sweep.png)

## Layout

```
src/            synthesisable RTL (Tiny Tapeout requires src/)
src/rings/      structural ring netlists, and the analog stub
sim/            behavioural ring model, cell stand-ins, every testbench
scripts/        sweep plotting
docs/           register map, pin map, rings, notes, sweep plots
test/           the cocotb smoke test Tiny Tapeout's CI runs
```

## Running it

Needs only `iverilog`; the plots need `matplotlib` (`make tools` sets up a
venv with it).

```bash
make test                # every module testbench, in build order
make test_measure_core   # or one at a time
make sweep               # 8 rings x 256 codes -> build/sweep.csv, docs/sweep*.png
make cocotb              # the CI testbench
```

Each testbench prints `RESULT: PASS` or `RESULT: FAIL`.

## Branches

| branch | what |
|---|---|
| `ring-osc-meter` | **this**: the instrument |
| `main` | the mixed-signal hello world: a digital tile importing a hand-drawn CMOS inverter as a hard macro. The worked example for bringing the analog ring into this tile, with every LibreLane trap documented. |
| `analog-inverter` | the inverse arrangement: an analog custom-GDS tile with a digital macro merged into it |

---

## What is Tiny Tapeout?

Tiny Tapeout is an educational project that aims to make it easier and cheaper than ever to get your digital and analog designs manufactured on a real chip.

To learn more and get started, visit https://tinytapeout.com.

## Resources

- [FAQ](https://tinytapeout.com/faq/)
- [Digital design lessons](https://tinytapeout.com/digital_design/)
- [Join the community](https://tinytapeout.com/discord)
- [Build your design locally](https://www.tinytapeout.com/guides/local-hardening/)
