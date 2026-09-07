v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {current-starved inverter: the ring stage} -200 -260 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 0 -150 0 0 {name=MPS
l=0.5u
w=1u
ng=1
m=1
model=sg13_lv_pmos
spiceprefix=X
}
N 20 -150 80 -150 {}
C {devices/lab_pin.sym} 80 -150 0 0 {name=l1 sig_type=std_logic lab=VPWR}
N 20 -180 20 -200 {}
C {devices/lab_pin.sym} 20 -200 0 0 {name=l2 sig_type=std_logic lab=VPWR}
N -20 -150 -60 -150 {}
C {devices/lab_pin.sym} -60 -150 0 0 {name=l3 sig_type=std_logic lab=vbp}
C {sg13g2_pr/sg13_lv_pmos.sym} 0 -60 0 0 {name=MP
l=0.13u
w=0.5u
ng=1
m=1
model=sg13_lv_pmos
spiceprefix=X
}
N 20 -60 80 -60 {}
C {devices/lab_pin.sym} 80 -60 0 0 {name=l4 sig_type=std_logic lab=VPWR}
N 20 -120 20 -90 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 0 60 0 0 {name=MN
l=0.13u
w=0.3u
ng=1
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 20 60 80 60 {}
C {devices/lab_pin.sym} 80 60 0 0 {name=l5 sig_type=std_logic lab=VGND}
N 20 -30 20 30 {}
N 20 0 80 0 {}
C {devices/lab_pin.sym} 80 0 0 0 {name=l6 sig_type=std_logic lab=out}
C {sg13g2_pr/sg13_lv_nmos.sym} 0 150 0 0 {name=MNS
l=0.5u
w=0.5u
ng=1
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 20 150 80 150 {}
C {devices/lab_pin.sym} 80 150 0 0 {name=l7 sig_type=std_logic lab=VGND}
N 20 90 20 120 {}
N -20 150 -60 150 {}
C {devices/lab_pin.sym} -60 150 0 0 {name=l8 sig_type=std_logic lab=vbn}
N 20 180 20 200 {}
C {devices/lab_pin.sym} 20 200 0 0 {name=l9 sig_type=std_logic lab=VGND}
N -20 -60 -60 -60 {}
N -60 -60 -60 60 {}
N -60 60 -20 60 {}
N -60 0 -100 0 {}
C {devices/lab_pin.sym} -100 0 0 0 {name=l10 sig_type=std_logic lab=in}
C {devices/ipin.sym} -300 -200 0 0 {name=p11 lab=in}
C {devices/opin.sym} -300 -160 0 0 {name=p12 lab=out}
C {devices/ipin.sym} -300 -120 0 0 {name=p13 lab=vbp}
C {devices/iopin.sym} -300 -80 0 0 {name=p14 lab=VPWR}
C {devices/ipin.sym} -300 -40 0 0 {name=p15 lab=vbn}
C {devices/iopin.sym} -300 0 0 0 {name=p16 lab=VGND}
C {devices/title.sym} -300 400 0 0 {name=t1 author="Maxwell Pauly"}
