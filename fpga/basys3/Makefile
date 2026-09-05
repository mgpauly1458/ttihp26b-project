# Basys3 prototype build.
#
#   make lint      syntax/elaboration check with Icarus (no Vivado needed)
#   make bit       synthesise, place, route and write the bitstream
#   make prog      load the bitstream onto an attached board over JTAG
#   make clean     remove build outputs
#
# Vivado must be on PATH: source /tools/Xilinx/Vivado/<version>/settings64.sh

VIVADO ?= vivado
TOP    := tt_basys3_top
BIT    := build/$(TOP).bit
SRCS   := tt_basys3_top.v ../../src/project.v sim/xil_stubs.v

.PHONY: all lint bit prog clean

all: bit

lint:
	iverilog -g2012 -Wall -t null -s $(TOP) $(SRCS)
	@echo "lint: OK"

bit: $(BIT)

$(BIT): $(SRCS) basys3.xdc build.tcl
	@mkdir -p build
	$(VIVADO) -mode batch -nojournal -log build/vivado.log -source build.tcl

prog: $(BIT)
	$(VIVADO) -mode batch -nojournal -nolog -source program.tcl

clean:
	rm -rf build .Xil vivado*.jou vivado*.log
