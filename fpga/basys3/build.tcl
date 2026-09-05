# Non-project (batch) Vivado build for the Basys3 Tiny Tapeout prototype.
# Usage:  vivado -mode batch -source build.tcl
# Everything lands in ./build; nothing is written outside this directory.

set part      "xc7a35tcpg236-1"
set top       "tt_basys3_top"
set here      [file normalize [file dirname [info script]]]
set proj_root [file normalize $here/../..]
set outdir    $here/build

# 100 MHz >> CLK_DIV_LOG2 is the clock the design under test sees.
# 24 -> ~6 Hz (watchable on the LEDs). 0 -> full 100 MHz.
# This value is also used to emit the matching generated-clock constraint below,
# so change it here rather than editing the Verilog default.
set CLK_DIV_LOG2 24

file mkdir $outdir

# ---------------------------------------------------------------- sources
# The design under test, straight out of src/. Keep this list in sync with the
# source_files entry in info.yaml.
set dut_sources [list \
    $proj_root/src/project.v \
]

read_verilog -sv $dut_sources
read_verilog $here/tt_basys3_top.v
read_xdc $here/basys3.xdc

# ---------------------------------------------------------------- synthesis
synth_design -top $top -part $part -generic CLK_DIV_LOG2=$CLK_DIV_LOG2

# Tell the timing engine about the divided clock driving the DUT. Without this
# the DUT's paths are unconstrained and timing reports are meaningless.
if {$CLK_DIV_LOG2 > 0} {
    create_generated_clock -name clk_user \
        -source [get_ports clk] \
        -divide_by [expr {int(pow(2, $CLK_DIV_LOG2))}] \
        [get_pins bufg_user/O]
}

# The manual single-step path and the free-running divider are unrelated in time.
set_false_path -from [get_ports btn*]
set_false_path -from [get_ports sw*]
set_false_path -to   [get_ports {led* seg* an dp}]

# ------------------------------------------------------- place, route, write
opt_design
place_design
phys_opt_design
route_design

report_timing_summary -file $outdir/timing_summary.rpt
report_utilization    -file $outdir/utilization.rpt
report_drc            -file $outdir/drc.rpt

write_bitstream -force $outdir/$top.bit

# Fail loudly rather than shipping a bitstream that misses timing.
set wns [get_property SLACK [get_timing_paths -delay_type max]]
puts "=========================================="
puts " Bitstream: $outdir/$top.bit"
puts " Worst negative slack: $wns ns"
puts "=========================================="
if {$wns < 0} {
    puts "ERROR: design does not meet timing."
    exit 1
}
