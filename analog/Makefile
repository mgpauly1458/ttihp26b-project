# Tile assembly for this Tiny Tapeout mixed-signal project.
#
# This directory owns the analog half AND the merge. The digital half is built
# next door in ../digital (LibreLane, RTL -> GDS) and arrives here as a macro
# GDS; `make gds` reads it and drops it into the tile. The dependency is wired
# up, so `make` here builds the digital half first if it is missing -- but it
# does NOT rebuild it when the RTL changes. Run `make macro` after editing
# ../src/ms_hello.v.
#
# Every step is a separate target that does exactly one thing, and only when its
# inputs have actually changed. `make lvs` will not silently re-run the layout
# build; if the GDS is already current it just runs LVS.
#
# Run `make help` for the list, or `make -n <target>` to see what a step would
# do without doing it.
#
# Everything runs inside the hpretl/iic-osic-tools container via ./run.sh, so
# Docker is the only host dependency. The image ships the ihp-sg13g2 PDK,
# xschem, ngspice, KLayout, magic, netgen and kpex.

TOP     := tt_um_mgpauly1458_inverter
TB      := inverter_tb
RUN     := ./run.sh
GUI     := ./gui.sh
PDKTECH := /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
XSCHEM  := xschem -n -s -q --no_x --rcfile /work/analog/xschem/xschemrc
MACRO   := ms_hello

# --------------------------------------------------------------- artefacts
GDS       := ../gds/$(TOP).gds
LEF       := ../lef/$(TOP).lef
SIM_NL    := out/$(TB).spice
LVS_NL    := out/$(TOP).spice
TILE_NL   := out/$(TOP)_tile.spice
MACRO_GDS := ../digital/out/$(MACRO).gds
SIM_DATA  := out/inverter_vtc.data
SIM_PNG   := ../docs/inverter_sim.png
LAYOUT_PNG:= ../docs/tile_layout.png
LAYOUT_PNGS:= $(LAYOUT_PNG) ../docs/inverter_layout.png ../docs/digital_layout.png
DRC_STAMP := out/drc/.passed
LVS_STAMP := out/lvs/.passed
PRE_STAMP := out/.precheck-passed

# ----------------------------------------------------------------- sources
SCH_CELL  := xschem/inverter.sch xschem/inverter.sym xschem/xschemrc
SCH_TB    := xschem/$(TB).sch $(SCH_CELL)
SCH_TOP   := xschem/$(TOP).sch $(SCH_CELL)
LAYOUT_SRC:= layout/build_gds.py tech/tt_analog_1x2.def $(MACRO_GDS)
CHECK_SRC := checks/tt_precheck.py checks/tt_valid_layers.txt ../info.yaml

.DEFAULT_GOAL := help
.PHONY: help macro netlist netlist-sim netlist-lvs netlist-tile sim plot gds \
        lef drc lvs precheck png design tt all xschem klayout shell ci clean \
        distclean

# ==================================================================== help
help:
	@echo 'Steps (each does one thing, and only if its inputs changed)'
	@echo '  make netlist-sim   xschem -> out/$(TB).spice        (subckt calls, for ngspice)'
	@echo '  make netlist-lvs   xschem -> out/$(TOP).spice  (device lines, for LVS)'
	@echo '  make netlist       both of the above'
	@echo '  make netlist-tile  whole-tile LVS reference: analog + digital'
	@echo '  make macro         build the digital half in ../digital (LibreLane)'
	@echo '  make sim           ngspice DC sweep + transient  -> out/*.data, out/*.raw'
	@echo '  make plot          waveforms                     -> $(SIM_PNG)'
	@echo '  make gds           analog + digital macro -> $(GDS) + $(LEF)'
	@echo '  make png           layout renders                -> ../docs/*_layout.png'
	@echo '  make drc           KLayout DRC, sg13g2 maximal rule set'
	@echo '  make lvs           KLayout LVS, whole tile vs the tile netlist'
	@echo '  make precheck      local stand-in for TT'"'"'s GDS prechecks'
	@echo
	@echo 'Pipelines (just chain the steps above)'
	@echo '  make design        netlist sim gds drc lvs   -- is the circuit right?'
	@echo '  make tt            gds drc lvs precheck      -- will TT accept it?'
	@echo '  make all           both'
	@echo
	@echo 'Interactive'
	@echo '  make xschem        open the testbench in xschem'
	@echo '  make klayout       open the tile layout in KLayout'
	@echo '  make shell         bash prompt inside the container'
	@echo '  make ci            latest GitHub Actions results for this branch'
	@echo
	@echo '  make clean         remove out/ (keeps gds/, lef/, docs/)'
	@echo '  make distclean     also remove the generated GDS, LEF and PNGs'
	@echo
	@echo 'Force a step to re-run even if up to date:  make -B <target>'

out:
	@mkdir -p out

# ================================================================ netlists
# Two netlists come out of the same schematics and they are NOT interchangeable.
#
#   $(SIM_NL)  simulation. Devices are subcircuit calls, "XM1 ... sg13_lv_pmos",
#              which is what ngspice wants.
#   $(LVS_NL)  LVS. Devices are device lines, "MM1 ...", selected by
#              `set lvs_netlist 1`. LVS compares extracted devices and reads the
#              X-prefixed form as subcircuit instances, so handing it the
#              simulation netlist fails with no useful diagnostic.
#
# `set top_subckt 1` wraps the top schematic in .subckt/.ends rather than
# netlisting it as a flat top level.
netlist-sim: $(SIM_NL)
$(SIM_NL): $(SCH_TB) | out
	$(RUN) bash -lc 'cd /work/analog/xschem && $(XSCHEM) $(TB).sch -o /work/analog/out'

