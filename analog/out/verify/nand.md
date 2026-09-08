## NAND: enable=0 holds the loop
The output of the starved NAND with `enable` low, over a full-rail sweep of the feedback input, loaded by a stage. It never leaves the high rail; the stopped ring is stopped.

| PVT | code | VDD | min V(out) with enable=0 | as fraction of VDD | supply current uA (enable=0, whole NAND+bias, min over b) |
|---|---|---|---|---|---|
| tt_27C_1.20V | 0 | 1.20 | 1.2000 | 1.0000 | 5.8 |
| tt_27C_1.20V | 16 | 1.20 | 1.2000 | 1.0000 | 51.1 |
| tt_27C_1.20V | 255 | 1.20 | 1.2000 | 1.0000 | 581.7 |
| ss_125C_1.08V | 0 | 1.08 | 1.0799 | 0.9999 | 2.9 |
| ss_125C_1.08V | 16 | 1.08 | 1.0800 | 1.0000 | 25.0 |
| ss_125C_1.08V | 255 | 1.08 | 1.0800 | 1.0000 | 288.9 |
| ff_-40C_1.32V | 0 | 1.32 | 1.3200 | 1.0000 | 10.2 |
| ff_-40C_1.32V | 16 | 1.32 | 1.3200 | 1.0000 | 90.4 |
| ff_-40C_1.32V | 255 | 1.32 | 1.3200 | 1.0000 | 1043.6 |

Worst over all 135 runs (45 PVT x 3 codes): V(out) min = 1.0789 V = 99.90 % of VDD at ff_125C_1.08V code 0.

## NAND: as the eleventh inverter (enable=1)
| PVT | code | NAND tPLH ps | NAND tPHL ps | stage tPLH ps | stage tPHL ps | NAND/stage (mean) |
|---|---|---|---|---|---|---|
| tt_27C_1.20V | 0 | 13890 | 11059 | 9818 | 10878 | 1.21 |
| tt_27C_1.20V | 16 | 1450 | 1227 | 1011 | 1208 | 1.21 |
| tt_27C_1.20V | 255 | 160 | 146 | 114 | 136 | 1.22 |
| ss_125C_1.08V | 0 | 25594 | 20278 | 17341 | 20090 | 1.23 |
| ss_125C_1.08V | 16 | 2599 | 2288 | 1765 | 2253 | 1.22 |
| ss_125C_1.08V | 255 | 287 | 263 | 203 | 250 | 1.21 |
| ff_-40C_1.32V | 0 | 9126 | 6499 | 6586 | 6502 | 1.19 |
| ff_-40C_1.32V | 16 | 945 | 761 | 673 | 751 | 1.20 |
| ff_-40C_1.32V | 255 | 98 | 90 | 69 | 83 | 1.23 |

NAND delay / stage delay over all PVT points and codes: 1.14 .. 1.24. (Its NMOS are 0.6 um against the stage's 0.3 um to make up for the series stack.)
