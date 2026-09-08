## Whole block: frequency and current against code
The macro's own netlist (the LVS reference), clk_out into 15 fF, released from enable=0 and measured over the last 16 of 40 nominal periods.

**Signoff corners:**
| PVT | code | f MHz | Idd running uA | Idd disabled uA | vbp V | vbn V | start-up ns | stage.py predicts MHz |
|---|---|---|---|---|---|---|---|---|
| tt_27C_1.20V | 0 | 3.81 | 6.6 | 5.8 | 0.855 | 0.255 | 127.3 | 4.4 |
| tt_27C_1.20V | 1 | 5.80 | 9.6 | 8.7 | 0.839 | 0.270 | 84.2 | n/a |
| tt_27C_1.20V | 2 | 7.82 | 12.7 | 11.5 | 0.827 | 0.281 | 63.0 | n/a |
| tt_27C_1.20V | 4 | 11.89 | 18.7 | 17.3 | 0.808 | 0.298 | 42.2 | n/a |
| tt_27C_1.20V | 8 | 20.11 | 30.7 | 28.6 | 0.782 | 0.321 | 25.4 | n/a |
| tt_27C_1.20V | 16 | 36.53 | 54.3 | 51.1 | 0.746 | 0.352 | 14.5 | 41.0 |
| tt_27C_1.20V | 32 | 68.35 | 100.3 | 94.9 | 0.698 | 0.391 | 8.0 | n/a |
| tt_27C_1.20V | 64 | 125.64 | 187.5 | 178.2 | 0.636 | 0.440 | 4.6 | n/a |
| tt_27C_1.20V | 128 | 215.66 | 344.9 | 329.7 | 0.557 | 0.501 | 2.8 | 238.8 |
| tt_27C_1.20V | 255 | 331.97 | 604.6 | 581.7 | 0.461 | 0.572 | 1.9 | 363.4 |
| ss_125C_1.08V | 0 | 2.11 | 3.3 | 2.9 | 0.804 | 0.196 | 229.9 | 2.4 |
| ss_125C_1.08V | 1 | 3.22 | 4.8 | 4.3 | 0.785 | 0.213 | 152.0 | n/a |
| ss_125C_1.08V | 2 | 4.34 | 6.2 | 5.7 | 0.771 | 0.226 | 113.5 | n/a |
| ss_125C_1.08V | 4 | 6.63 | 9.2 | 8.5 | 0.751 | 0.245 | 75.4 | n/a |
| ss_125C_1.08V | 8 | 11.25 | 15.0 | 14.1 | 0.723 | 0.270 | 45.4 | n/a |
| ss_125C_1.08V | 16 | 20.44 | 26.6 | 25.0 | 0.687 | 0.303 | 25.8 | 22.6 |
| ss_125C_1.08V | 32 | 38.00 | 49.1 | 46.5 | 0.641 | 0.343 | 14.4 | n/a |
| ss_125C_1.08V | 64 | 69.21 | 91.6 | 87.3 | 0.584 | 0.393 | 8.3 | n/a |
| ss_125C_1.08V | 128 | 118.46 | 169.4 | 162.1 | 0.514 | 0.453 | 5.0 | 130.0 |
| ss_125C_1.08V | 255 | 184.03 | 299.7 | 288.9 | 0.430 | 0.523 | 3.3 | 200.5 |
| ff_-40C_1.32V | 0 | 5.95 | 12.2 | 10.2 | 0.962 | 0.271 | 81.5 | 6.9 |
| ff_-40C_1.32V | 1 | 8.98 | 17.8 | 15.3 | 0.947 | 0.284 | 54.2 | n/a |
| ff_-40C_1.32V | 2 | 12.01 | 23.2 | 20.4 | 0.935 | 0.295 | 40.7 | n/a |
| ff_-40C_1.32V | 4 | 18.12 | 33.8 | 30.5 | 0.917 | 0.311 | 27.5 | n/a |
| ff_-40C_1.32V | 8 | 30.41 | 54.9 | 50.6 | 0.890 | 0.333 | 16.6 | n/a |
| ff_-40C_1.32V | 16 | 55.37 | 96.8 | 90.4 | 0.852 | 0.364 | 9.4 | 63.9 |
| ff_-40C_1.32V | 32 | 105.15 | 179.1 | 168.6 | 0.800 | 0.404 | 5.1 | n/a |
| ff_-40C_1.32V | 64 | 198.69 | 336.0 | 318.4 | 0.730 | 0.456 | 2.9 | n/a |
| ff_-40C_1.32V | 128 | 350.26 | 620.6 | 591.6 | 0.639 | 0.522 | 1.7 | 391.6 |
| ff_-40C_1.32V | 255 | 543.74 | 1087.4 | 1043.6 | 0.525 | 0.600 | 1.1 | 598.0 |

