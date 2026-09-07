v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
N -30 0 -90 0 {lab=A}
N 50 0 110 0 {lab=Y}
N 0 -30 0 -80 {lab=VPWR}
N 0 30 0 80 {lab=VGND}
C {devices/lab_pin.sym} -90 0 0 1 {name=lin lab=A}
C {devices/lab_pin.sym} 110 0 0 0 {name=lout lab=Y}
C {devices/lab_pin.sym} 0 -80 0 0 {name=lvd lab=VPWR}
C {devices/lab_pin.sym} 0 80 0 2 {name=lvg lab=VGND}
C {devices/ipin.sym} -260 -120 0 0 {name=p0 lab=A}
C {devices/opin.sym} -260 -90 0 0 {name=p1 lab=Y}
C {devices/iopin.sym} -260 -60 0 0 {name=p2 lab=VPWR}
C {devices/iopin.sym} -260 -30 0 0 {name=p3 lab=VGND}
C {devices/title.sym} -260 120 0 0 {name=l1 author="Maxwell Pauly"}
C {inverter.sym} 0 0 0 0 {name=x1}
