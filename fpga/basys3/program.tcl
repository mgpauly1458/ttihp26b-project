# Load the bitstream onto an attached Basys3 over JTAG (volatile; lost on power
# cycle). Usage:  vivado -mode batch -source program.tcl
set here [file normalize [file dirname [info script]]]
set bit  $here/build/tt_basys3_top.bit

if {![file exists $bit]} {
    puts "ERROR: $bit not found. Run 'make' first."
    exit 1
}

open_hw_manager
connect_hw_server
open_hw_target
current_hw_device [lindex [get_hw_devices xc7a35t_0] 0]
set_property PROGRAM.FILE $bit [current_hw_device]
program_hw_devices [current_hw_device]
puts "Programmed $bit"
close_hw_manager
