## DAC: current against code
Drain held at 0.6 V. Endpoint fit; DNL/INL in units of the fitted LSB.
**Signoff corners** (the three LibreLane times the tile at):
| PVT | I(0) uA | I(1)-I(0) uA | unit uA | I(255) uA | DNL min | DNL max | at code | |INL| max | monotonic |
|---|---|---|---|---|---|---|---|---|---|
| tt_27C_1.20V | 5.16 | 2.58 | 2.575 | 662 | -0.000 | 0.000 | 128 | 0.00 | yes |
| ss_125C_1.08V | 2.66 | 1.31 | 1.307 | 336 | -0.000 | 0.000 | 128 | 0.00 | yes |
| ff_-40C_1.32V | 8.62 | 4.31 | 4.306 | 1107 | -0.000 | 0.000 | 128 | 0.00 | yes |

**All 45 PVT points**, extremes:
|  | min | at | max | at |
|---|---|---|---|---|
| unit current uA | 1.307 | ss_125C_1.08V | 4.306 | ff_-40C_1.32V |
| full scale uA | 336 | ss_125C_1.08V | 1107 | ff_-40C_1.32V |
| code-0 current uA | 2.66 | ss_125C_1.08V | 8.62 | ff_-40C_1.32V |
| DNL min | -0.001 | ff_125C_1.32V | -0.000 | ss_-40C_1.08V |
| DNL max | 0.000 | ss_-40C_1.08V | 0.000 | ff_125C_1.32V |
| |INL| max | 0.00 | ss_-40C_1.08V | 0.00 | ff_125C_1.32V |

Monotonic at 45 of 45 PVT points.

**Drain voltage sensitivity** (typical): the units are in triode, so the current follows the drain.
| PVT | I(0) uA | I(1)-I(0) uA | unit uA | I(255) uA | DNL min | DNL max | at code | |INL| max | monotonic |
|---|---|---|---|---|---|---|---|---|---|
| tt_27C_1.20V | 5.16 | 2.58 | 2.575 | 662 | -0.000 | 0.000 | 128 | 0.00 | yes |
| tt_27C_1.20V_vd0.46 | 4.43 | 2.21 | 2.212 | 569 | -0.000 | 0.000 | 128 | 0.00 | yes |
| tt_27C_1.20V_vd0.85 | 5.66 | 2.82 | 2.825 | 726 | -0.000 | 0.000 | 128 | 0.00 | yes |

## DAC: mismatch Monte Carlo, 200 samples (mos_tt_mismatch, 27 C, 1.2 V)
|  | value |
|---|---|
| samples monotonic | 200 / 200 |
| worst DNL (most negative step) | -0.393 LSB at code 128 |
| DNL min, mean over samples | -0.106 LSB |
| |INL| max, worst sample | 0.25 LSB |
| worst-DNL codes (count) | 128 (70), 64 (30), 192 (19) |
| unit current sigma/mean | 0.05 % |

## DAC: process Monte Carlo, 100 samples (mos_tt_stat, 27 C, 1.2 V)
|  | mean | sigma | sigma/mean | min | max |
|---|---|---|---|---|---|
| unit current uA | 2.560 | 0.113 | 4.4 % | 2.304 | 2.793 |
| code-0 current uA | 5.13 | 0.24 | 4.6 % | 4.61 | 5.67 |

Monotonic in 100 / 100 samples (global variation moves every finger together, so it cannot break the weighting).
