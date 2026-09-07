v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {current-starved NAND: enable (a) and feedback (b) close the loop} -260 -320 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 0 -240 0 0 {name=MPS0
l=0.5u
w=1u
ng=1
m=1
model=sg13_lv_pmos
spiceprefix=X
}
N 20 -240 80 -240 {}
C {devices/lab_pin.sym} 80 -240 0 0 {name=l1 sig_type=std_logic lab=VPWR}
N 20 -270 20 -290 {}
C {devices/lab_pin.sym} 20 -290 0 0 {name=l2 sig_type=std_logic lab=VPWR}
N -20 -240 -60 -240 {}
C {devices/lab_pin.sym} -60 -240 0 0 {name=l3 sig_type=std_logic lab=vbp}
C {sg13g2_pr/sg13_lv_pmos.sym} -80 -120 0 0 {name=MPA0
l=0.13u
w=0.5u
ng=1
m=1
model=sg13_lv_pmos
spiceprefix=X
}
N -60 -120 0 -120 {}
C {devices/lab_pin.sym} 0 -120 0 0 {name=l4 sig_type=std_logic lab=VPWR}
C {sg13g2_pr/sg13_lv_pmos.sym} 160 -120 0 0 {name=MPB0
l=0.13u
w=0.5u
ng=1
m=1
model=sg13_lv_pmos
spiceprefix=X
}
N 180 -120 240 -120 {}
C {devices/lab_pin.sym} 240 -120 0 0 {name=l5 sig_type=std_logic lab=VPWR}
N 20 -210 20 -170 {}
N 20 -170 -60 -170 {}
N -60 -170 -60 -150 {}
N 20 -170 180 -170 {}
N 180 -170 180 -150 {}
N -60 -90 -60 -60 {}
N -60 -60 180 -60 {}
N 180 -60 180 -90 {}
N 20 -60 20 30 {}
N 20 0 240 0 {}
C {devices/lab_pin.sym} 240 0 0 0 {name=l6 sig_type=std_logic lab=out}
N -100 -120 -140 -120 {}
C {devices/lab_pin.sym} -140 -120 0 0 {name=l7 sig_type=std_logic lab=a}
N 140 -120 110 -120 {}
C {devices/lab_pin.sym} 110 -120 0 0 {name=l8 sig_type=std_logic lab=b}
C {sg13g2_pr/sg13_lv_nmos.sym} 0 60 0 0 {name=MNB0
l=0.13u
w=0.6u
ng=1
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 20 60 80 60 {}
C {devices/lab_pin.sym} 80 60 0 0 {name=l9 sig_type=std_logic lab=VGND}
N -20 60 -60 60 {}
C {devices/lab_pin.sym} -60 60 0 0 {name=l10 sig_type=std_logic lab=b}
C {sg13g2_pr/sg13_lv_nmos.sym} 0 150 0 0 {name=MNA0
l=0.13u
w=0.6u
ng=1
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 20 150 80 150 {}
C {devices/lab_pin.sym} 80 150 0 0 {name=l11 sig_type=std_logic lab=VGND}
N 20 90 20 120 {}
N -20 150 -60 150 {}
C {devices/lab_pin.sym} -60 150 0 0 {name=l12 sig_type=std_logic lab=a}
C {sg13g2_pr/sg13_lv_nmos.sym} 0 240 0 0 {name=MNS0
l=0.5u
w=0.5u
ng=1
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 20 240 80 240 {}
C {devices/lab_pin.sym} 80 240 0 0 {name=l13 sig_type=std_logic lab=VGND}
N 20 180 20 210 {}
N -20 240 -60 240 {}
C {devices/lab_pin.sym} -60 240 0 0 {name=l14 sig_type=std_logic lab=vbn}
N 20 270 20 290 {}
C {devices/lab_pin.sym} 20 290 0 0 {name=l15 sig_type=std_logic lab=VGND}
C {devices/ipin.sym} -300 -260 0 0 {name=p16 lab=a}
C {devices/ipin.sym} -300 -220 0 0 {name=p17 lab=b}
C {devices/opin.sym} -300 -180 0 0 {name=p18 lab=out}
C {devices/ipin.sym} -300 -140 0 0 {name=p19 lab=vbp}
C {devices/iopin.sym} -300 -100 0 0 {name=p20 lab=VPWR}
C {devices/ipin.sym} -300 -60 0 0 {name=p21 lab=vbn}
C {devices/iopin.sym} -300 -20 0 0 {name=p22 lab=VGND}
C {devices/title.sym} -300 400 0 0 {name=t1 author="Maxwell Pauly"}
