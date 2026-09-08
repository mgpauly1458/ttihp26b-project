## Output buffer: swing and edges at 332 MHz
**Signoff corners**, both loads:
| PVT | load fF | VDD | V high | V low | high/VDD | low/VDD | rise 20-80 ps | fall 20-80 ps | delay ps |
|---|---|---|---|---|---|---|---|---|---|
| tt_27C_1.20V | 15 | 1.20 | 1.239 | -0.0308 | 1.032 | -0.0256 | 49 | 51 | 115 |
| tt_27C_1.20V | 108 | 1.20 | 1.210 | -0.0079 | 1.008 | -0.0066 | 258 | 245 | 262 |
| ss_125C_1.08V | 15 | 1.08 | 1.117 | -0.0307 | 1.034 | -0.0284 | 78 | 82 | 171 |
| ss_125C_1.08V | 108 | 1.08 | 1.088 | -0.0071 | 1.008 | -0.0065 | 401 | 403 | 404 |
| ff_-40C_1.32V | 15 | 1.32 | 1.354 | -0.0250 | 1.026 | -0.0189 | 33 | 34 | 83 |
| ff_-40C_1.32V | 108 | 1.32 | 1.330 | -0.0075 | 1.008 | -0.0057 | 165 | 168 | 177 |

**All 45 PVT points into 108 fF**: lowest high level 1.328 V (100.6 % of VDD) at ff_125C_1.32V; highest low level -0.0056 V at ff_125C_1.32V; slowest rise 401 ps at ss_125C_1.08V, slowest fall 403 ps at ss_125C_1.08V.
