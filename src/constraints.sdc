# constraints.sdc -- tile timing constraints on top of LibreLane's base.sdc (plan: docs/constraints.md)
# base.sdc constrains clk and the pins and knows nothing about the eight rings. Here: every ring output,
# the selected ring (after the mux) and the divided ring (after the tap mux) are clocks, all asynchronous
# to clk and to each other; the ring loops are not timing paths.
# The divided ring is constrained to 250 MHz, the instrument's one usage rule: a ring faster than that
# is measured at tap 1 or higher; tap 0 is for slow rings.
# The pin names are stable across synthesis because they belong to (* keep *) cell instances: each
# standard-cell ring's u_out buffer, the analog macro, and u_selout / u_divout in ring_mux and ring_divider.

source $::env(SCRIPTS_DIR)/base.sdc

# ---------------------------------------------------------------- ring clocks
# Period = fastest expected with margin. Simulated: 350 MHz for the 21-stage min rings (2.86 ns), ~700 MHz
# for the 11-stage ring; the analog macro at code 255 is 332 MHz typical, 544 MHz fast corner, cold, 1.32 V
# (analog/verify/ring.py). Fast-corner factor ~1.6 on the standard-cell rings too: 1.6 / 0.8 / 1.6 ns,
# and the selected-ring clock takes the fastest of them.
set ring_clocks [list \
    ring0 1.6 [get_pins u_rings.u_ring0.u_out/X] \
    ring1 1.6 [get_pins u_rings.u_ring1.u_out/X] \
    ring2 1.6 [get_pins u_rings.u_ring2.u_out/X] \
    ring3 1.6 [get_pins u_rings.u_ring3.u_out/X] \
    ring4 1.6 [get_pins u_rings.u_ring4.u_out/X] \
    ring5 0.8 [get_pins u_rings.u_ring5.u_out/X] \
    ring6 1.6 [get_pins u_rings.u_ring6.u_out/X] \
    ring7 1.6 [get_pins u_rings.u_ring7/clk_out] \
    ring_sel 0.8 [get_pins u_mux.u_selout/X] \
    div_ring 4.0 [get_pins u_div.u_divout/X] \
]

set groups [list -group [get_clocks $clock_port]]
foreach {name period pin} $ring_clocks {
    create_clock -name $name -period $period $pin
    lappend groups -group [get_clocks $name]
}

# base.sdc sets every clock propagated after CTS; include the new ones.
set_propagated_clock [all_clocks]

# clk, the ring sources, the selected ring and the divided ring are mutually asynchronous: no path between
# them is timed. The cdc_sync two-flop synchronisers are the only crossings and are false by construction.
# The divider's ripple stages q2..q7 are each clocked by the previous stage and left unconstrained (each
# runs at half the rate of q1, which is constrained at the selected ring's period).
set_clock_groups -asynchronous {*}$groups

# ------------------------------------------------------------------ the loops
# Each standard-cell ring is a combinational loop through its NAND. Break it at the NAND's feedback input
# so the choice is recorded here rather than left to OpenSTA and a warning.
foreach r {0 1 2 3 4 5 6} {
    set nand [get_cells -quiet u_rings.u_ring$r.u_en]
    if { [llength $nand] > 0 } {
        set_disable_timing $nand -from B -to Y
    }
}
