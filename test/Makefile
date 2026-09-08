# test/Makefile -- cocotb bench (test.py) at RTL, or GATES=yes on the hardened netlist
# https://docs.cocotb.org/en/stable/quickstart.html

# defaults
SIM ?= icarus
FST ?= -fst # Use more efficient FST format
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src
PROJECT_SOURCES = project.v regfile.v measure_core.v cdc_sync.v ring_divider.v ring_mux.v \
                  rings/ring_bank.v rings/ring_21_min.v rings/ring_21_hd.v rings/ring_11_min.v \
                  rings/ring_tap.v rings/tt_analog_ring.v

ifneq ($(GATES),yes)

# RTL simulation:
SIM_BUILD				= sim_build/rtl
# -DSIM swaps every ring's structural netlist for sim/ring_model.v, whose frequencies are known exactly.
COMPILE_ARGS    += -DSIM
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))
VERILOG_SOURCES += $(PWD)/../sim/ring_model.v

else

# Gate level simulation:
SIM_BUILD				= sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DSIM
# Gate-level rings are zero-delay cells without SDF, and a zero-delay loop does not advance simulation
# time: test.py keeps ena low until ring 7 is selected (docs/design_notes.md, "Gate-level simulation").
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_io/verilog/sg13g2_io.v
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v
# The analog ring is a blackbox in the gate-level netlist too: its model and ring_model go in beside it.
VERILOG_SOURCES += $(SRC_DIR)/rings/tt_analog_ring.v
VERILOG_SOURCES += $(PWD)/../sim/ring_model.v
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# Allow sharing configuration between design and testbench via `include`:
COMPILE_ARGS 		+= -I$(SRC_DIR)

# Include the testbench sources:
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL = tb

# List test modules to run, separated by commas and without the .py suffix:
COCOTB_TEST_MODULES = test

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