**All 45 PVT points**, frequency extremes per code, and monotonicity:
| code | slowest MHz | at | fastest MHz | at | fast/slow |
|---|---|---|---|---|---|
| 0 | 2.06 | sf_125C_1.08V | 5.96 | fs_-40C_1.32V | 2.89 |
| 1 | 3.12 | sf_125C_1.08V | 9.02 | fs_-40C_1.32V | 2.89 |
| 2 | 4.20 | sf_125C_1.08V | 12.08 | fs_-40C_1.32V | 2.88 |
| 4 | 6.39 | sf_125C_1.08V | 18.26 | fs_-40C_1.32V | 2.86 |
| 8 | 10.88 | sf_125C_1.08V | 30.46 | fs_-40C_1.32V | 2.80 |
| 16 | 20.10 | sf_125C_1.08V | 55.37 | ff_-40C_1.32V | 2.75 |
| 32 | 38.00 | ss_125C_1.08V | 105.15 | ff_-40C_1.32V | 2.77 |
| 64 | 69.21 | ss_125C_1.08V | 198.69 | ff_-40C_1.32V | 2.87 |
| 128 | 118.46 | ss_125C_1.08V | 350.26 | ff_-40C_1.32V | 2.96 |
| 255 | 184.03 | ss_125C_1.08V | 543.74 | ff_-40C_1.32V | 2.95 |

f(code) monotonic over the codes simulated at 45 of 45 PVT points.

**Stopped** (enable=0, every PVT point and code): clk_out never below 1.080 V at the operating point, 1.080 V during the hold. Disabled supply current is the DAC's (2.9 .. 1044 uA over codes and corners). **Start-up**: worst release-to-first-edge 230 ns at ss_125C_1.08V code 0.

**Supply pushing and temperature coefficient** (typical process):
| code | f @1.08 V | f @1.20 V | f @1.32 V | %/V | f @-40 C | f @125 C | ppm/C |
|---|---|---|---|---|---|---|---|
| 16 | 33.2 | 36.5 | 38.8 | 64.0 | 46.9 | 23.7 | -3859 |
| 128 | 178.3 | 215.7 | 248.2 | 135.1 | 255.7 | 163.6 | -2589 |
| 255 | 268.2 | 332.0 | 392.1 | 155.4 | 384.6 | 268.3 | -2124 |

## Whole block: mismatch Monte Carlo, 64 samples (mos_tt_mismatch, 27 C, 1.2 V)
| code | mean MHz | sigma MHz | sigma % | min | max |
|---|---|---|---|---|---|
| 0 | 3.79 | 0.383 | 10.09 | 3.16 | 5.02 |
| 15 | 34.26 | 2.334 | 6.81 | 30.00 | 39.74 |
| 16 | 36.32 | 2.488 | 6.85 | 31.46 | 43.01 |
| 127 | 214.04 | 8.123 | 3.80 | 197.78 | 232.61 |
| 128 | 215.22 | 8.232 | 3.82 | 199.40 | 234.85 |
| 255 | 331.53 | 9.330 | 2.81 | 310.73 | 352.68 |

Major-carry steps: f(16) - f(15) = 1.256 .. 3.269 MHz, f(128) - f(127) = 0.127 .. 2.240 MHz. Non-monotonic samples: 0 at 15->16, 0 at 127->128, of 64.

## Whole block: process Monte Carlo, 32 samples (mos_tt_stat, 27 C, 1.2 V)
| code | mean MHz | sigma MHz | sigma % | min | max |
|---|---|---|---|---|---|
| 0 | 3.84 | 0.219 | 5.70 | 3.18 | 4.19 |
| 16 | 36.39 | 1.945 | 5.35 | 30.56 | 39.40 |
| 255 | 327.69 | 18.406 | 5.62 | 281.85 | 363.99 |

f(255)/f(0), the span of the scale, 76.2 .. 92.9 across samples.

## Whole block: noise on the bias node and the jitter it makes
| code | vbp current noise pA/sqrt(Hz) (white, 10M-1G) | vbp impedance kohm (1 kHz) | vbp voltage noise nV/sqrt(Hz) at 1 kHz | white-part voltage noise nV/sqrt(Hz) |
|---|---|---|---|---|
| 16 | 4.47 | 1.3 | 151.6 | 6.0 |
| 128 | 8.51 | 0.4 | 163.7 | 3.4 |

**Transient with the bias-node current noise injected** (typical, 27 C, 1.2 V; 600 periods; `quiet` = same run without the source, the numerical floor):
| code | run | periods | mean period ns | period jitter ps rms | ppm | jitter of 50-period means ps | ppm |
|---|---|---|---|---|---|---|---|
| 16 | quiet | 612 | 27.3217 | 0.15 | 5 | 0.00 | 0 |
| 16 | noise | 612 | 27.3211 | 10.16 | 372 | 1.23 | 45 |
| 128 | quiet | 617 | 4.6294 | 0.03 | 7 | 0.01 | 1 |
| 128 | noise | 617 | 4.6292 | 0.84 | 181 | 0.12 | 27 |

The injected source carries the white part of the current noise every device on vbp contributes (DAC units, diode, always-on units), measured by `.noise` at the same operating point and divided by the node's impedance from an `ac` analysis. Flicker noise below 10 MHz is not injected: the bias node's own time constant already filters it into slow drift, which a reciprocal count averages, and the stage's own thermal jitter is in stage.py.
