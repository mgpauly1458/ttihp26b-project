v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
N -30 0 -90 0 {lab=ua[1]}
N 50 0 110 0 {lab=ua[0]}
N 0 -30 0 -80 {lab=VDPWR}
N 0 30 0 80 {lab=VGND}
C {devices/lab_pin.sym} -90 0 0 1 {name=lin lab=ua[1]}
C {devices/lab_pin.sym} 110 0 0 0 {name=lout lab=ua[0]}
C {devices/lab_pin.sym} 0 -80 0 0 {name=lvd lab=VDPWR}
C {devices/lab_pin.sym} 0 80 0 2 {name=lvg lab=VGND}
C {devices/iopin.sym} -260 -120 0 0 {name=p0 lab=ua[0]}
C {devices/iopin.sym} -260 -90 0 0 {name=p1 lab=ua[1]}
C {devices/iopin.sym} -260 -60 0 0 {name=p2 lab=VDPWR}
C {devices/iopin.sym} -260 -30 0 0 {name=p3 lab=VGND}
C {devices/title.sym} -260 120 0 0 {name=l1 author="Maxwell Pauly"}
C {inverter.sym} 0 0 0 0 {name=x1}
