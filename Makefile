# Tiny Tapeout mixed-signal tile: digital top, analog macro inside.
#
# The tile is hardened by LibreLane through tt-support-tools, exactly as CI
# does it. This Makefile runs the same commands locally so a failure can be
# seen in a minute instead of after a seven-minute CI round trip.
#
#   make macro      build + check the analog block         (Docker)
#   make harden     LibreLane the tile around it           (Docker, ~2 min)
#   make precheck   Tiny Tapeout's own precheck on the GDS (Docker)
#   make test       cocotb, RTL                            (host)
#   make all        macro -> harden -> precheck -> test
#
# `make harden` needs a host Python environment (LibreLane drives its own
# container); everything else runs in the iic-osic-tools image.

TOP      := $(shell sed -n 's/^ *top_module: *"\(.*\)".*/\1/p' info.yaml)
VENV     := venv
PY       := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip
PDK_ROOT ?= $(HOME)/pdk
RUN      := flow/run.sh

# tt-support-tools is cloned, not vendored, so that what runs here is what runs
# in CI. It is gitignored.
TT       := tt
TT_REPO  := https://github.com/TinyTapeout/tt-support-tools.git

MACRO_GDS := analog/macro/tt_analog_inverter.gds
MACRO_LIB := analog/lib/tt_analog_inverter.lib
FINAL_GDS := runs/wokwi/final/gds/$(TOP).gds
SUBMISSION := tt_submission/$(TOP).gds

.DEFAULT_GOAL := help
.PHONY: help macro harden precheck test test-gl submission clean distclean \
        tools venv view

help:
	@echo 'Tiny Tapeout tile: $(TOP)'
	@echo
	@echo '  make macro       analog/: build the inverter macro, DRC + LVS it'
	@echo '  make harden      LibreLane the whole tile (uses $$PDK_ROOT=$(PDK_ROOT))'
	@echo '  make precheck    run Tiny Tapeout precheck on the hardened GDS'
	@echo '  make test        cocotb tests against the RTL'
	@echo '  make test-gl     cocotb tests against the gate-level netlist'
	@echo '  make submission  stage tt_submission/ as CI would'
	@echo '  make all         macro -> harden -> precheck -> test'
	@echo
	@echo 'Block-level analog work lives in analog/:  make -C analog help'

all: macro harden precheck test

# ------------------------------------------------------------------- the macro
macro:
	$(MAKE) -C analog macro

# ------------------------------------------------------------------- the tile
# tt-support-tools generates src/user_config.json from info.yaml, merges it over
# src/config.json, and runs LibreLane in its own container. This is exactly the
# sequence tt-gds-action runs.
$(TT):
	git clone --depth 1 $(TT_REPO) $(TT)

tools: $(TT) | $(VENV)
	$(PIP) install -q -r $(TT)/requirements.txt
	$(PIP) install -q yowasp-yosys librelane==3.0.5

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip

venv: $(VENV)

harden: $(FINAL_GDS)
$(FINAL_GDS): src/*.v src/config.json info.yaml $(MACRO_GDS) $(MACRO_LIB) | $(TT)
	PATH="$(PWD)/$(VENV)/bin:$$PATH" PDK_ROOT=$(PDK_ROOT) \
	    $(PY) $(TT)/tt_tool.py --create-user-config --ihp
	PATH="$(PWD)/$(VENV)/bin:$$PATH" PDK_ROOT=$(PDK_ROOT) \
	    $(PY) $(TT)/tt_tool.py --harden --ihp

submission: $(SUBMISSION)
$(SUBMISSION): $(FINAL_GDS)
	PATH="$(PWD)/$(VENV)/bin:$$PATH" PDK_ROOT=$(PDK_ROOT) \
	    $(PY) $(TT)/tt_tool.py --create-tt-submission --ihp

# ---------------------------------------------------------------- the prechecks
# Run in the iic-osic-tools container: precheck shells out to `klayout` and to
# `yowasp-yosys`, and the container has both plus the PDK's DRC decks.
precheck: $(SUBMISSION)
	$(RUN) bash -lc 'cd /work/$(TT)/precheck && \
	    PDK_ROOT=/foss/pdks PDK=ihp-sg13g2 PATH=$$PATH:/foss/tools/klayout \
	    python precheck.py --gds /work/tt_submission/$(TOP).gds --tech ihp-sg13g2'

# --------------------------------------------------------------------- testing
test:
	PATH="$(PWD)/$(VENV)/bin:$$PATH" $(MAKE) -C test clean
	PATH="$(PWD)/$(VENV)/bin:$$PATH" $(MAKE) -C test

# Needs Tiny Tapeout's iverilog 13 build; see test/README.md. Distribution
# iverilog 12 leaves every flop at X, and the container's 14 will not parse the
# PDK's cell models at all.
test-gl: $(FINAL_GDS)
	cp runs/wokwi/final/nl/$(TOP).v test/gate_level_netlist.v
	PATH="$(PWD)/$(VENV)/bin:$$PATH" $(MAKE) -C test clean
	PATH="$(PWD)/$(VENV)/bin:$$PATH" PDK_ROOT=$(PDK_ROOT)/ciel/ihp-sg13g2/versions/$$(ls $(PDK_ROOT)/ciel/ihp-sg13g2/versions | head -1) \
	    $(MAKE) -C test GATES=yes

# ------------------------------------------------------------------- 3D / view
view:
	$(MAKE) -C analog glb GDS=../$(FINAL_GDS) CELL=$(TOP)

clean:
	rm -rf runs tt_submission src/user_config.json src/config_merged.json
	$(MAKE) -C test clean || true

distclean: clean
	$(MAKE) -C analog distclean || true
	rm -rf $(TT)
