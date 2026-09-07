# On-chip ring oscillator frequency meter -- Tiny Tapeout IHP 26b
#
# Simulation is the main loop and needs only iverilog:
#
#   make test               every module testbench, in build order
#   make test_<module>      one of them (see the list below)
#   make sweep              the exit criterion: 8 rings x 256 codes -> CSV + plots
#
# The Tiny Tapeout flow (cocotb for CI, LibreLane hardening, precheck) is at
# the bottom and is unchanged from the template apart from the file list.

IVERILOG := iverilog -g2005 -Wall -Wno-timescale
VVP      := vvp
PY       := venv/bin/python

# Synthesisable sources, in the order the top needs them.
RTL := src/project.v \
       src/regfile.v \
       src/measure_core.v \
       src/cdc_sync.v \
       src/ring_divider.v \
       src/ring_mux.v \
       src/rings/ring_bank.v \
       src/rings/ring_21_min.v \
       src/rings/ring_21_hd.v \
       src/rings/ring_11_min.v \
       src/rings/ring_tap.v \
       src/rings/tt_analog_ring.v

.DEFAULT_GOAL := help
.PHONY: help test sweep plot clean \
        test_ring_model test_ring_divider test_cdc_sync test_measure_core \
        test_ring_mux test_rings test_top

help:
	@echo 'Simulation (iverilog):'
	@echo '  make test                 run every testbench'
	@echo '  make test_ring_model      1. behavioural ring, the ground truth'
	@echo '  make test_ring_divider    2. programmable-tap divider, all 8 taps'
	@echo '  make test_measure_core    3. reciprocal counter + FSM + timeout'
	@echo '  make test_cdc_sync        4. two-flop synchroniser, awkward ratios'
	@echo '  make test_ring_mux        5. ring select and one-hot enables'
	@echo '  make test_rings           7. structural ring netlists oscillate'
	@echo '  make test_top             8. whole tile through its pins'
	@echo '  make sweep                8. 8 rings x 256 codes -> build/sweep.csv, docs/sweep*.png'
	@echo
	@echo 'The analog macro (analog/):'
	@echo '  make macro                layout, Liberty, DRC, LVS of the ring oscillator block (Docker)'
	@echo
	@echo 'Tiny Tapeout flow:'
	@echo '  make cocotb               the CI testbench (test/), RTL'
	@echo '  make tools                clone tt-support-tools, set up venv'
	@echo '  make harden               LibreLane the tile locally'
	@echo '  make precheck             Tiny Tapeout precheck on the result'

build:
	mkdir -p build

# Each testbench prints "RESULT: PASS" or "RESULT: FAIL"; the grep is what
# turns that into a make failure.

test_ring_model: | build
	$(IVERILOG) -o build/tb_ring_model sim/tb_ring_model.v sim/ring_model.v
	$(VVP) build/tb_ring_model | tee build/tb_ring_model.log
	@grep -q 'RESULT: PASS' build/tb_ring_model.log

test_ring_divider: | build
	$(IVERILOG) -o build/tb_ring_divider sim/tb_ring_divider.v src/ring_divider.v sim/sg13g2_cells_sim.v
	$(VVP) build/tb_ring_divider | tee build/tb_ring_divider.log
	@grep -q 'RESULT: PASS' build/tb_ring_divider.log

test_measure_core: | build
	$(IVERILOG) -o build/tb_measure_core sim/tb_measure_core.v src/measure_core.v src/cdc_sync.v
	$(VVP) build/tb_measure_core | tee build/tb_measure_core.log
	@grep -q 'RESULT: PASS' build/tb_measure_core.log

test_cdc_sync: | build
	$(IVERILOG) -o build/tb_cdc_sync sim/tb_cdc_sync.v src/cdc_sync.v
	$(VVP) build/tb_cdc_sync | tee build/tb_cdc_sync.log
	@grep -q 'RESULT: PASS' build/tb_cdc_sync.log

test_ring_mux: | build
	$(IVERILOG) -o build/tb_ring_mux sim/tb_ring_mux.v src/ring_mux.v sim/sg13g2_cells_sim.v
	$(VVP) build/tb_ring_mux | tee build/tb_ring_mux.log
	@grep -q 'RESULT: PASS' build/tb_ring_mux.log

