## Environment: supply, ground and crosstalk (pre-layout netlist, typical, 27 C, 1.2 V)
| case | code | f MHz | shift ppm vs quiet | period jitter ps rms | 25-period mean jitter ps | max-min period ps | clk_out min V | edges | note |
|---|---|---|---|---|---|---|---|---|---|
| bounce_mvpp30_code16 | 16 | 36.594 | -152 | 32.28 | 1.12 | 105.2 | -0.017 | 179 |  |
| noise_mvrms10_code16 | 16 | 36.610 | 262 | 16.67 | 3.40 | 87.7 | -0.002 | 178 |  |
| quiet_code16 | 16 | 36.600 | 0 | 0.37 | 0.01 | 1.2 | -0.002 | 178 |  |
| ripple_mvpp100_code16 | 16 | 36.535 | -1782 | 119.40 | 3.80 | 383.5 | -0.002 | 179 |  |
| ripple_mvpp10_code16 | 16 | 36.599 | -15 | 11.89 | 0.46 | 39.1 | -0.002 | 178 |  |
| ripple_mvpp30_code16 | 16 | 36.595 | -151 | 35.71 | 1.17 | 116.6 | -0.002 | 178 |  |
| slow_enable_code16 | 16 | 36.600 | 0 | n/a | n/a | n/a | -0.002 | 57 | first edge 30.8 ns after enable starts rising; shortest early period 27.322 ns |
| step_code16 | 16 | 36.600 | 0 | n/a | n/a | n/a | -0.002 | 175 | before 36.600 MHz, after -50 mV 35.345 MHz (-34297 ppm); settled within 5.6 ns |
| xcode_bit0_code16 | 16 | 36.600 | 4 | 0.32 | 0.01 | 1.5 | -0.002 | 178 | gate moves -0.060..0.060 V |
| xcode_bit7_code16 | 16 | 36.600 | 4 | 2.18 | 0.08 | 8.8 | -0.002 | 179 | gate moves -0.045..0.045 V |
| xenable_running_code16 | 16 | 36.600 | 7 | 6.69 | 0.59 | 39.6 | -0.002 | 178 | enable dips to 1.140 V |
| xout_ff10_code16 | 16 | 36.597 | -97 | 12.68 | n/a | 107.2 | -0.101 | 40 | 39 periods; shortest 27.271 ns; 0 extra edge(s) at the 0.6 V threshold, clean |
| xout_ff20_code16 | 16 | 36.593 | -186 | 38.18 | n/a | 290.5 | -0.111 | 40 | 39 periods; shortest 27.181 ns; 0 extra edge(s) at the 0.6 V threshold, clean |
| xout_ff30_code16 | 16 | 36.590 | -274 | 44.22 | n/a | 277.3 | -0.173 | 40 | 39 periods; shortest 27.192 ns; 0 extra edge(s) at the 0.6 V threshold, clean |
| xout_ff5_code16 | 16 | 36.598 | -47 | 8.41 | n/a | 55.6 | -0.027 | 40 | 39 periods; shortest 27.295 ns; 0 extra edge(s) at the 0.6 V threshold, clean |
| bounce_mvpp30_code255 | 255 | 331.925 | -138 | 60.61 | 3.41 | 141.9 | -0.026 | 180 |  |
| noise_mvrms10_code255 | 255 | 332.103 | 398 | 9.17 | 2.34 | 46.8 | -0.012 | 180 |  |
| quiet_code255 | 255 | 331.971 | 0 | 0.02 | 0.01 | 0.1 | -0.011 | 180 |  |
| ripple_mvpp100_code255 | 255 | 331.416 | -1671 | 201.17 | 12.64 | 474.9 | -0.013 | 180 |  |
| ripple_mvpp10_code255 | 255 | 331.966 | -15 | 20.03 | 1.05 | 47.4 | -0.011 | 180 |  |
| ripple_mvpp30_code255 | 255 | 331.925 | -138 | 60.32 | 3.19 | 141.8 | -0.012 | 179 |  |
| slow_enable_code255 | 255 | 331.970 | -3 | n/a | n/a | n/a | -0.011 | 57 | first edge 6.0 ns after enable starts rising; shortest early period 3.012 ns |
| step_code255 | 255 | 331.970 | -1 | n/a | n/a | n/a | -0.012 | 172 | before 331.970 MHz, after -50 mV 305.706 MHz (-79118 ppm); settled within 3.9 ns |
| xcode_bit0_code255 | 255 | 331.972 | 4 | 0.08 | 0.02 | 0.6 | -0.011 | 180 | gate moves 1.140..1.260 V |
| xcode_bit7_code255 | 255 | 331.971 | 1 | 2.83 | 0.16 | 12.2 | -0.012 | 180 | gate moves 1.187..1.213 V |
| xenable_running_code255 | 255 | 331.980 | 28 | 1.12 | 0.10 | 12.5 | -0.011 | 180 | enable dips to 1.139 V |
| xenable_stopped_code255 | 255 | n/a | n/a | n/a | n/a | n/a | 1.200 | 0 | enable peak 0.060 V |
| xout_ff10_code255 | 255 | 331.941 | -91 | 4.86 | n/a | 36.8 | -0.092 | 40 | 39 periods; shortest 2.994 ns; 0 extra edge(s) at the 0.6 V threshold, clean |
| xout_ff20_code255 | 255 | 331.926 | -136 | 13.65 | n/a | 87.8 | -0.144 | 40 | 39 periods; shortest 2.968 ns; 0 extra edge(s) at the 0.6 V threshold, clean |
| xout_ff30_code255 | 255 | 331.922 | -147 | 25.38 | n/a | 169.3 | -0.151 | 40 | 39 periods; shortest 2.928 ns; 0 extra edge(s) at the 0.6 V threshold, clean |
| xout_ff5_code255 | 255 | 331.952 | -56 | 2.74 | n/a | 21.1 | -0.051 | 40 | 39 periods; shortest 3.002 ns; 0 extra edge(s) at the 0.6 V threshold, clean |

Shift is the mean frequency over the run against the quiet run at the same code; the counter reads that mean. Period jitter is what the ring does cycle to cycle; the 25-period mean jitter is closer to what a reciprocal count over hundreds of periods scatters by. 50 MHz ripple and bounce are square waves with 1 ns edges; the crosstalk aggressor is a full-swing 50 MHz square with 200 ps edges through 20 fF (30 fF onto clk_out), the victim driven through 500 ohm. Every case of a code uses the same maximum time step.
