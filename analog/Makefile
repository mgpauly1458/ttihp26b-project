# Analog / mixed-signal flow, one block at a time.
#
# Every step takes a CELL, so the same commands work for any schematic, layout
# or block you add later:
#
#   make sim   CELL=inverter          simulate xschem/inverter_tb.sch
#   make gds   CELL=someblock         build layout/build_someblock.py
#   make drc   CELL=someblock         DRC that block's GDS
#   make lvs   CELL=someblock         LVS it against its schematic
#
# CELL defaults to the Tiny Tapeout top module read out of ../info.yaml, so a
# bare `make drc` still means "the submission tile".
#
# `make list` shows what is available. `make help` explains the variables.
#
# Everything runs in the hpretl/iic-osic-tools container via ./run.sh, so Docker
# is the only host dependency.

# ================================================================ conventions
#
#   xschem/<cell>.sch         schematic for <cell>
#   xschem/<cell>_tb.sch      its testbench
#   layout/build_<cell>.py    layout generator, writes out/<cell>.gds
#   out/<cell>.spice          netlist for LVS      (device lines, MM1 ...)
#   out/<cell>_tb.sim.spice   netlist for ngspice  (subckt calls, XM1 ...)
#   out/<cell>/drc, /lvs      per-cell run directories, so blocks never collide
#
# The two netlist formats are NOT interchangeable; see the netlist rules below.

# The analog macro the digital tile imports. It is the default CELL because it
# is the only block this directory is responsible for now: the tile itself is
# built by LibreLane from the repository root (see ../Makefile).
MACRO   ?= tt_analog_inverter

CELL    ?= $(MACRO)
TB      ?= $(CELL)_tb
PLOT    ?= sim/plot.py

RUN     := ./run.sh
GUI     := ./gui.sh
PDKTECH := /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
XSCHEM  := xschem -n -s -q --no_x --rcfile /work/analog/xschem/xschemrc

# ------------------------------------------------------- per-cell file paths
# The macro is the one cell that is special: its GDS and LEF are COMMITTED,
# under macro/, because CI has neither KLayout nor the PDK's PCell library and
# LibreLane has to find them in the repository. Everything else is scratch and
# lives in out/.
ifeq ($(CELL),$(MACRO))
  GDS      ?= macro/$(MACRO).gds
  LEF      ?= macro/$(MACRO).lef
  LIB      ?= lib/$(MACRO).lib
else
  GDS      ?= out/$(CELL).gds
  NETLIST  ?= out/$(CELL).spice
endif
BUILD    ?= layout/build_$(CELL).py
NETLIST  ?= out/$(CELL).spice

SIM_NL   := out/$(TB).sim.spice
CELLDIR  := out/$(CELL)
DRC_OK   := $(CELLDIR)/.drc-passed
LVS_OK   := $(CELLDIR)/.lvs-passed

