## Bias chain: operating points against code
Stage starve devices measured with their drains at 0.6 V. The nominal mirror ratio is 48:1 (24 x 2 um diode, 1 um stage device).

**Signoff corners:**
| PVT | code | vbp V | vbn V | I_dac uA | I_stage(p) uA | I_stage(n) uA | I_dac/I_stage |
|---|---|---|---|---|---|---|---|
| tt_27C_1.20V | 0 | 0.855 | 0.255 | 5.7 | 0.13 | 0.18 | 44.0 |
| tt_27C_1.20V | 1 | 0.839 | 0.270 | 8.5 | 0.19 | 0.27 | 44.1 |
| tt_27C_1.20V | 16 | 0.746 | 0.352 | 49.9 | 1.12 | 1.33 | 44.7 |
| tt_27C_1.20V | 128 | 0.557 | 0.501 | 322.6 | 7.04 | 7.34 | 45.8 |
| tt_27C_1.20V | 255 | 0.461 | 0.572 | 569.3 | 12.32 | 12.45 | 46.2 |
| ss_125C_1.08V | 0 | 0.804 | 0.196 | 2.8 | 0.06 | 0.09 | 45.7 |
| ss_125C_1.08V | 1 | 0.785 | 0.213 | 4.2 | 0.09 | 0.14 | 45.7 |
| ss_125C_1.08V | 16 | 0.687 | 0.303 | 24.5 | 0.53 | 0.68 | 45.9 |
| ss_125C_1.08V | 128 | 0.514 | 0.453 | 158.6 | 3.41 | 3.66 | 46.6 |
| ss_125C_1.08V | 255 | 0.430 | 0.523 | 282.8 | 6.03 | 6.24 | 46.9 |
| ff_-40C_1.32V | 0 | 0.962 | 0.271 | 10.0 | 0.24 | 0.34 | 40.8 |
| ff_-40C_1.32V | 1 | 0.947 | 0.284 | 14.9 | 0.36 | 0.49 | 41.1 |
| ff_-40C_1.32V | 16 | 0.852 | 0.364 | 88.3 | 2.05 | 2.39 | 43.0 |
| ff_-40C_1.32V | 128 | 0.639 | 0.522 | 578.7 | 12.87 | 13.25 | 45.0 |
| ff_-40C_1.32V | 255 | 0.525 | 0.600 | 1021.1 | 22.46 | 22.46 | 45.5 |

**All 45 PVT points**, per-stage PMOS current extremes (this is what sets the ring's delay):
| code | min I_stage(p) uA | at | max I_stage(p) uA | at | max/min |
|---|---|---|---|---|---|
| 0 | 0.06 | ss_125C_1.08V | 0.24 | ff_-40C_1.32V | 4.0 |
| 1 | 0.09 | ss_125C_1.08V | 0.36 | ff_-40C_1.32V | 3.9 |
| 16 | 0.53 | ss_125C_1.08V | 2.05 | ff_-40C_1.32V | 3.8 |
| 128 | 3.41 | ss_125C_1.08V | 12.87 | ff_-40C_1.32V | 3.8 |
| 255 | 6.03 | ss_125C_1.08V | 22.46 | ff_-40C_1.32V | 3.7 |

I_dac / I_stage(p) over every PVT point and code >= 1: 41.1 .. 47.3 (nominal 48; the deviation is the diode and the stage device sitting at different drain voltages).

## Bias chain: mismatch Monte Carlo, 200 samples (mos_tt_mismatch, 27 C, 1.2 V)
| code | stage PMOS current sigma/mean %, mean | worst sample | worst max-min % | stage NMOS sigma/mean % | MPM/MPD ratio sigma % | I_dac sigma % |
|---|---|---|---|---|---|---|
| 1 | 7.4 | 12.4 | 42.5 | 18.9 | 8.1 | 1.32 |
| 16 | 4.5 | 7.8 | 26.8 | 12.4 | 4.9 | 0.26 |
| 255 | 1.7 | 3.1 | 10.8 | 5.3 | 1.9 | 0.11 |

Each row: across the eleven stages within one sample (mean and worst over samples), then the mirror ratio and the DAC current across samples.

## Bias chain: noise at the bias nodes (typical, 27 C, 1.2 V)
| code | vbn noise uVrms 1k-1G | 1-1G | 1k-1M | vbn LSB step mV | noise/LSB % (1k-1G) | noise/LSB % (1k-1M) | vbp noise uVrms 1k-1G | 1-1G | 1k-1M | vbp LSB step mV | noise/LSB % (1k-1G) | noise/LSB % (1k-1M) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 679.1 | 686.3 | 124.4 | 11.17 | 6.1 | 1.11 | 189.0 | 189.4 | 15.9 | 12.24 | 1.5 | 0.13 |
| 16 | 585.3 | 594.1 | 109.3 | 3.12 | 18.8 | 3.50 | 147.4 | 147.9 | 13.8 | 3.72 | 4.0 | 0.37 |
| 128 | 499.1 | 511.5 | 114.2 | 0.75 | 66.9 | 15.29 | 86.2 | 87.3 | 14.0 | 0.99 | 8.7 | 1.41 |
| 255 | 473.5 | 488.1 | 120.0 | 0.43 | 110.3 | 27.95 | 66.2 | 67.6 | 14.0 | 0.59 | 11.2 | 2.36 |

Integrated output noise (rms) of the bias nodes with the code held, from ngspice `.noise` (PSP thermal + flicker; ngspice reports onoise_total as the rms voltage). "LSB step" is how far the node moves for one code step at that code; noise/LSB is the rms noise as a percentage of that step. The 1 kHz-1 GHz figure is everything the node carries; most of it is white noise above 1 MHz, which the ring turns into period jitter that a reciprocal count averages (ring.py measures that directly). The 1 kHz-1 MHz figure is the slow part that behaves like a code error within one measurement, and is the one to compare with a code step.
