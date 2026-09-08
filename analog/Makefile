# Analog block: current-starved ring oscillator + 8-bit current DAC as a hard macro (tt_analog_ring).
#   make macro      gds + lib + drc + lvs, everything the tile needs
#   make help       every target
# Everything runs in the hpretl/iic-osic-tools container via ./run.sh; Docker is the only host dependency.

MACRO   := tt_analog_ring
RUN     := ./run.sh
GUI     := ./gui.sh
PDKTECH := /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech

# CELL/GDS are overridden by the repo root's `make view` to show the hardened tile in 3D (see 3D viewing)
CELL    ?= $(MACRO)
BUILD   := layout/build_$(MACRO).py
GDS     := macro/$(MACRO).gds
LEF     := macro/$(MACRO).lef
LIB     := lib/$(MACRO).lib
SIM_NL  := spice/$(MACRO).spice
LVS_NL  := spice/$(MACRO).lvs.spice
PEX_RAW := out/pex/$(MACRO)_pex.spice
PEX_SIM := out/pex/$(MACRO).pex.spice
SWEEP   := out/sweep.csv
DRC_OK  := out/drc/.passed
LVS_OK  := out/lvs/.passed

.DEFAULT_GOAL := help
.PHONY: help gds drc drc-density lvs lvs-diff sim plot lib png macro all \
        sch sch-png netlist-sch lvs-sch xschem klayout shell clean \
        verify verify-blocks verify-dac verify-bias verify-stage verify-nand \
        verify-buffer verify-ring verify-report verify-env verify-env-post \
        pex sim-post verify-ring-post \
        glb gds3d-tech d25 view3d

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
	@echo '  make lib          ngspice characterisation of the POST-LAYOUT netlist -> $(LIB) (runs pex)'
	@echo '  make png          layout figures -> ../docs/'
	@echo
	@echo '  make sch          xschem/make_sch.py -> xschem/*.sch, *.sym  (the schematic)'
	@echo '  make sch-png      render every sheet -> ../docs/sch_*.png'
	@echo '  make lvs-sch      netlist the schematic flat and LVS it against the layout'
	@echo
	@echo '  make verify       corners + Monte Carlo + noise, every block then the whole macro'
	@echo '                    (verify-dac, -bias, -stage, -nand, -buffer, -ring, -report; VERIFY_JOBS=$(VERIFY_JOBS))'
	@echo '  make verify-env   the tile as noise: supply ripple, ground bounce, crosstalk (verify-env-post: on the extracted netlist)'
	@echo
	@echo '  make pex          kpex parasitics of $(MACRO) -> $(PEX_SIM)'
	@echo '  make sim-post     parasitics per block + pre/post-layout side by side -> ../docs/analog_ring_sim_post.png'
	@echo '  make verify-ring-post  the whole-block verification on the extracted netlist'
	@echo
	@echo '  make macro        gds lib drc lvs      (everything LibreLane needs)'
	@echo '  make all          macro sim plot png'
	@echo
	@echo '3D views of $(CELL) (repo root: make view, the hardened submission tile)'
	@echo '  make glb           out/tile_3d.glb, no display needed'
	@echo '  make d25           KLayout 2.5D viewer      (needs a display)'
	@echo '  make view3d        GDS3D                    (needs a display)'
	@echo '  make gds3d-tech    regenerate the GDS3D process file from the PDK'
	@echo
	@echo '  make xschem       open the schematic (needs a display)'
	@echo '  make klayout      open the layout (needs a display)'
	@echo '  make shell        a prompt inside the container'
	@echo '  make clean        remove out/'
	@echo
	@echo 'Variables for make sim: CODES=0,1,2,... CORNER=mos_tt TEMP=27 VDD=1.2'

# ------------------------------------------------------------------ layout
# one generator writes GDS, LEF and both netlists, so they cannot drift apart
gds: $(GDS)
$(GDS) $(LEF) $(SIM_NL) $(LVS_NL): $(BUILD)
	$(RUN) klayout -b -r $(BUILD)

png: $(GDS) layout/render.py
	$(RUN) klayout -b -z -r layout/render.py

# --------------------------------------------------------------- schematic
# the generator's netlist is the LVS reference; lvs-sch proves the xschem drawing matches the layout too
SCH     := xschem/tt_analog_ring.sch
SHEETS  := tt_analog_ring csro_stage csro_nand csro_dac csro_inv
XSCHEM  := xschem --rcfile /work/analog/xschem/xschemrc
SCH_NL  := out/tt_analog_ring.sch.lvs.spice

sch: $(SCH)
$(SCH): xschem/make_sch.py
	python3 xschem/make_sch.py

netlist-sch: $(SCH_NL)
$(SCH_NL): $(SCH) xschem/wrap_flat.py
	$(RUN) bash -lc 'cd /work/analog/xschem && $(XSCHEM) -n -s -q --no_x -f \
	    --tcl "set lvs_netlist 1; set top_subckt 1" tt_analog_ring.sch -o /work/analog/out'
	python3 xschem/wrap_flat.py out/tt_analog_ring.spice $@

lvs-sch: $(GDS) $(SCH_NL)
	@rm -rf out/lvs-sch && mkdir -p out/lvs-sch
	$(RUN) bash -lc 'python3 $(PDKTECH)/lvs/run_lvs.py --layout=/work/analog/$(GDS) \
	    --netlist=/work/analog/$(SCH_NL) --topcell=$(MACRO) \
	    --run_dir=/work/analog/out/lvs-sch --disable_tap_extraction'

