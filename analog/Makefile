# The analog block: a current-starved ring oscillator with an 8-bit current
# DAC, built as a hard macro for the digital tile.
#
#   make macro      gds + lib + drc + lvs: everything the tile needs
#   make sim        frequency vs. code sweep of the generated netlist
#   make png        layout figures -> ../docs/
#
# Everything runs in the hpretl/iic-osic-tools container via ./run.sh, so
# Docker is the only host dependency. `make help` lists the targets.

MACRO   := tt_analog_ring
RUN     := ./run.sh
GUI     := ./gui.sh
PDKTECH := /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech

BUILD   := layout/build_$(MACRO).py
GDS     := macro/$(MACRO).gds
LEF     := macro/$(MACRO).lef
LIB     := lib/$(MACRO).lib
SIM_NL  := spice/$(MACRO).spice
LVS_NL  := spice/$(MACRO).lvs.spice
SWEEP   := out/sweep.csv
DRC_OK  := out/drc/.passed
LVS_OK  := out/lvs/.passed

.DEFAULT_GOAL := help
.PHONY: help gds drc drc-density lvs lvs-diff sim plot lib png macro all \
        klayout shell clean

help:
	@echo 'Analog block: $(MACRO)'
	@echo
	@echo '  make gds          $(BUILD) -> $(GDS), $(LEF), $(SIM_NL), $(LVS_NL)'
	@echo '  make drc          KLayout DRC, sg13g2 maximal rule set, no density'
	@echo '  make drc-density  the density rules alone (informational: density is a tile-level matter)'
	@echo '  make lvs          KLayout LVS, $(GDS) vs $(LVS_NL)'
	@echo '  make lvs-diff     list what did not match in the last LVS run'
	@echo '  make sim          ngspice: frequency and current vs. code -> $(SWEEP)'
	@echo '  make plot         $(SWEEP) -> ../docs/analog_ring_sweep.png'
	@echo '  make lib          ngspice characterisation -> $(LIB)'
	@echo '  make png          layout figures -> ../docs/'
	@echo
	@echo '  make macro        gds lib drc lvs      -- ready for LibreLane?'
	@echo '  make all          macro sim plot png'
	@echo
	@echo '  make klayout      open the layout (needs a display)'
	@echo '  make shell        a prompt inside the container'
	@echo '  make clean        remove out/'
	@echo
	@echo 'Variables for make sim: CODES=0,1,2,... CORNER=mos_tt TEMP=27 VDD=1.2'

# ------------------------------------------------------------------ layout
# The generator writes the GDS, the LEF and both netlists in one go, so they
# cannot drift apart.
gds: $(GDS)
$(GDS) $(LEF) $(SIM_NL) $(LVS_NL): $(BUILD)
	$(RUN) klayout -b -r $(BUILD)

png: $(GDS) layout/render.py
	$(RUN) klayout -b -z -r layout/render.py

# ----------------------------------------------------------------- signoff
drc: $(DRC_OK)
$(DRC_OK): $(GDS)
	@rm -rf out/drc && mkdir -p out/drc
	$(RUN) bash -lc 'python3 $(PDKTECH)/drc/run_drc.py --path=/work/analog/$(GDS) \
	    --topcell=$(MACRO) --run_dir=/work/analog/out/drc --no_density --mp=8'
	@touch $@

drc-density: $(GDS)
	@rm -rf out/drc-density && mkdir -p out/drc-density
	$(RUN) bash -lc 'python3 $(PDKTECH)/drc/run_drc.py --path=/work/analog/$(GDS) \
	    --topcell=$(MACRO) --run_dir=/work/analog/out/drc-density --density_only' || true

# --disable_tap_extraction keeps the well and substrate ties out of the
# device list; otherwise they extract as ntap1/ptap1 resistors that the
# schematic does not have.
lvs: $(LVS_OK)
$(LVS_OK): $(GDS) $(LVS_NL)
	@rm -rf out/lvs && mkdir -p out/lvs
	$(RUN) bash -lc 'python3 $(PDKTECH)/lvs/run_lvs.py --layout=/work/analog/$(GDS) \
	    --netlist=/work/analog/$(LVS_NL) --topcell=$(MACRO) \
	    --run_dir=/work/analog/out/lvs --disable_tap_extraction'
	@touch $@

lvs-diff:
	$(RUN) klayout -b -r layout/lvs_diff.py -rd db=out/lvs/$(MACRO).lvsdb

# -------------------------------------------------------------- simulation
CODES  ?= 0,1,2,3,4,6,8,12,16,24,32,48,64,96,128,160,192,224,255
CORNER ?= mos_tt
TEMP   ?= 27
VDD    ?= 1.2

sim: $(SWEEP)
$(SWEEP): $(SIM_NL) char/sweep_codes.py
	$(RUN) python3 char/sweep_codes.py --netlist $(SIM_NL) --out $@ \
	    --codes $(CODES) --corner $(CORNER) --temp $(TEMP) --vdd $(VDD)

plot: $(SWEEP) char/plot_sweep.py
	$(RUN) python3 char/plot_sweep.py $(SWEEP) ../docs/analog_ring_sweep.png

# --------------------------------------------------------- characterisation
lib: $(LIB)
$(LIB): $(SIM_NL) char/characterize.py
	$(RUN) python3 char/characterize.py

# --------------------------------------------------------------- pipelines
macro: gds lib drc lvs
	@echo '=== $(MACRO): GDS, LEF and Liberty ready for LibreLane; DRC clean, LVS matching ==='

all: macro sim plot png

# ------------------------------------------------------------- interactive
klayout:
	$(GUI) klayout -e -l $(PDKTECH)/sg13g2.lyp /work/analog/$(GDS)

shell:
	$(GUI) bash

clean:
	rm -rf out
