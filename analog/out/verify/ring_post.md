## Whole block: frequency and current against code
The macro's own netlist (the LVS reference), clk_out into 15 fF, released from enable=0 and measured over the last 16 of 40 nominal periods.

**Signoff corners:**
| PVT | code | f MHz | Idd running uA | Idd disabled uA | vbp V | vbn V | start-up ns | stage.py predicts MHz |
|---|---|---|---|---|---|---|---|---|
| tt_27C_1.20V | 0 | 1.97 | 6.7 | 5.8 | 0.855 | 0.255 | 237.3 | 4.4 |
| tt_27C_1.20V | 1 | 2.97 | 9.7 | 8.7 | 0.839 | 0.270 | 157.4 | n/a |
| tt_27C_1.20V | 2 | 3.97 | 12.7 | 11.5 | 0.827 | 0.281 | 118.9 | n/a |
| tt_27C_1.20V | 4 | 5.99 | 18.6 | 17.3 | 0.808 | 0.298 | 79.7 | n/a |
| tt_27C_1.20V | 8 | 10.03 | 30.5 | 28.6 | 0.782 | 0.321 | 48.5 | n/a |
| tt_27C_1.20V | 16 | 18.04 | 53.8 | 51.1 | 0.746 | 0.352 | 27.8 | 41.0 |
| tt_27C_1.20V | 32 | 33.51 | 99.3 | 94.9 | 0.698 | 0.391 | 15.5 | n/a |
| tt_27C_1.20V | 64 | 61.27 | 185.4 | 178.2 | 0.636 | 0.440 | 8.8 | n/a |
| tt_27C_1.20V | 128 | 105.23 | 341.3 | 329.7 | 0.557 | 0.501 | 5.3 | 238.8 |
| tt_27C_1.20V | 255 | 164.04 | 599.3 | 581.7 | 0.461 | 0.572 | 3.5 | 363.4 |
| ss_125C_1.08V | 0 | 1.08 | 3.3 | 2.9 | 0.804 | 0.196 | 429.6 | 2.4 |
| ss_125C_1.08V | 1 | 1.62 | 4.8 | 4.3 | 0.785 | 0.213 | 287.0 | n/a |
| ss_125C_1.08V | 2 | 2.18 | 6.2 | 5.7 | 0.771 | 0.226 | 215.8 | n/a |
| ss_125C_1.08V | 4 | 3.29 | 9.1 | 8.5 | 0.751 | 0.245 | 144.6 | n/a |
| ss_125C_1.08V | 8 | 5.52 | 14.9 | 14.1 | 0.723 | 0.270 | 88.0 | n/a |
| ss_125C_1.08V | 16 | 9.91 | 26.3 | 25.0 | 0.687 | 0.303 | 50.4 | 22.6 |
| ss_125C_1.08V | 32 | 18.31 | 48.6 | 46.5 | 0.641 | 0.343 | 28.3 | n/a |
| ss_125C_1.08V | 64 | 33.21 | 90.7 | 87.3 | 0.584 | 0.393 | 16.2 | n/a |
| ss_125C_1.08V | 128 | 56.96 | 167.5 | 162.1 | 0.514 | 0.453 | 9.7 | 130.0 |
| ss_125C_1.08V | 255 | 89.70 | 297.4 | 288.9 | 0.430 | 0.523 | 6.3 | 200.5 |
| ff_-40C_1.32V | 0 | 3.17 | 12.4 | 10.2 | 0.962 | 0.271 | 146.1 | 6.9 |
| ff_-40C_1.32V | 1 | 4.74 | 17.6 | 15.3 | 0.947 | 0.284 | 96.9 | n/a |
| ff_-40C_1.32V | 2 | 6.34 | 23.1 | 20.4 | 0.935 | 0.295 | 74.1 | n/a |
| ff_-40C_1.32V | 4 | 9.52 | 33.7 | 30.5 | 0.917 | 0.311 | 49.6 | n/a |
| ff_-40C_1.32V | 8 | 15.76 | 54.7 | 50.6 | 0.890 | 0.333 | 30.4 | n/a |
| ff_-40C_1.32V | 16 | 28.34 | 96.2 | 90.4 | 0.852 | 0.364 | 17.4 | 63.9 |
| ff_-40C_1.32V | 32 | 53.21 | 177.5 | 168.6 | 0.800 | 0.404 | 9.6 | n/a |
| ff_-40C_1.32V | 64 | 99.56 | 332.7 | 318.4 | 0.730 | 0.456 | 5.4 | n/a |
| ff_-40C_1.32V | 128 | 174.52 | 614.5 | 591.6 | 0.639 | 0.522 | 3.2 | 391.6 |
| ff_-40C_1.32V | 255 | 273.45 | 1077.5 | 1043.6 | 0.525 | 0.600 | 2.1 | 598.0 |

