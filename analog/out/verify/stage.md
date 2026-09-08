## Stage: delay against code and corner
A starved inverter driven by and loading identical stages, with the real bias chain at the code shown. The last column is 1 / (11 x (tPLH + tPHL)): the period an 11-stage ring of these would have.

**Signoff corners:**
| PVT | code | tPLH ps | tPHL ps | mean ps | rise 20-80 ps | fall 20-80 ps | slope up V/ns | slope down V/ns | 11-stage ring MHz |
|---|---|---|---|---|---|---|---|---|---|
| tt_27C_1.20V | 0 | 9818 | 10878 | 10348 | 16233 | 11466 | 0.05 | 0.10 | 4.4 |
| tt_27C_1.20V | 16 | 1011 | 1208 | 1110 | 1801 | 1443 | 0.53 | 0.67 | 41.0 |
| tt_27C_1.20V | 128 | 170 | 210 | 190 | 262 | 238 | 3.46 | 3.39 | 238.8 |
| tt_27C_1.20V | 255 | 114 | 136 | 125 | 154 | 139 | 6.07 | 5.72 | 363.4 |
| ss_125C_1.08V | 0 | 17341 | 20090 | 18716 | 29550 | 21057 | 0.02 | 0.05 | 2.4 |
| ss_125C_1.08V | 16 | 1765 | 2253 | 2009 | 3198 | 2649 | 0.28 | 0.32 | 22.6 |
| ss_125C_1.08V | 128 | 309 | 390 | 350 | 457 | 431 | 1.81 | 1.71 | 130.0 |
| ss_125C_1.08V | 255 | 203 | 250 | 227 | 261 | 252 | 3.17 | 2.89 | 200.5 |
| ff_-40C_1.32V | 0 | 6586 | 6502 | 6544 | 10035 | 6666 | 0.08 | 0.18 | 6.9 |
| ff_-40C_1.32V | 16 | 673 | 751 | 712 | 1152 | 873 | 0.79 | 1.27 | 63.9 |
| ff_-40C_1.32V | 128 | 104 | 128 | 116 | 171 | 148 | 5.76 | 6.00 | 391.6 |
| ff_-40C_1.32V | 255 | 69 | 83 | 76 | 102 | 87 | 10.25 | 10.04 | 598.0 |

**All 45 PVT points**, delay extremes:
| code | fastest mean delay ps | at | slowest mean delay ps | at | slow/fast |
|---|---|---|---|---|---|
| 0 | 6544 | ff_-40C_1.32V | 19033 | sf_125C_1.08V | 2.91 |
| 16 | 712 | ff_-40C_1.32V | 2009 | ss_125C_1.08V | 2.82 |
| 128 | 116 | ff_-40C_1.32V | 350 | ss_125C_1.08V | 3.01 |
| 255 | 76 | ff_-40C_1.32V | 227 | ss_125C_1.08V | 2.98 |

## Stage: thermal noise to timing jitter (typical, 27 C, 1.2 V)
| code | trip point V | gain at trip | output noise mVrms (1k-100G) | slope V/ns | sigma_td per transition ps | sigma per period ps (x sqrt 22) | ppm of period | ppm over N=200 periods |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.610 | -17.9 | 48.88 | 0.07 | 679.6 | 3187.7 | 14002 | 990 |
| 16 | 0.620 | -18.9 | 20.70 | 0.60 | 34.5 | 161.7 | 6625 | 468 |
| 128 | 0.605 | -18.1 | 5.88 | 3.43 | 1.7 | 8.0 | 1922 | 136 |
| 255 | 0.605 | -18.0 | 5.68 | 5.89 | 1.0 | 4.5 | 1641 | 116 |

Estimate: output noise of the stage held at its trip point (ngspice `.noise`, the load being the next stage), divided by the output slope at the half-rail crossing from the transient. Twenty-two such transitions make a period, uncorrelated, so the period jitter is sqrt(22) larger; a measurement of N periods averages it by sqrt(N). This is the white-noise floor of the instrument; it excludes the bias chain (bias.py) and the supply.
