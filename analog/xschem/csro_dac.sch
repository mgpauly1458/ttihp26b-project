v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {binary-weighted current DAC: 2^k unit fingers (0.15u/8u) per bit, gate driven by the code bit; +2 always-on units} -100 -200 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 0 0 0 0 {name=D0
l=8u
w=0.15u
ng=1
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 20 0 80 0 {}
C {devices/lab_pin.sym} 80 0 0 0 {name=l1 sig_type=std_logic lab=VGND}
N -20 0 -50 0 {}
C {devices/lab_pin.sym} -50 0 0 0 {name=l2 sig_type=std_logic lab=code[0]}
N 20 -30 20 -80 {}
N 20 30 20 80 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 220 0 0 0 {name=D1
l=8u
w=0.3u
ng=2
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 240 0 300 0 {}
C {devices/lab_pin.sym} 300 0 0 0 {name=l3 sig_type=std_logic lab=VGND}
N 200 0 170 0 {}
C {devices/lab_pin.sym} 170 0 0 0 {name=l4 sig_type=std_logic lab=code[1]}
N 240 -30 240 -80 {}
N 240 30 240 80 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 440 0 0 0 {name=D2
l=8u
w=0.6u
ng=4
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 460 0 520 0 {}
C {devices/lab_pin.sym} 520 0 0 0 {name=l5 sig_type=std_logic lab=VGND}
N 420 0 390 0 {}
C {devices/lab_pin.sym} 390 0 0 0 {name=l6 sig_type=std_logic lab=code[2]}
N 460 -30 460 -80 {}
N 460 30 460 80 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 660 0 0 0 {name=D3
l=8u
w=1.2u
ng=8
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 680 0 740 0 {}
C {devices/lab_pin.sym} 740 0 0 0 {name=l7 sig_type=std_logic lab=VGND}
N 640 0 610 0 {}
C {devices/lab_pin.sym} 610 0 0 0 {name=l8 sig_type=std_logic lab=code[3]}
N 680 -30 680 -80 {}
N 680 30 680 80 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 880 0 0 0 {name=D4
l=8u
w=2.4u
ng=16
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 900 0 960 0 {}
C {devices/lab_pin.sym} 960 0 0 0 {name=l9 sig_type=std_logic lab=VGND}
N 860 0 830 0 {}
C {devices/lab_pin.sym} 830 0 0 0 {name=l10 sig_type=std_logic lab=code[4]}
N 900 -30 900 -80 {}
N 900 30 900 80 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 1100 0 0 0 {name=D5
l=8u
w=4.8u
ng=32
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 1120 0 1180 0 {}
C {devices/lab_pin.sym} 1180 0 0 0 {name=l11 sig_type=std_logic lab=VGND}
N 1080 0 1050 0 {}
C {devices/lab_pin.sym} 1050 0 0 0 {name=l12 sig_type=std_logic lab=code[5]}
N 1120 -30 1120 -80 {}
N 1120 30 1120 80 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 1320 0 0 0 {name=D6
l=8u
w=9.6u
ng=64
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 1340 0 1400 0 {}
C {devices/lab_pin.sym} 1400 0 0 0 {name=l13 sig_type=std_logic lab=VGND}
N 1300 0 1270 0 {}
C {devices/lab_pin.sym} 1270 0 0 0 {name=l14 sig_type=std_logic lab=code[6]}
N 1340 -30 1340 -80 {}
N 1340 30 1340 80 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 1540 0 0 0 {name=D7
l=8u
w=19.2u
ng=128
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 1560 0 1620 0 {}
C {devices/lab_pin.sym} 1620 0 0 0 {name=l15 sig_type=std_logic lab=VGND}
N 1520 0 1490 0 {}
C {devices/lab_pin.sym} 1490 0 0 0 {name=l16 sig_type=std_logic lab=code[7]}
N 1560 -30 1560 -80 {}
N 1560 30 1560 80 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 1760 0 0 0 {name=DON
l=8u
w=0.3u
ng=2
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 1780 0 1840 0 {}
C {devices/lab_pin.sym} 1840 0 0 0 {name=l17 sig_type=std_logic lab=VGND}
N 1740 0 1710 0 {}
C {devices/lab_pin.sym} 1710 0 0 0 {name=l18 sig_type=std_logic lab=VPWR}
N 1780 -30 1780 -80 {}
N 1780 30 1780 80 {}
N 20 -80 1840 -80 {}
C {devices/lab_pin.sym} 1840 -80 0 0 {name=l19 sig_type=std_logic lab=vbp}
N 20 80 1840 80 {}
C {devices/lab_pin.sym} 1840 80 0 0 {name=l20 sig_type=std_logic lab=VGND}
C {devices/ipin.sym} -300 -160 0 0 {name=p21 lab=code[0]}
C {devices/ipin.sym} -300 -120 0 0 {name=p22 lab=code[1]}
C {devices/ipin.sym} -300 -80 0 0 {name=p23 lab=code[2]}
C {devices/ipin.sym} -300 -40 0 0 {name=p24 lab=code[3]}
C {devices/ipin.sym} -300 0 0 0 {name=p25 lab=code[4]}
C {devices/ipin.sym} -300 40 0 0 {name=p26 lab=code[5]}
C {devices/ipin.sym} -300 80 0 0 {name=p27 lab=code[6]}
C {devices/ipin.sym} -300 120 0 0 {name=p28 lab=code[7]}
C {devices/opin.sym} -300 160 0 0 {name=p29 lab=vbp}
C {devices/iopin.sym} -300 200 0 0 {name=p30 lab=VPWR}
C {devices/iopin.sym} -300 240 0 0 {name=p31 lab=VGND}
C {devices/title.sym} -300 400 0 0 {name=t1 author="Maxwell Pauly"}
