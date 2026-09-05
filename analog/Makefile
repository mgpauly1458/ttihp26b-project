# Analog tile: schematic -> SPICE -> layout -> DRC -> LVS.
# Everything runs in the IIC-OSIC-TOOLS container via ./run.sh (Docker only).
#
#   make          netlist, simulate, build GDS+LEF, then DRC and LVS
#   make gds      build ../gds/<TOP>.gds and ../lef/<TOP>.lef
#   make drc      KLayout DRC, sg13g2 maximal rule set
#   make lvs      KLayout LVS, tile layout vs the xschem netlist
#   make sim      ngspice VTC + transient
#   make png      render the core layout
#   make xschem / make klayout    open the GUIs

TOP     := tt_um_mgpauly1458_inverter
RUN     := ./run.sh
GUI     := ./gui.sh
PDKTECH := /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
XSCHEM  := xschem -n -s -q --no_x --rcfile /work/analog/xschem/xschemrc

.PHONY: all netlist sim plot gds drc lvs png xschem klayout clean

all: drc lvs

out:
	@mkdir -p out

# Two netlists from the same schematics: a simulation netlist (X-prefix
# subcircuit calls) and an LVS netlist (M-prefix device lines). LVS compares
# extracted devices and cannot use the former.
netlist: out
	$(RUN) bash -lc 'cd /work/analog/xschem && $(XSCHEM) inverter_tb.sch -o /work/analog/out'
	$(RUN) bash -lc 'cd /work/analog/xschem && $(XSCHEM) --tcl "set lvs_netlist 1; set top_subckt 1" $(TOP).sch -o /work/analog/out'

sim: netlist
	$(RUN) bash -lc 'cd /work/analog/out && ngspice -b inverter_tb.spice'

plot: sim
	$(RUN) python3 sim/plot.py

gds: out
	$(RUN) klayout -b -r layout/build_gds.py

png: gds
	$(RUN) klayout -b -z -r layout/render.py

drc: gds
	@rm -rf out/drc && mkdir -p out/drc
	$(RUN) bash -lc 'python3 $(PDKTECH)/drc/run_drc.py --path=/work/gds/$(TOP).gds \
	    --topcell=$(TOP) --run_dir=/work/analog/out/drc --no_density --no_offgrid'

# --disable_tap_extraction keeps the well/substrate ties out of the device list.
lvs: gds netlist
	@rm -rf out/lvs && mkdir -p out/lvs
	$(RUN) bash -lc 'python3 $(PDKTECH)/lvs/run_lvs.py --layout=/work/gds/$(TOP).gds \
	    --netlist=/work/analog/out/$(TOP).spice --topcell=$(TOP) \
	    --run_dir=/work/analog/out/lvs --disable_tap_extraction'

xschem:
	$(GUI) xschem --rcfile /work/analog/xschem/xschemrc /work/analog/xschem/inverter_tb.sch

klayout:
	$(GUI) klayout -e -l $(PDKTECH)/sg13g2.lyp /work/gds/$(TOP).gds

clean:
	rm -rf out