**All 45 PVT points**, frequency extremes per code, and monotonicity:
| code | slowest MHz | at | fastest MHz | at | fast/slow |
|---|---|---|---|---|---|
| 0 | 1.08 | ss_125C_1.08V | 3.17 | ff_-40C_1.32V | 2.95 |
| 1 | 1.62 | ss_125C_1.08V | 4.74 | ff_-40C_1.32V | 2.92 |
| 2 | 2.18 | ss_125C_1.08V | 6.34 | ff_-40C_1.32V | 2.91 |
| 4 | 3.29 | ss_125C_1.08V | 9.52 | ff_-40C_1.32V | 2.89 |
| 8 | 5.52 | ss_125C_1.08V | 15.76 | ff_-40C_1.32V | 2.86 |
| 16 | 9.91 | ss_125C_1.08V | 28.34 | ff_-40C_1.32V | 2.86 |
| 32 | 18.31 | ss_125C_1.08V | 53.21 | ff_-40C_1.32V | 2.91 |
| 64 | 33.21 | ss_125C_1.08V | 99.56 | ff_-40C_1.32V | 3.00 |
| 128 | 56.96 | ss_125C_1.08V | 174.52 | ff_-40C_1.32V | 3.06 |
| 255 | 89.70 | ss_125C_1.08V | 273.45 | ff_-40C_1.32V | 3.05 |

f(code) monotonic over the codes simulated at 45 of 45 PVT points.

**Stopped** (enable=0, every PVT point and code): clk_out never below 1.080 V at the operating point, 1.080 V during the hold. Disabled supply current is the DAC's (2.9 .. 1044 uA over codes and corners). **Start-up**: worst release-to-first-edge 430 ns at ss_125C_1.08V code 0.

**Supply pushing and temperature coefficient** (typical process):
| code | f @1.08 V | f @1.20 V | f @1.32 V | %/V | f @-40 C | f @125 C | ppm/C |
|---|---|---|---|---|---|---|---|
| 16 | 16.2 | 18.0 | 19.4 | 75.2 | 22.9 | 12.3 | -3582 |
| 128 | 87.0 | 105.2 | 121.5 | 136.4 | 125.4 | 80.7 | -2569 |
| 255 | 133.0 | 164.0 | 193.5 | 153.6 | 191.9 | 132.5 | -2193 |

## Whole block: mismatch Monte Carlo, 64 samples (mos_tt_mismatch, 27 C, 1.2 V)
| code | mean MHz | sigma MHz | sigma % | min | max |
|---|---|---|---|---|---|
| 0 | 1.97 | 0.171 | 8.68 | 1.65 | 2.32 |
| 15 | 17.01 | 0.999 | 5.87 | 14.77 | 18.97 |
| 16 | 18.00 | 1.040 | 5.78 | 15.55 | 20.16 |
| 127 | 104.38 | 3.008 | 2.88 | 97.50 | 110.30 |
| 128 | 104.96 | 3.062 | 2.92 | 98.12 | 111.45 |
| 255 | 163.65 | 3.465 | 2.12 | 156.01 | 171.12 |

Major-carry steps: f(16) - f(15) = 0.627 .. 1.320 MHz, f(128) - f(127) = -0.120 .. 1.209 MHz. Non-monotonic samples: 0 at 15->16, 1 at 127->128, of 64.

## Whole block: process Monte Carlo, 32 samples (mos_tt_stat, 27 C, 1.2 V)
| code | mean MHz | sigma MHz | sigma % | min | max |
|---|---|---|---|---|---|
| 0 | 1.98 | 0.122 | 6.17 | 1.61 | 2.17 |
| 16 | 17.98 | 1.014 | 5.64 | 14.95 | 19.67 |
| 255 | 162.11 | 9.110 | 5.62 | 139.39 | 180.28 |

f(255)/f(0), the span of the scale, 74.5 .. 88.6 across samples.

## Whole block: noise on the bias node and the jitter it makes
| code | vbp current noise pA/sqrt(Hz) (white, 10M-1G) | vbp impedance kohm (1 kHz) | vbp voltage noise nV/sqrt(Hz) at 1 kHz | white-part voltage noise nV/sqrt(Hz) |
|---|---|---|---|---|
| 16 | 4.47 | 1.3 | 151.6 | 6.0 |
| 128 | 8.52 | 0.4 | 163.7 | 3.4 |

**Transient with the bias-node current noise injected** (typical, 27 C, 1.2 V; 600 periods; `quiet` = same run without the source, the numerical floor):
| code | run | periods | mean period ns | period jitter ps rms | ppm | jitter of 50-period means ps | ppm |
|---|---|---|---|---|---|---|---|
| 16 | quiet | 604 | 55.3332 | 0.74 | 13 | 0.01 | 0 |
| 16 | noise | 604 | 55.3308 | 14.13 | 255 | 2.58 | 47 |
| 128 | quiet | 602 | 9.4862 | 0.04 | 4 | 0.00 | 0 |
| 128 | noise | 602 | 9.4859 | 1.27 | 134 | 0.13 | 14 |

The injected source carries the white part of the current noise every device on vbp contributes (DAC units, diode, always-on units), measured by `.noise` at the same operating point and divided by the node's impedance from an `ac` analysis. Flicker noise below 10 MHz is not injected: the bias node's own time constant already filters it into slow drift, which a reciprocal count averages, and the stage's own thermal jitter is in stage.py.
