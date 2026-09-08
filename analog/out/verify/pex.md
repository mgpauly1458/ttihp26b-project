## Post-layout: where the parasitic capacitance is
kpex 2.5D on the flat macro: 334 capacitors, 721 fF in total (each counted once; the per-net column counts a coupling cap on both of its nets).

| block (group of nets) | nets | parasitic fF | to VPWR/VGND/substrate fF | to other signals fF |
|---|---|---|---|---|
| DAC and code buses | 8 | 478.1 | 321.0 | 157.1 |
| bias nodes | 2 | 255.3 | 140.5 | 114.8 |
| ring: stage outputs | 11 | 24.0 | 11.0 | 13.0 |
| ring: enable | 1 | 10.9 | 5.9 | 5.0 |
| ring: starved rails (unlabelled) | 23 | 5.3 | 3.1 | 2.2 |
| output buffer | 2 | 3.2 | 2.5 | 0.7 |

**Per net**, the ones that matter:
| net | parasitic fF | to supplies | to signals | largest partners (fF) | device cap on the net fF (Liberty, pre-layout) | wire / device % |
|---|---|---|---|---|---|---|
| code[0] | 8.52 | 3.15 | 5.37 | code[1] 3.8, VGND 3.1, code[7] 0.6 | 9.6 | 89 |
| code[1] | 12.24 | 3.76 | 8.48 | code[0] 3.8, VGND 3.7, code[2] 3.4 | 19.4 | 63 |
| code[2] | 16.96 | 6.06 | 10.90 | VGND 6.1, code[3] 5.5, code[1] 3.4 | 39.5 | 43 |
| code[3] | 25.33 | 11.85 | 13.48 | VGND 11.8, code[2] 5.5, code[4] 4.5 | 79.0 | 32 |
| code[4] | 35.41 | 20.28 | 15.13 | VGND 20.3, vbp 5.6, code[3] 4.5 | 159.0 | 22 |
| code[5] | 60.03 | 39.55 | 20.48 | VGND 39.5, vbp 11.2, code[4] 4.4 | 320.0 | 19 |
| code[6] | 109.60 | 78.29 | 31.31 | VGND 78.3, vbp 22.3, code[5] 4.2 | 643.0 | 17 |
| code[7] | 210.00 | 158.05 | 51.95 | VGND 158.0, vbp 44.6, code[6] 3.7 | 1295.0 | 16 |
| vbp | 238.31 | 133.70 | 104.61 | VGND 128.5, code[7] 44.6, code[6] 22.3 | n/a | n/a |
| vbn | 17.01 | 6.81 | 10.20 | vbp 7.7, VGND 6.7, s0 0.2 | n/a | n/a |
| enable | 10.91 | 5.91 | 5.00 | VGND 5.3, vbp 2.5, code[7] 1.6 | 2.2 | 496 |
| s0 | 1.79 | 0.87 | 0.92 | VGND 0.9, vbn 0.2, s1 0.1 | n/a | n/a |
| s1 | 1.66 | 0.88 | 0.78 | VGND 0.8, vbn 0.2, s2 0.1 | n/a | n/a |
| s2 | 1.66 | 0.88 | 0.78 | VGND 0.8, vbn 0.2, s1 0.1 | n/a | n/a |
| s3 | 1.66 | 0.88 | 0.78 | VGND 0.8, vbn 0.2, s2 0.1 | n/a | n/a |
| s4 | 1.66 | 0.88 | 0.78 | VGND 0.8, vbn 0.2, s3 0.1 | n/a | n/a |
| s5 | 1.66 | 0.88 | 0.78 | VGND 0.8, vbn 0.2, s4 0.1 | n/a | n/a |
| s6 | 1.67 | 0.88 | 0.78 | VGND 0.8, vbn 0.2, s5 0.1 | n/a | n/a |
| s7 | 1.67 | 0.89 | 0.78 | VGND 0.8, vbn 0.2, s6 0.1 | n/a | n/a |
| s8 | 1.66 | 0.88 | 0.79 | VGND 0.8, vbn 0.2, s7 0.1 | n/a | n/a |
| s9 | 1.69 | 0.87 | 0.82 | VGND 0.8, s10 0.2, vbn 0.2 | n/a | n/a |
| s10 | 7.26 | 2.23 | 5.03 | vbp 3.8, VGND 1.9, VPWR 0.3 | n/a | n/a |
| b1 | 1.64 | 1.14 | 0.50 | VGND 1.0, s10 0.3, clk_out 0.2 | n/a | n/a |
| clk_out | 1.56 | 1.34 | 0.23 | VGND 1.1, VPWR 0.2, b1 0.2 | n/a | n/a |

The stage outputs s1..s10 carry about 1.7 fF of wiring each: the output strap, its Metal1 jog across the row gap, and its coupling to the neighbouring straps and to the vbp/vbn/enable lines it runs under. A stage's own input is a 0.5 um and a 0.3 um gate at L = 0.13 um, about 1 fF, plus its drains; the wiring is therefore comparable to the device load, which is why the post-layout ring is slower (below). The code buses add 8 to 210 fF to gate loads of 10 to 1300 fF, i.e. 16 to 90 %, largest in fraction on the small bits whose few fingers still need a full-length bus.

## Post-layout: the same circuit twice (typical, 27 C, 1.2 V)
| code | f pre MHz | f post MHz | change % | stage delay pre ps | post ps | NAND pre ps | post ps | buffer s10->clk_out pre ps | post ps | vbp ripple pre mV | post mV | vbn ripple pre mV | post mV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3.81 | 1.97 | -48 | 11497 | 22127 | 16180 | 33041 | 1539 | 2219 | 0.34 | 0.81 | 5.01 | 4.83 |
| 16 | 36.59 | 18.07 | -51 | 1188 | 2422 | 1789 | 3453 | 638 | 1013 | 0.56 | 1.17 | 5.28 | 5.37 |
| 128 | 215.94 | 105.38 | -51 | 205 | 424 | 273 | 513 | 291 | 481 | 0.54 | 1.67 | 7.03 | 7.79 |
| 255 | 332.34 | 164.25 | -51 | 133 | 270 | 180 | 341 | 230 | 381 | 0.34 | 1.60 | 6.73 | 7.75 |

**Code bus settling** (10-90 %, driven 0 -> 1.2 V through 500 ohm, ring disabled):
| code bit | pre-layout ps | post-layout ps |
|---|---|---|
| 0 | 45 | 47 |
| 7 | 1534 | 1774 |

Stage delay is the mean over the ten stages of the time from a crossing of s_k to the next crossing of s_k+1, read off the running ring over its last three periods; the NAND is s10 to s0, the buffer s10 to clk_out. The bias ripple is the peak-to-peak movement of vbp and vbn while the ring runs, which the layout's coupling of the stage straps to the bias lines increases. Code bus settling is what the tile's driver sees; the code is a DC control, so nanoseconds do not matter.

**Frequency against code, pre and post layout, signoff corners** (from `ring.py` and `ring.py --netlist <pex>`):
| PVT | code | f pre MHz | f post MHz | post/pre % |
|---|---|---|---|---|
| tt_27C_1.20V | 255 | 331.97 | 164.26 | 49 |
| ss_125C_1.08V | 255 | 184.03 | 89.73 | 49 |
| ff_-40C_1.32V | 255 | 543.74 | 274.50 | 50 |