# Structural rings: compiled WITHOUT -DSIM, with the delay stand-ins.
test_rings: | build
	$(IVERILOG) -o build/tb_rings sim/tb_rings.v sim/sg13g2_cells_sim.v src/rings/*.v
	$(VVP) build/tb_rings | tee build/tb_rings.log
	@grep -q 'RESULT: PASS' build/tb_rings.log

# Whole tile, rings replaced by the behavioural model (-DSIM).
test_top: | build
	$(IVERILOG) -DSIM -Isim -o build/tb_top sim/tb_top.v sim/ring_model.v $(RTL)
	$(VVP) build/tb_top | tee build/tb_top.log
	@grep -q 'RESULT: PASS' build/tb_top.log

test: test_ring_model test_ring_divider test_measure_core test_cdc_sync \
      test_ring_mux test_rings test_top
	@echo
	@echo 'All testbenches passed.'

sweep: | build
	$(IVERILOG) -DSIM -Isim -o build/tb_sweep sim/tb_sweep.v sim/ring_model.v $(RTL)
	$(VVP) build/tb_sweep | tee build/tb_sweep.log
	@grep -q 'RESULT: PASS' build/tb_sweep.log
	$(MAKE) plot

plot:
	$(PY) scripts/plot_sweep.py build/sweep.csv docs/sweep.png

clean:
	rm -rf build runs tt_submission src/user_config.json src/config_merged.json
	$(MAKE) -C test clean || true

# ============================================================================
# Tiny Tapeout flow -- as the template, see CLAUDE.md on the main branch for
# the full local-hardening story including a hard macro.
# ============================================================================
TOP      := $(shell sed -n 's/^ *top_module: *"\(.*\)".*/\1/p' info.yaml)
VENV     := venv
PIP      := $(VENV)/bin/pip
PDK_ROOT ?= $(HOME)/pdk
RUN      := flow/run.sh
TT       := tt
TT_REPO  := https://github.com/TinyTapeout/tt-support-tools.git
FINAL_GDS  := runs/wokwi/final/gds/$(TOP).gds
SUBMISSION := tt_submission/$(TOP).gds

.PHONY: cocotb tools harden precheck submission macro

# The analog block is built and checked in its own directory, in the
# iic-osic-tools container. Its outputs (analog/macro/*.gds, *.lef and
# analog/lib/*.lib) are committed because CI cannot regenerate them.
macro:
	$(MAKE) -C analog macro

cocotb:
	PATH="$(PWD)/$(VENV)/bin:$$PATH" $(MAKE) -C test clean
	PATH="$(PWD)/$(VENV)/bin:$$PATH" $(MAKE) -C test

$(TT):
	git clone --depth 1 $(TT_REPO) $(TT)

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip

tools: $(TT) | $(VENV)
	$(PIP) install -q -r $(TT)/requirements.txt -r test/requirements.txt matplotlib
	$(PIP) install -q yowasp-yosys librelane==3.0.5

harden: $(FINAL_GDS)
$(FINAL_GDS): $(RTL) src/config.json info.yaml | $(TT)
	PATH="$(PWD)/$(VENV)/bin:$$PATH" PDK_ROOT=$(PDK_ROOT) \
	    $(PY) $(TT)/tt_tool.py --create-user-config --ihp
	PATH="$(PWD)/$(VENV)/bin:$$PATH" PDK_ROOT=$(PDK_ROOT) \
	    $(PY) $(TT)/tt_tool.py --harden --ihp

submission: $(SUBMISSION)
$(SUBMISSION): $(FINAL_GDS)
	PATH="$(PWD)/$(VENV)/bin:$$PATH" PDK_ROOT=$(PDK_ROOT) \
	    $(PY) $(TT)/tt_tool.py --create-tt-submission --ihp

precheck: $(SUBMISSION)
	$(RUN) bash -lc 'cd /work/$(TT)/precheck && \
	    PDK_ROOT=/foss/pdks PDK=ihp-sg13g2 PATH=$$PATH:/foss/tools/klayout \
	    python precheck.py --gds /work/tt_submission/$(TOP).gds --tech ihp-sg13g2'
