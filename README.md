![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg)

# Ring oscillator frequency meter, TTIHP 26b

A reciprocal frequency counter that measures one of eight on-chip ring
oscillators over the Tiny Tapeout pins. Slots 0..6 are standard-cell
rings; slot 7 is a hand-drawn current-starved ring with an 8-bit current
DAC (`analog/`), placed as a hard macro. Hardened clean (STA, DRC, LVS,
antenna), precheck passes.

| document | content |
|---|---|
| [docs/info.md](docs/info.md) | project page: what it is, how to use it |
| [docs/registers.md](docs/registers.md) | register map, formula, settings |
| [docs/pinmap.md](docs/pinmap.md) | pins, protocol, parallel vs SPI |
| [docs/rings.md](docs/rings.md) | the ring population |
| [docs/design_notes.md](docs/design_notes.md) | decisions and open questions |
| [docs/constraints.md](docs/constraints.md) | timing constraints |
| [analog/README.md](analog/README.md) | analog block: circuit, interface, build |
| [docs/analog_layout_notes.md](docs/analog_layout_notes.md) | analog layout |
| [docs/analog_verification.md](docs/analog_verification.md) | analog verification |
| [CLAUDE.md](CLAUDE.md) | working notes |

![sweep](docs/sweep.png)

## Layout

```
analog/         analog ring macro for slot 7
src/            RTL (Tiny Tapeout requires src/)
src/rings/      ring netlists, analog macro blackbox
sim/            ring model, cell delay stand-ins, testbenches
scripts/        sweep plotting
docs/           documents and plots
test/           cocotb test run by CI
```

## Make targets

Needs `iverilog`; plots need `matplotlib` (`make tools` builds a venv).
Each testbench prints `RESULT: PASS` or `RESULT: FAIL`.

| target | does |
|---|---|
| `make test` | every testbench |
| `make test_measure_core` | one testbench |
| `make sweep` | 8 rings x 256 codes to `build/sweep.csv`, `docs/sweep*.png` |
| `make cocotb` | the CI testbench |
| `make macro` | analog block: layout, Liberty, DRC, LVS (Docker) |
| `make -C analog verify` | analog block: corners, Monte Carlo, noise (Docker, ~1 h) |
| `make tools harden` | LibreLane the tile locally as CI does |
| `make precheck` | Tiny Tapeout precheck |

## Branches

| branch | what |
|---|---|
| `ring-osc-meter` | this: the instrument |
| `main` | mixed-signal hello world: digital tile with a hand-drawn inverter macro, LibreLane traps documented |
| `analog-inverter` | the inverse: analog custom-GDS tile with a digital macro |

---

## What is Tiny Tapeout?

Tiny Tapeout is an educational project that aims to make it easier and cheaper than ever to get your digital and analog designs manufactured on a real chip.

To learn more and get started, visit https://tinytapeout.com.

## Resources

- [FAQ](https://tinytapeout.com/faq/)
- [Digital design lessons](https://tinytapeout.com/digital_design/)
- [Join the community](https://tinytapeout.com/discord)
- [Build your design locally](https://www.tinytapeout.com/guides/local-hardening/)
