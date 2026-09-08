## Environment: supply, ground and crosstalk (post-layout netlist, typical, 27 C, 1.2 V)
| case | code | f MHz | shift ppm vs quiet | period jitter ps rms | 25-period mean jitter ps | max-min period ps | clk_out min V | edges | note |
|---|---|---|---|---|---|---|---|---|---|
| bounce_mvpp30_code16 | 16 | 18.067 | -354 | 126.65 | 4.58 | 362.1 | -0.016 | 88 |  |
| noise_mvrms10_code16 | 16 | 18.082 | 492 | 27.81 | 5.36 | 133.8 | -0.002 | 88 |  |
| quiet_code16 | 16 | 18.074 | 0 | 0.22 | 0.00 | 0.7 | -0.001 | 88 |  |
| ripple_mvpp100_code16 | 16 | 18.001 | -3985 | 460.49 | 42.61 | 1495.8 | -0.001 | 88 |  |
| ripple_mvpp10_code16 | 16 | 18.073 | -13 | 44.50 | 1.33 | 125.5 | -0.001 | 88 |  |
| ripple_mvpp30_code16 | 16 | 18.067 | -346 | 132.63 | 5.12 | 381.2 | -0.001 | 89 |  |
| slow_enable_code16 | 16 | 18.074 | 0 | n/a | n/a | n/a | -0.001 | 28 | first edge 58.3 ns after enable starts rising; shortest early period 55.329 ns |
| step_code16 | 16 | 18.074 | 0 | n/a | n/a | n/a | -0.001 | 86 | before 18.074 MHz, after -50 mV 17.361 MHz (-39418 ppm); settled within 33.6 ns |
| xcode_bit0_code16 | 16 | 18.074 | 1 | 0.24 | 0.02 | 1.0 | -0.001 | 88 | gate moves -0.061..0.061 V |
| xcode_bit7_code16 | 16 | 18.074 | 0 | 10.10 | 0.83 | 39.9 | -0.001 | 88 | gate moves -0.033..0.033 V |
| xenable_running_code16 | 16 | 18.074 | 8 | 5.66 | 0.52 | 26.2 | -0.001 | 89 | enable dips to 1.139 V |
| xout_ff10_code16 | 16 | 18.073 | -25 | 11.16 | n/a | 66.7 | -0.080 | 20 | 19 periods; shortest 55.298 ns; 0 extra edge(s) at the 0.6 V threshold, clean |
| xout_ff20_code16 | 16 | 18.073 | -51 | 30.37 | n/a | 182.1 | -0.109 | 20 | 19 periods; shortest 55.241 ns; 0 extra edge(s) at the 0.6 V threshold, clean |
| xout_ff30_code16 | 16 | 19.027 | 52739 | 12316.76 | n/a | 55165.0 | -0.288 | 21 | 20 periods; shortest 0.230 ns; 1 extra edge(s) at the 0.6 V threshold - GLITCH |
| xout_ff5_code16 | 16 | 18.072 | -58 | 21.98 | n/a | 114.3 | -0.045 | 20 | 19 periods; shortest 55.273 ns; 0 extra edge(s) at the 0.6 V threshold, clean |
| bounce_mvpp30_code255 | 255 | 164.215 | -241 | 102.36 | 4.92 | 280.6 | -0.021 | 89 |  |
| noise_mvrms10_code255 | 255 | 164.264 | 52 | 14.20 | 4.65 | 80.3 | -0.007 | 89 |  |
| quiet_code255 | 255 | 164.255 | 0 | 0.07 | 0.00 | 0.2 | -0.006 | 89 |  |
| ripple_mvpp100_code255 | 255 | 163.997 | -1568 | 340.15 | 15.87 | 941.8 | -0.008 | 89 |  |
| ripple_mvpp10_code255 | 255 | 164.250 | -29 | 34.10 | 1.54 | 93.7 | -0.007 | 89 |  |
| ripple_mvpp30_code255 | 255 | 164.222 | -198 | 102.15 | 4.68 | 281.0 | -0.007 | 89 |  |
| slow_enable_code255 | 255 | 164.255 | -0 | n/a | n/a | n/a | -0.006 | 28 | first edge 9.2 ns after enable starts rising; shortest early period 6.088 ns |
| step_code255 | 255 | 164.255 | 0 | n/a | n/a | n/a | -0.007 | 85 | before 164.255 MHz, after -50 mV 151.407 MHz (-78217 ppm); settled within 5.5 ns |
| xcode_bit0_code255 | 255 | 164.255 | 2 | 0.09 | 0.01 | 0.5 | -0.007 | 89 | gate moves 1.140..1.260 V |
| xcode_bit7_code255 | 255 | 164.252 | -15 | 3.81 | 0.29 | 14.5 | -0.007 | 89 | gate moves 1.188..1.212 V |
| xenable_running_code255 | 255 | 164.243 | -74 | 1.35 | 0.08 | 6.2 | -0.007 | 89 | enable dips to 1.140 V |
| xenable_stopped_code255 | 255 | n/a | n/a | n/a | n/a | n/a | 1.200 | 0 | enable peak 0.060 V |
| xout_ff10_code255 | 255 | 164.241 | -83 | 1.44 | n/a | 8.6 | -0.041 | 20 | 19 periods; shortest 6.084 ns; 0 extra edge(s) at the 0.6 V threshold, clean |
| xout_ff20_code255 | 255 | 164.230 | -152 | 14.12 | n/a | 84.4 | -0.081 | 20 | 19 periods; shortest 6.047 ns; 0 extra edge(s) at the 0.6 V threshold, clean |
| xout_ff30_code255 | 255 | 164.220 | -212 | 27.95 | n/a | 167.3 | -0.120 | 20 | 19 periods; shortest 6.006 ns; 0 extra edge(s) at the 0.6 V threshold, clean |
| xout_ff5_code255 | 255 | 164.248 | -42 | 3.34 | n/a | 20.0 | -0.021 | 20 | 19 periods; shortest 6.078 ns; 0 extra edge(s) at the 0.6 V threshold, clean |

Shift is the mean frequency over the run against the quiet run at the same code; the counter reads that mean. Period jitter is what the ring does cycle to cycle; the 25-period mean jitter is closer to what a reciprocal count over hundreds of periods scatters by. 50 MHz ripple and bounce are square waves with 1 ns edges; the crosstalk aggressor is a full-swing 50 MHz square with 200 ps edges through 20 fF (30 fF onto clk_out), the victim driven through 500 ohm. Every case of a code uses the same maximum time step.
