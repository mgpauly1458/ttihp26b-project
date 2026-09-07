v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {tt_analog_ring: current-starved ring oscillator with an 8-bit current DAC} -560 -620 0 0 0.5 0.5 {}
C {devices/ipin.sym} -760 -560 0 0 {name=p1 lab=code[0]}
C {devices/ipin.sym} -760 -520 0 0 {name=p2 lab=code[1]}
C {devices/ipin.sym} -760 -480 0 0 {name=p3 lab=code[2]}
C {devices/ipin.sym} -760 -440 0 0 {name=p4 lab=code[3]}
C {devices/ipin.sym} -760 -400 0 0 {name=p5 lab=code[4]}
C {devices/ipin.sym} -760 -360 0 0 {name=p6 lab=code[5]}
C {devices/ipin.sym} -760 -320 0 0 {name=p7 lab=code[6]}
C {devices/ipin.sym} -760 -280 0 0 {name=p8 lab=code[7]}
C {devices/ipin.sym} -760 -240 0 0 {name=p9 lab=enable}
C {devices/opin.sym} -760 -200 0 0 {name=p10 lab=clk_out}
C {devices/iopin.sym} -760 -160 0 0 {name=p11 lab=VPWR}
C {devices/iopin.sym} -760 -120 0 0 {name=p12 lab=VGND}
C {csro_dac.sym} -400 -300 0 0 {name=XDAC}
N -500 -380 -540 -380 {}
C {devices/lab_pin.sym} -540 -380 0 0 {name=l13 sig_type=std_logic lab=code[0]}
N -500 -360 -540 -360 {}
C {devices/lab_pin.sym} -540 -360 0 0 {name=l14 sig_type=std_logic lab=code[1]}
N -500 -340 -540 -340 {}
C {devices/lab_pin.sym} -540 -340 0 0 {name=l15 sig_type=std_logic lab=code[2]}
N -500 -320 -540 -320 {}
C {devices/lab_pin.sym} -540 -320 0 0 {name=l16 sig_type=std_logic lab=code[3]}
N -500 -300 -540 -300 {}
C {devices/lab_pin.sym} -540 -300 0 0 {name=l17 sig_type=std_logic lab=code[4]}
N -500 -280 -540 -280 {}
C {devices/lab_pin.sym} -540 -280 0 0 {name=l18 sig_type=std_logic lab=code[5]}
N -500 -260 -540 -260 {}
C {devices/lab_pin.sym} -540 -260 0 0 {name=l19 sig_type=std_logic lab=code[6]}
N -500 -240 -540 -240 {}
C {devices/lab_pin.sym} -540 -240 0 0 {name=l20 sig_type=std_logic lab=code[7]}
C {devices/lab_pin.sym} -400 -420 0 0 {name=l21 sig_type=std_logic lab=VPWR}
C {devices/lab_pin.sym} -400 -180 0 0 {name=l22 sig_type=std_logic lab=VGND}
N -300 -300 -240 -300 {}
C {sg13g2_pr/sg13_lv_pmos.sym} -200 -300 0 0 {name=MPD
l=0.5u
w=48u
ng=24
m=1
model=sg13_lv_pmos
spiceprefix=X
}
N -180 -300 -120 -300 {}
C {devices/lab_pin.sym} -120 -300 0 0 {name=l23 sig_type=std_logic lab=VPWR}
N -180 -330 -180 -360 {}
C {devices/lab_pin.sym} -180 -360 0 0 {name=l24 sig_type=std_logic lab=VPWR}
N -180 -270 -180 -240 {}
N -180 -240 -240 -240 {}
N -240 -240 -240 -300 {}
N -240 -300 -220 -300 {}
N -240 -240 -240 -210 {}
C {devices/lab_pin.sym} -240 -210 0 0 {name=l25 sig_type=std_logic lab=vbp}
T {vbp = I_dac into the diode; each stage's PMOS starve is 1/48 of it} -140 -370 0 0 0.3 0.3 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 40 -300 0 0 {name=MPM
l=0.5u
w=1u
ng=1
m=1
model=sg13_lv_pmos
spiceprefix=X
}
N 60 -300 120 -300 {}
C {devices/lab_pin.sym} 120 -300 0 0 {name=l26 sig_type=std_logic lab=VPWR}
N 20 -300 -20 -300 {}
C {devices/lab_pin.sym} -20 -300 0 0 {name=l27 sig_type=std_logic lab=vbp}
N 60 -330 60 -360 {}
C {devices/lab_pin.sym} 60 -360 0 0 {name=l28 sig_type=std_logic lab=VPWR}
C {sg13g2_pr/sg13_lv_nmos.sym} 40 -180 0 0 {name=MND
l=0.5u
w=0.5u
ng=1
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 60 -180 120 -180 {}
C {devices/lab_pin.sym} 120 -180 0 0 {name=l29 sig_type=std_logic lab=VGND}
N 60 -270 60 -210 {}
N 60 -240 0 -240 {}
N 0 -240 0 -180 {}
N 0 -180 20 -180 {}
N 0 -240 -40 -240 {}
C {devices/lab_pin.sym} -40 -240 0 0 {name=l30 sig_type=std_logic lab=vbn}
N 60 -150 60 -120 {}
C {devices/lab_pin.sym} 60 -120 0 0 {name=l31 sig_type=std_logic lab=VGND}
T {vbn: MPM copies the stage current into the diode MND} 100 -200 0 0 0.3 0.3 {}
C {csro_nand.sym} -400 260 0 0 {name=XNAND}
N -470 240 -530 240 {}
C {devices/lab_pin.sym} -530 240 0 0 {name=l32 sig_type=std_logic lab=enable}
C {devices/lab_pin.sym} -420 200 0 0 {name=l33 sig_type=std_logic lab=vbp}
C {devices/lab_pin.sym} -380 200 0 0 {name=l34 sig_type=std_logic lab=VPWR}
C {devices/lab_pin.sym} -420 320 0 0 {name=l35 sig_type=std_logic lab=vbn}
C {devices/lab_pin.sym} -380 320 0 0 {name=l36 sig_type=std_logic lab=VGND}
C {csro_stage.sym} -200 260 0 0 {name=X1}
N -330 260 -270 260 {lab=s0}
C {devices/lab_pin.sym} -220 200 0 0 {name=l37 sig_type=std_logic lab=vbp}
C {devices/lab_pin.sym} -180 200 0 0 {name=l38 sig_type=std_logic lab=VPWR}
C {devices/lab_pin.sym} -220 320 0 0 {name=l39 sig_type=std_logic lab=vbn}
C {devices/lab_pin.sym} -180 320 0 0 {name=l40 sig_type=std_logic lab=VGND}
C {csro_stage.sym} 0 260 0 0 {name=X2}
N -130 260 -70 260 {lab=s1}
C {devices/lab_pin.sym} -20 200 0 0 {name=l41 sig_type=std_logic lab=vbp}
C {devices/lab_pin.sym} 20 200 0 0 {name=l42 sig_type=std_logic lab=VPWR}
C {devices/lab_pin.sym} -20 320 0 0 {name=l43 sig_type=std_logic lab=vbn}
C {devices/lab_pin.sym} 20 320 0 0 {name=l44 sig_type=std_logic lab=VGND}
C {csro_stage.sym} 200 260 0 0 {name=X3}
N 70 260 130 260 {lab=s2}
C {devices/lab_pin.sym} 180 200 0 0 {name=l45 sig_type=std_logic lab=vbp}
C {devices/lab_pin.sym} 220 200 0 0 {name=l46 sig_type=std_logic lab=VPWR}
C {devices/lab_pin.sym} 180 320 0 0 {name=l47 sig_type=std_logic lab=vbn}
C {devices/lab_pin.sym} 220 320 0 0 {name=l48 sig_type=std_logic lab=VGND}
C {csro_stage.sym} 400 260 0 0 {name=X4}
N 270 260 330 260 {lab=s3}
C {devices/lab_pin.sym} 380 200 0 0 {name=l49 sig_type=std_logic lab=vbp}
C {devices/lab_pin.sym} 420 200 0 0 {name=l50 sig_type=std_logic lab=VPWR}
C {devices/lab_pin.sym} 380 320 0 0 {name=l51 sig_type=std_logic lab=vbn}
C {devices/lab_pin.sym} 420 320 0 0 {name=l52 sig_type=std_logic lab=VGND}
C {csro_stage.sym} 600 260 0 0 {name=X5}
N 470 260 530 260 {lab=s4}
C {devices/lab_pin.sym} 580 200 0 0 {name=l53 sig_type=std_logic lab=vbp}
C {devices/lab_pin.sym} 620 200 0 0 {name=l54 sig_type=std_logic lab=VPWR}
C {devices/lab_pin.sym} 580 320 0 0 {name=l55 sig_type=std_logic lab=vbn}
C {devices/lab_pin.sym} 620 320 0 0 {name=l56 sig_type=std_logic lab=VGND}
C {csro_stage.sym} 800 260 0 0 {name=X6}
N 670 260 730 260 {lab=s5}
C {devices/lab_pin.sym} 780 200 0 0 {name=l57 sig_type=std_logic lab=vbp}
C {devices/lab_pin.sym} 820 200 0 0 {name=l58 sig_type=std_logic lab=VPWR}
C {devices/lab_pin.sym} 780 320 0 0 {name=l59 sig_type=std_logic lab=vbn}
C {devices/lab_pin.sym} 820 320 0 0 {name=l60 sig_type=std_logic lab=VGND}
C {csro_stage.sym} 1000 260 0 0 {name=X7}
N 870 260 930 260 {lab=s6}
C {devices/lab_pin.sym} 980 200 0 0 {name=l61 sig_type=std_logic lab=vbp}
C {devices/lab_pin.sym} 1020 200 0 0 {name=l62 sig_type=std_logic lab=VPWR}
C {devices/lab_pin.sym} 980 320 0 0 {name=l63 sig_type=std_logic lab=vbn}
C {devices/lab_pin.sym} 1020 320 0 0 {name=l64 sig_type=std_logic lab=VGND}
C {csro_stage.sym} 1200 260 0 0 {name=X8}
N 1070 260 1130 260 {lab=s7}
C {devices/lab_pin.sym} 1180 200 0 0 {name=l65 sig_type=std_logic lab=vbp}
C {devices/lab_pin.sym} 1220 200 0 0 {name=l66 sig_type=std_logic lab=VPWR}
C {devices/lab_pin.sym} 1180 320 0 0 {name=l67 sig_type=std_logic lab=vbn}
C {devices/lab_pin.sym} 1220 320 0 0 {name=l68 sig_type=std_logic lab=VGND}
C {csro_stage.sym} 1400 260 0 0 {name=X9}
N 1270 260 1330 260 {lab=s8}
C {devices/lab_pin.sym} 1380 200 0 0 {name=l69 sig_type=std_logic lab=vbp}
C {devices/lab_pin.sym} 1420 200 0 0 {name=l70 sig_type=std_logic lab=VPWR}
C {devices/lab_pin.sym} 1380 320 0 0 {name=l71 sig_type=std_logic lab=vbn}
C {devices/lab_pin.sym} 1420 320 0 0 {name=l72 sig_type=std_logic lab=VGND}
C {csro_stage.sym} 1600 260 0 0 {name=X10}
N 1470 260 1530 260 {lab=s9}
C {devices/lab_pin.sym} 1580 200 0 0 {name=l73 sig_type=std_logic lab=vbp}
C {devices/lab_pin.sym} 1620 200 0 0 {name=l74 sig_type=std_logic lab=VPWR}
C {devices/lab_pin.sym} 1580 320 0 0 {name=l75 sig_type=std_logic lab=vbn}
C {devices/lab_pin.sym} 1620 320 0 0 {name=l76 sig_type=std_logic lab=VGND}
N 1670 260 1700 260 {lab=s10}
N 1700 260 1700 380 {lab=s10}
N 1700 380 -510 380 {lab=s10}
N -510 380 -510 280 {lab=s10}
N -510 280 -470 280 {lab=s10}
C {devices/lab_pin.sym} 1700 320 0 0 {name=l77 sig_type=std_logic lab=s10}
C {csro_inv.sym} 1820 120 0 0 {name=XB1}
N 1700 260 1700 120 {}
N 1700 120 1760 120 {}
N 1880 120 1920 120 {lab=b1}
N 1920 120 1920 60 {}
N 1920 60 1960 60 {}
N 1920 120 1920 180 {}
N 1920 180 1960 180 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 1980 60 0 0 {name=MBP2
l=0.13u
w=2u
ng=1
m=1
model=sg13_lv_pmos
spiceprefix=X
}
N 2000 60 2060 60 {}
C {devices/lab_pin.sym} 2060 60 0 0 {name=l78 sig_type=std_logic lab=VPWR}
C {sg13g2_pr/sg13_lv_nmos.sym} 1980 180 0 0 {name=MBN2
l=0.13u
w=1u
ng=1
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 2000 180 2060 180 {}
C {devices/lab_pin.sym} 2060 180 0 0 {name=l79 sig_type=std_logic lab=VGND}
N 2000 30 2000 10 {}
C {devices/lab_pin.sym} 2000 10 0 0 {name=l80 sig_type=std_logic lab=VPWR}
N 2000 210 2000 230 {}
C {devices/lab_pin.sym} 2000 230 0 0 {name=l81 sig_type=std_logic lab=VGND}
N 2000 90 2000 150 {}
N 2000 120 2060 120 {}
C {devices/lab_pin.sym} 2060 120 0 0 {name=l82 sig_type=std_logic lab=clk_out}
C {devices/lab_pin.sym} 1820 70 0 0 {name=l83 sig_type=std_logic lab=VPWR}
C {devices/lab_pin.sym} 1820 170 0 0 {name=l84 sig_type=std_logic lab=VGND}
C {devices/title.sym} -300 400 0 0 {name=t1 author="Maxwell Pauly"}
