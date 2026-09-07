v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {output buffer inverter: the second one is 4x this} -200 -200 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 0 -60 0 0 {name=MBP
l=0.13u
w=0.5u
ng=1
m=1
model=sg13_lv_pmos
spiceprefix=X
}
N 20 -60 80 -60 {}
C {devices/lab_pin.sym} 80 -60 0 0 {name=l1 sig_type=std_logic lab=VPWR}
C {sg13g2_pr/sg13_lv_nmos.sym} 0 60 0 0 {name=MBN
l=0.13u
w=0.3u
ng=1
m=1
model=sg13_lv_nmos
spiceprefix=X
}
N 20 60 80 60 {}
C {devices/lab_pin.sym} 80 60 0 0 {name=l2 sig_type=std_logic lab=VGND}
N 20 -90 20 -110 {}
C {devices/lab_pin.sym} 20 -110 0 0 {name=l3 sig_type=std_logic lab=VPWR}
N 20 90 20 110 {}
C {devices/lab_pin.sym} 20 110 0 0 {name=l4 sig_type=std_logic lab=VGND}
N 20 -30 20 30 {}
N 20 0 80 0 {}
C {devices/lab_pin.sym} 80 0 0 0 {name=l5 sig_type=std_logic lab=out}
N -20 -60 -60 -60 {}
N -60 -60 -60 60 {}
N -60 60 -20 60 {}
N -60 0 -100 0 {}
C {devices/lab_pin.sym} -100 0 0 0 {name=l6 sig_type=std_logic lab=in}
C {devices/ipin.sym} -300 -160 0 0 {name=p7 lab=in}
C {devices/opin.sym} -300 -120 0 0 {name=p8 lab=out}
C {devices/iopin.sym} -300 -80 0 0 {name=p9 lab=VPWR}
C {devices/iopin.sym} -300 -40 0 0 {name=p10 lab=VGND}
C {devices/title.sym} -300 400 0 0 {name=t1 author="Maxwell Pauly"}
