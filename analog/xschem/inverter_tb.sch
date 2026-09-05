v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
N -30 0 -90 0 {lab=A}
N 50 0 200 0 {lab=Y}
N 0 -30 0 -80 {lab=VDD}
N 0 30 0 80 {lab=GND}
N -300 -130 -300 -170 {lab=VDD}
N -300 -70 -300 -40 {lab=GND}
N -300 30 -300 0 {lab=A}
N -300 90 -300 120 {lab=GND}
N 200 0 200 30 {lab=Y}
N 200 90 200 120 {lab=GND}
C {devices/code_shown.sym} -720 -180 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.lib $::env(PDK_ROOT)/$::env(PDK)/libs.tech/ngspice/models/cornerMOSlv.lib mos_tt
"}
C {devices/code_shown.sym} -720 40 0 0 {name=NGSPICE only_toplevel=true
value="
.control
save all
* --- Voltage transfer characteristic ---
dc Vin 0 1.2 1m
let gain = deriv(v(Y))
meas dc vtrip  find v(A) when v(Y)=0.6
meas dc maxgain min gain
write inverter_tb_dc.raw
wrdata inverter_vtc.data v(Y) gain
reset
* --- Switching behaviour into the 10fF load ---
tran 1p 4n
meas tran tphl trig v(A) val=0.6 rise=1 targ v(Y) val=0.6 fall=1
meas tran tplh trig v(A) val=0.6 fall=1 targ v(Y) val=0.6 rise=1
write inverter_tb_tran.raw
wrdata inverter_tran.data v(A) v(Y)
.endc
"}
C {devices/vsource.sym} -300 -100 0 0 {name=Vdd value=1.2}
C {devices/vsource.sym} -300 60 0 0 {name=Vin value="dc 0 pulse(0 1.2 0.5n 50p 50p 1n 2n)"}
C {devices/gnd.sym} -300 -40 0 0 {name=g1 lab=GND}
C {devices/gnd.sym} -300 120 0 0 {name=g2 lab=GND}
C {devices/gnd.sym} 0 80 0 0 {name=g3 lab=GND}
C {devices/gnd.sym} 200 120 0 0 {name=g4 lab=GND}
C {devices/lab_pin.sym} -300 -170 0 0 {name=lv lab=VDD}
C {devices/lab_pin.sym} -300 0 0 0 {name=li lab=A}
C {devices/lab_pin.sym} 0 -80 0 0 {name=lv2 lab=VDD}
C {devices/lab_pin.sym} -90 0 0 1 {name=la lab=A}
C {devices/lab_pin.sym} 130 0 0 0 {name=ly lab=Y}
C {devices/capa.sym} 200 60 0 0 {name=CL value=10f}
C {devices/title.sym} -720 200 0 0 {name=l1 author="Maxwell Pauly"}
C {inverter.sym} 0 0 0 0 {name=x1}
