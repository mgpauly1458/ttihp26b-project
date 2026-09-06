# Analog flow for this Tiny Tapeout tile.
#
# Two pipelines, and they are different things:
#
#   make design   YOUR pipeline -- does the circuit work and does the layout
#                 match it?  netlist -> simulate -> GDS -> DRC -> LVS
#   make tt       TINY TAPEOUT's pipeline -- will the shuttle accept it?
#                 DRC + LVS + a local stand-in for the GDS prechecks
#   make all      both
#
# Everything runs inside the hpretl/iic-osic-tools container via ./run.sh, so
# Docker is the only thing you need installed. The container already ships the
# ihp-sg13g2 PDK, xschem, ngspice, KLayout, magic, netgen and kpex.
#
# Run `make help` for the full target list.

TOP     := tt_um_mgpauly1458_inverter
TB      := inverter_tb
RUN     := ./run.sh
GUI     := ./gui.sh
PDKTECH := /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
XSCHEM  := xschem -n -s -q --no_x --rcfile /work/analog/xschem/xschemrc

.DEFAULT_GOAL := help
.PHONY: help all design tt netlist sim plot gds drc lvs precheck png \
        xschem klayout shell ci clean

help:
	@echo 'Pipelines'
	@echo '  make design    netlist -> sim -> GDS+LEF -> DRC -> LVS   (is the design right?)'
	@echo '  make tt        DRC -> LVS -> local precheck              (will TT accept it?)'
	@echo '  make all       both of the above'
	@echo
	@echo 'Individual steps'
	@echo '  make netlist   xschem -> SPICE, both the sim and the LVS netlist'
	@echo '  make sim       ngspice DC sweep + transient on $(TB)'
	@echo '  make plot      waveform figure -> ../docs/inverter_sim.png'
	@echo '  make gds       layout -> ../gds/$(TOP).gds and ../lef/$(TOP).lef'
	@echo '  make drc       KLayout DRC, sg13g2 maximal rule set'
	@echo '  make lvs       KLayout LVS, layout vs the xschem netlist'
	@echo '  make precheck  local stand-in for TT'"'"'s GDS prechecks'
	@echo '  make png       render the layout -> ../docs/inverter_layout.png'
	@echo
	@echo 'Interactive'
	@echo '  make xschem    open the testbench in xschem'
	@echo '  make klayout   open the tile layout in KLayout'
	@echo '  make shell     a bash prompt inside the container'
	@echo '  make ci        show the latest GitHub Actions results'
	@echo
	@echo '  make clean     remove out/'

all: design tt

# ============================================================ your pipeline
design: netlist sim gds drc lvs
	@echo '=== design pipeline complete: simulated, DRC clean, LVS matching ==='

out:
	@mkdir -p out

# Two netlists come out of the same schematics and they are NOT interchangeable:
#
#   $(TB).spice   simulation. Devices appear as subcircuit calls,
#                 "XM1 ... sg13_lv_pmos", which is what ngspice wants.
#   $(TOP).spice  LVS. Devices appear as device lines, "MM1 ...", selected by
#                 `set lvs_netlist 1`. LVS compares extracted devices and reads
#                 the X-prefixed form as subcircuit instances, so handing it the
#                 simulation netlist fails with no useful diagnostic.
#
# `set top_subckt 1` wraps the top schematic in .subckt/.ends instead of
# netlisting it as a flat top level.
netlist: out
	$(RUN) bash -lc 'cd /work/analog/xschem && $(XSCHEM) $(TB).sch -o /work/analog/out'
	$(RUN) bash -lc 'cd /work/analog/xschem && $(XSCHEM) --tcl "set lvs_netlist 1; set top_subckt 1" $(TOP).sch -o /work/analog/out'

# DC sweep for the transfer curve plus a transient into a 10fF load. The .control
# block lives in the testbench schematic, so edit it there, not here.
sim: netlist
	$(RUN) bash -lc 'cd /work/analog/out && ngspice -b $(TB).spice'

plot: sim
	$(RUN) python3 sim/plot.py

# Places the PDK PCells, draws the interconnect, and emits the LEF from the same
# constants -- so the LEF can never describe geometry the GDS does not have.
gds: out
	$(RUN) klayout -b -r layout/build_gds.py

png: gds
	$(RUN) klayout -b -z -r layout/render.py

drc: gds
	@rm -rf out/drc && mkdir -p out/drc
	$(RUN) bash -lc 'python3 $(PDKTECH)/drc/run_drc.py --path=/work/gds/$(TOP).gds \
	    --topcell=$(TOP) --run_dir=/work/analog/out/drc --no_density --no_offgrid'

# --disable_tap_extraction keeps the well and substrate ties out of the device
# list. Without it they extract as ntap1/ptap1 resistors with the transistor
# bulks on unnamed nets, which no hand-drawn schematic will ever match.
lvs: gds netlist
	@rm -rf out/lvs && mkdir -p out/lvs
	$(RUN) bash -lc 'python3 $(PDKTECH)/lvs/run_lvs.py --layout=/work/gds/$(TOP).gds \
	    --netlist=/work/analog/out/$(TOP).spice --topcell=$(TOP) \
	    --run_dir=/work/analog/out/lvs --disable_tap_extraction'

# ====================================================== tiny tapeout pipeline
tt: drc lvs precheck
	@echo '=== TT pipeline clear locally -- push and let CI confirm ==='

# Catches the GDS-shaped mistakes without a ~7 minute CI round trip. Not the
# authority: CI runs the real precheck, which checks more than this.
precheck: gds
	$(RUN) python3 checks/tt_precheck.py

ci:
	@gh run list --branch $$(git rev-parse --abbrev-ref HEAD) --limit 5 \
	    --json name,status,conclusion,createdAt \
	    -q '.[] | "\(.name)\t\(.status)\t\(.conclusion // "-")"' || \
	    echo 'gh not available or not authenticated'

# ================================================================ interactive
xschem:
	$(GUI) xschem --rcfile /work/analog/xschem/xschemrc /work/analog/xschem/$(TB).sch

klayout:
	$(GUI) klayout -e -l $(PDKTECH)/sg13g2.lyp /work/gds/$(TOP).gds

shell:
	$(GUI) bash

clean:
	rm -rf out
