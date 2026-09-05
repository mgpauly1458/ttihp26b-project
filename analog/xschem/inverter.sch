v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
N 20 -40 20 0 {lab=Y}
N 20 -20 80 -20 {lab=Y}
N 20 -100 80 -100 {lab=VDD}
N 20 -70 80 -70 {lab=VDD}
N 20 30 80 30 {lab=VSS}
N 20 60 80 60 {lab=VSS}
N -20 -70 -80 -70 {lab=A}
N -20 30 -80 30 {lab=A}
N -80 -70 -80 30 {lab=A}
C {devices/lab_pin.sym} 80 -100 0 0 {name=lvdds lab=VDD}
C {devices/lab_pin.sym} 80 -70 0 0 {name=lvddb lab=VDD}
C {devices/lab_pin.sym} 80 -20 0 0 {name=ly lab=Y}
C {devices/lab_pin.sym} 80 30 0 0 {name=lvssb lab=VSS}
C {devices/lab_pin.sym} 80 60 0 0 {name=lvsss lab=VSS}
C {devices/lab_pin.sym} -80 -20 0 1 {name=la lab=A}
C {devices/ipin.sym} -240 -180 0 0 {name=pa lab=A}
C {devices/opin.sym} -240 -150 0 0 {name=py lab=Y}
C {devices/iopin.sym} -240 -120 0 0 {name=pvdd lab=VDD}
C {devices/iopin.sym} -240 -90 0 0 {name=pvss lab=VSS}
C {devices/title.sym} -240 100 0 0 {name=l1 author="Maxwell Pauly"}
C {sg13g2_pr/sg13_lv_pmos.sym} 0 -70 0 0 {name=M1
l=0.13u
w=2.0u
ng=1
m=1
model=sg13_lv_pmos
spiceprefix=X
}
C {sg13g2_pr/sg13_lv_nmos.sym} 0 30 0 0 {name=M2
l=0.13u
w=1.0u
ng=1
m=1
model=sg13_lv_nmos
spiceprefix=X
}