# rendered through xvfb; no display needed
sch-png: $(SCH)
	$(RUN) bash -lc 'cd /work/analog/xschem && for f in $(SHEETS); do \
	    xvfb-run -a $(XSCHEM) -q --command "xschem zoom_full; xschem print png /work/docs/sch_$$f.png" $$f.sch >/dev/null 2>&1; done'
	@ls ../docs/sch_*.png

xschem:
	$(GUI) $(XSCHEM) /work/analog/$(SCH)

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

# --disable_tap_extraction: the ties would otherwise extract as ntap1/ptap1 resistors the schematic lacks
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
# the shipped Liberty is from the POST-LAYOUT netlist (code buses add 16..90 % to the gate caps), so lib runs kpex first
lib: $(LIB)
$(LIB): $(PEX_SIM) char/characterize.py
	$(RUN) python3 char/characterize.py --netlist $(PEX_SIM) --out out/char_post

# ------------------------------------------------------------ verification
# strategy: docs/analog_verification.md; verify regenerates docs/analog_verification_results.md and docs/verify_*.png
VERIFY_JOBS ?= 14
BLOCKS := out/blocks/blocks.spice

verify-blocks: $(BLOCKS)
$(BLOCKS): $(SCH) verify/netlist_blocks.py
	$(RUN) python3 verify/netlist_blocks.py

verify-dac verify-bias verify-stage verify-nand verify-buffer: $(BLOCKS)
	$(RUN) python3 verify/$(subst verify-,,$@).py --jobs $(VERIFY_JOBS)

verify-ring: $(SIM_NL)
	$(RUN) python3 verify/ring.py --jobs $(VERIFY_JOBS)

verify-report:
	python3 verify/report.py

verify: verify-dac verify-bias verify-stage verify-nand verify-buffer verify-ring verify-report

# the tile as sources around the macro: supply ripple, ground bounce, crosstalk (verify/environment.py)
verify-env: $(SIM_NL)
	$(RUN) python3 verify/environment.py --jobs $(VERIFY_JOBS)

verify-env-post: $(PEX_SIM)
	$(RUN) python3 verify/environment.py --netlist $(PEX_SIM) --tag env_post --jobs $(VERIFY_JOBS)

# ------------------------------------------------------------- post-layout
# kpex 2.5D capacitances of the flat macro; build_sim_post.py makes the output a drop-in for the pre-layout netlist
pex: $(PEX_SIM)
$(PEX_RAW): $(GDS) $(LVS_NL)
	@rm -rf out/pex && mkdir -p out/pex
	$(RUN) kpex --pdk ihp-sg13g2 --2.5D --gds /work/analog/$(GDS) \
	    --schematic /work/analog/$(LVS_NL) --cell $(MACRO) \
	    --out_dir /work/analog/out/pex --out_spice /work/analog/$(PEX_RAW) --threads 8
$(PEX_SIM): $(PEX_RAW) layout/build_sim_post.py
	python3 layout/build_sim_post.py --pex $(PEX_RAW) --out $@

# parasitics per block, and pre vs post layout side by side (verify/pex.py)
sim-post: $(PEX_SIM)
	$(RUN) python3 verify/pex.py --pex $(PEX_SIM) --jobs $(VERIFY_JOBS)

# ring.py on the extracted netlist (~1.3 h); --fscale 0.5 because the extracted ring is about half as fast
verify-ring-post: $(PEX_SIM)
	$(RUN) python3 verify/ring.py --netlist $(PEX_SIM) --tag ring_post --fscale 0.5 --jobs $(VERIFY_JOBS)


# --------------------------------------------------------------- pipelines
macro: gds lib drc lvs
	@echo '=== $(MACRO): GDS, LEF and Liberty ready for LibreLane; DRC clean, LVS matching ==='

all: macro lvs-sch sim plot png sch-png

# ============================================================== 3D viewing
# glb needs no display (use it over ssh); d25 and view3d do. All three use the PDK's
# sg13g2_beol.lyd25 heights: the GDS3D process file is generated from it (build_gds3d_tech.py).
GLB       := out/tile_3d.glb
GDS3D_TECH:= tech/sg13g2_gds3d.txt

# always rebuilt: the output path does not depend on GDS/CELL, so a stale glb from another CELL would look current
glb: $(GDS) layout/build_glb.py $(GDS3D_TECH) | out
	$(RUN) python3 layout/build_glb.py $(GDS) $(CELL)

# committed tool configuration; regenerate only if the PDK revises a layer height
gds3d-tech:
	$(RUN) python3 layout/build_gds3d_tech.py

# -n loads the PDK technology (registers the 2.5D macro; -l would not); viewer under
# sg13g2_menu > SG13G2 PDK > BEOL 2.5D Viewer, select shapes first
d25:
	$(GUI) klayout -n sg13g2 /work/analog/$(GDS)

view3d: $(GDS3D_TECH)
	$(GUI) GDS3D -p /work/analog/$(GDS3D_TECH) -i /work/analog/$(GDS) -t $(CELL)

out:
	mkdir -p out

# ------------------------------------------------------------- interactive
klayout:
	$(GUI) klayout -e -l $(PDKTECH)/sg13g2.lyp /work/analog/$(GDS)

shell:
	$(GUI) bash

clean:
	rm -rf out