netlist-lvs: $(LVS_NL)
$(LVS_NL): $(SCH_TOP) | out
	$(RUN) bash -lc 'cd /work/analog/xschem && $(XSCHEM) --tcl "set lvs_netlist 1; set top_subckt 1" $(TOP).sch -o /work/analog/out'

# The reference netlist for the WHOLE tile: the xschem inverter and the
# LibreLane macro, reconciled against the PDK's transistor-level standard cells.
# See checks/build_tile_netlist.py for why none of the three sources is usable
# as it stands.
netlist-tile: $(TILE_NL)
$(TILE_NL): $(LVS_NL) $(MACRO_GDS) checks/build_tile_netlist.py | out
	$(RUN) python3 checks/build_tile_netlist.py

netlist: netlist-sim netlist-lvs netlist-tile

# ============================================================== simulation
# DC sweep for the transfer curve plus a transient into a 10fF load. The
# .control block lives in the testbench schematic -- edit it there, not here.
sim: $(SIM_DATA)
$(SIM_DATA): $(SIM_NL)
	$(RUN) bash -lc 'cd /work/analog/out && ngspice -b $(TB).spice'

plot: $(SIM_PNG)
$(SIM_PNG): $(SIM_DATA) sim/plot.py
	$(RUN) python3 sim/plot.py

# ================================================================== layout
# The digital half. Delegated rather than duplicated: ../digital owns the
# LibreLane config and stages the macro into ../digital/out. `macro` always
# re-hardens; the file rule only fires when the macro is missing, so an
# unrelated `make` here never spends a minute in LibreLane.
macro:
	$(MAKE) -C ../digital

$(MACRO_GDS):
	$(MAKE) -C ../digital

# One script places the analog PCells, merges in the digital macro, routes
# between the two blocks and the tile interface, and emits the LEF from the same
# constants -- so the LEF can never describe geometry the GDS lacks. That is
# also why there is no separate `make lef`.
gds: $(GDS)
$(GDS): $(LAYOUT_SRC) | out
	$(RUN) klayout -b -r layout/build_gds.py

lef: $(LEF)
$(LEF): $(GDS) ;

# render.py writes three views in one pass; the tile image stands in for all of
# them as the make target.
png: $(LAYOUT_PNG)
$(LAYOUT_PNG): $(GDS) layout/render.py
	$(RUN) klayout -b -z -r layout/render.py

# ================================================================= signoff
drc: $(DRC_STAMP)
$(DRC_STAMP): $(GDS)
	@rm -rf out/drc && mkdir -p out/drc
	$(RUN) bash -lc 'python3 $(PDKTECH)/drc/run_drc.py --path=/work/gds/$(TOP).gds \
	    --topcell=$(TOP) --run_dir=/work/analog/out/drc --no_density --no_offgrid'
	@touch $@

# --disable_tap_extraction keeps the well and substrate ties out of the device
# list. Without it they extract as ntap1/ptap1 resistors with the transistor
# bulks on unnamed nets, which no hand-drawn schematic will ever match.
lvs: $(LVS_STAMP)
$(LVS_STAMP): $(GDS) $(TILE_NL)
	@rm -rf out/lvs && mkdir -p out/lvs
	$(RUN) bash -lc 'python3 $(PDKTECH)/lvs/run_lvs.py --layout=/work/gds/$(TOP).gds \
	    --netlist=/work/analog/$(TILE_NL) --topcell=$(TOP) \
	    --run_dir=/work/analog/out/lvs --disable_tap_extraction'
	@touch $@

# Catches the GDS-shaped mistakes without a ~7 minute CI round trip. Not the
# authority: CI runs the real precheck, which checks more than this.
precheck: $(PRE_STAMP)
$(PRE_STAMP): $(GDS) $(LEF) $(CHECK_SRC)
	$(RUN) python3 checks/tt_precheck.py
	@touch $@

# =============================================================== pipelines
design: netlist sim gds drc lvs
	@echo '=== design pipeline complete: simulated, DRC clean, LVS matching ==='

tt: gds drc lvs precheck
	@echo '=== TT pipeline clear locally -- push and let CI confirm ==='

all: design tt

# ============================================================= interactive
xschem:
	$(GUI) xschem --rcfile /work/analog/xschem/xschemrc /work/analog/xschem/$(TB).sch

klayout:
	$(GUI) klayout -e -l $(PDKTECH)/sg13g2.lyp /work/gds/$(TOP).gds

shell:
	$(GUI) bash

ci:
	@gh run list --branch $$(git rev-parse --abbrev-ref HEAD) --limit 5 \
	    --json name,status,conclusion \
	    -q '.[] | "\(.name)\t\(.status)\t\(.conclusion // "-")"' || \
	    echo 'gh not available or not authenticated'

clean:
	rm -rf out

distclean: clean
	rm -f $(GDS) $(LEF) $(SIM_PNG) $(LAYOUT_PNGS)