# Schematics are cheap to re-netlist and hard to dependency-track properly
# (xschem pulls in symbols transitively), so every .sch in the directory is a
# prerequisite of every netlist. Over-triggering costs a second; under-
# triggering silently netlists a stale hierarchy.
SCH_ALL  := $(wildcard xschem/*.sch) $(wildcard xschem/*.sym) xschem/xschemrc

.DEFAULT_GOAL := help
.PHONY: help list netlist netlist-lvs netlist-sim sim plot gds lef lib drc lvs \
        png design macro all xschem klayout shell ci \
        glb gds3d-tech d25 view3d clean distclean

# ======================================================================= help
help:
	@echo 'Usage:  make <target> [CELL=<name>] [TB=<name>] [GDS=<path>] [NETLIST=<path>]'
	@echo
	@echo 'Variables'
	@echo '  CELL     block to act on           (default: $(MACRO))'
	@echo '  TB       testbench schematic       (default: <CELL>_tb)'
	@echo '  GDS      layout to check           (default: $(GDS))'
	@echo '  NETLIST  LVS reference netlist     (default: $(NETLIST))'
	@echo '  BUILD    layout generator          (default: $(BUILD))'
	@echo '  PLOT     plotting script           (default: $(PLOT))'
	@echo
	@echo 'Steps -- each does one thing, and only if its inputs changed'
	@echo '  make netlist-lvs   xschem -> $(NETLIST)  (device lines)'
	@echo '  make netlist-sim   xschem -> $(SIM_NL)  (subckt calls)'
	@echo '  make netlist       both'
	@echo '  make sim           ngspice on the testbench'
	@echo '  make plot          waveforms -> ../docs/'
	@echo '  make gds           $(BUILD) -> $(GDS)'
	@echo '  make png           render the layout'
	@echo '  make drc           KLayout DRC on $(GDS)'
	@echo '  make lvs           KLayout LVS, $(GDS) vs $(NETLIST)'
	@echo '  make lib           ngspice characterisation -> $(LIB)'
	@echo
	@echo 'Pipelines'
	@echo '  make design        netlist sim gds drc lvs   -- is the block right?'
	@echo '  make macro         gds lib drc lvs           -- ready for LibreLane?'
	@echo '  make all           both'
	@echo
	@echo 'The tile itself is hardened from the repository root: make -C .. harden'
	@echo
	@echo '3D views of $(CELL)'
	@echo '  make glb           out/tile_3d.glb, no display needed'
	@echo '  make d25           KLayout 2.5D viewer      (needs a display)'
	@echo '  make view3d        GDS3D                    (needs a display)'
	@echo '  make gds3d-tech    regenerate the GDS3D process file from the PDK'
	@echo
	@echo 'Other:  list  xschem  klayout  shell  ci  clean  distclean'
	@echo 'Force a rerun with  make -B <target>'

list:
	@echo 'Schematics in xschem/  --  make sim|netlist CELL=<name>'
	@ls xschem/*.sch 2>/dev/null | sed 's|xschem/||; s|\.sch$$||' | sed 's/^/    /' || true
	@echo
	@echo 'Scripts in layout/  --  by convention build_<cell>.py makes out/<cell>.gds,'
	@echo 'but not every script here is a cell builder; some are utilities.'
	@ls layout/*.py 2>/dev/null | sed 's|layout/||; s|\.py$$||' | sed 's/^/    /' || true
	@echo
	@echo 'The analog macro the tile imports (the default CELL, built by $(BUILD)):'
	@echo '    $(MACRO)'

out:
	@mkdir -p out

$(CELLDIR):
	@mkdir -p $(CELLDIR)

# =================================================================== netlists
# Same schematic, two incompatible outputs:
#
#   .sim.spice  devices as subcircuit calls, "XM1 ... sg13_lv_pmos". ngspice
#               wants this.
#   .lvs.spice  devices as device lines, "MM1 ...", via `set lvs_netlist 1`.
#               LVS compares extracted devices and reads the X-prefixed form as
#               subcircuit instances, so giving it the simulation netlist fails
#               with no useful diagnostic.
#
# `set top_subckt 1` wraps the top schematic in .subckt/.ends instead of
# netlisting it as a flat top level.
# LVS keeps xschem's natural output name, out/<cell>.spice. Other tooling --
# checks/build_tile_netlist.py, for one -- expects to find it there.
out/%.spice: xschem/%.sch $(SCH_ALL) | out
	$(RUN) bash -lc 'cd /work/analog/xschem && $(XSCHEM) --tcl "set lvs_netlist 1; set top_subckt 1" $*.sch -o /work/analog/out'

out/%.sim.spice: xschem/%.sch $(SCH_ALL) | out
	$(RUN) bash -lc 'cd /work/analog/xschem && $(XSCHEM) $*.sch -o /work/analog/out'
	@mv out/$*.spice $@

# Reached when there is no such testbench. The submission top has none, which is
# why `make design` is a block-level pipeline and `make tt` is the one for the tile.
out/%.sim.spice:
	@echo "No testbench xschem/$*.sch."
	@echo "make sim expects xschem/<CELL>_tb.sch, or pass TB=<name>."
	@echo "Run 'make list' to see the schematics that exist."
	@exit 1

netlist-lvs: $(NETLIST)
netlist-sim: $(SIM_NL)
netlist: netlist-lvs netlist-sim

# ================================================================= simulation
# The analysis lives in the testbench schematic's .control block -- edit it
# there, not here.
sim: $(SIM_NL)
	$(RUN) bash -lc 'cd /work/analog/out && ngspice -b $(TB).sim.spice'

plot: sim
	$(RUN) python3 $(PLOT)

# ===================================================================== layout
gds: $(GDS)

# Generic blocks: layout/build_<cell>.py -> out/<cell>.gds
out/%.gds: layout/build_%.py | out
	$(RUN) klayout -b -r $<

# Reached only when the rule above cannot fire because there is no generator for
# this cell. Without it make says "No rule to make target 'out/foo.gds'", which
# does not tell you what to create.
out/%.gds:
	@echo "No layout generator for CELL=$*."
	@echo "Expected layout/build_$*.py, writing out/$*.gds."
	@echo "Run 'make list' to see what exists, or pass GDS=<path> to use a"
	@echo "layout that is built some other way."
	@exit 1

# The macro. Its builder also emits the LEF from the same constants, which is
# why there is no separate `make lef` -- the two must not be able to drift.
macro/$(MACRO).gds: layout/build_$(MACRO).py
	$(RUN) klayout -b -r $<

macro/$(MACRO).lef: macro/$(MACRO).gds ;
lef: $(LEF)

# ============================================================ characterisation
# Liberty for the macro, measured in ngspice on the transistor-level netlist.
# LibreLane cannot synthesise, place or sign off around the macro without it.
lib: $(LIB)
lib/$(MACRO).lib: char/characterize.py out/inverter.sim.spice
	$(RUN) python3 char/characterize.py

png: $(GDS) layout/render.py
	$(RUN) klayout -b -z -r layout/render.py

# ==================================================================== signoff
drc: $(DRC_OK)
$(DRC_OK): $(GDS) | $(CELLDIR)
	@rm -rf $(CELLDIR)/drc && mkdir -p $(CELLDIR)/drc
	$(RUN) bash -lc 'python3 $(PDKTECH)/drc/run_drc.py --path=/work/analog/$(GDS) \
	    --topcell=$(CELL) --run_dir=/work/analog/$(CELLDIR)/drc --no_density --no_offgrid'
	@touch $@

# --disable_tap_extraction keeps the well and substrate ties out of the device
# list. Without it they extract as ntap1/ptap1 resistors with the transistor
# bulks on unnamed nets, which no hand-drawn schematic will ever match.
lvs: $(LVS_OK)
$(LVS_OK): $(GDS) $(NETLIST) | $(CELLDIR)
	@rm -rf $(CELLDIR)/lvs && mkdir -p $(CELLDIR)/lvs
	$(RUN) bash -lc 'python3 $(PDKTECH)/lvs/run_lvs.py --layout=/work/analog/$(GDS) \
	    --netlist=/work/analog/$(NETLIST) --topcell=$(CELL) \
	    --run_dir=/work/analog/$(CELLDIR)/lvs --disable_tap_extraction'
	@touch $@

# Tiny Tapeout's precheck runs on the hardened tile, not on this block, so it
# lives in the top-level Makefile: `make -C .. precheck`.

# ================================================================== pipelines
# Block-level: needs a testbench, so run it as `make design CELL=<block>`.
# For the submission tile, which has no testbench, use `make tt`.
design: netlist sim gds drc lvs
	@echo '=== $(CELL): simulated, DRC clean, LVS matching ==='

# What the tile needs from this directory: layout, timing, and the two checks
# that say the layout is legal and matches the schematic.
macro: gds lib drc lvs
	@echo '=== $(MACRO): GDS, LEF and Liberty ready for LibreLane ==='

all: design macro

# ============================================================== 3D viewing
# Three views of the same stack. GDS3D and KLayout's 2.5D view both need an X
# display; the glTF export does not, which is why it exists -- reach for it over
# ssh or when the container cannot get to the display.
#
# All three read the same layer heights: KLayout's come from the PDK's
# libs.tech/klayout/tech/d25/sg13g2_beol.lyd25, and GDS3D's process file is
# generated from that same file by build_gds3d_tech.py, so the views agree by
# construction.
GLB       := out/tile_3d.glb
GDS3D_TECH:= tech/sg13g2_gds3d.txt

glb: $(GLB)
$(GLB): $(GDS) layout/build_glb.py $(GDS3D_TECH) | out
	$(RUN) python3 layout/build_glb.py $(GDS) $(CELL)

# The process file is a tool configuration rather than a build artefact, so it is
# committed; regenerate it only if the PDK revises a layer height.
gds3d-tech:
	$(RUN) python3 layout/build_gds3d_tech.py

# -n loads the PDK *technology*, which is what registers the 2.5D macro; -l would
# only load the layer properties. The viewer then lives under
# sg13g2_menu > SG13G2 PDK > BEOL 2.5D Viewer, and wants a selection first.
d25:
	$(GUI) klayout -n sg13g2 /work/analog/$(GDS)

view3d: $(GDS3D_TECH)
	$(GUI) GDS3D -p /work/analog/$(GDS3D_TECH) -i /work/analog/$(GDS) -t $(CELL)

# ================================================================ interactive
xschem:
	$(GUI) xschem --rcfile /work/analog/xschem/xschemrc /work/analog/xschem/$(TB).sch

klayout:
	$(GUI) klayout -e -l $(PDKTECH)/sg13g2.lyp /work/analog/$(GDS)

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
	rm -f ../gds/$(TT_TOP).gds ../lef/$(TT_TOP).lef
