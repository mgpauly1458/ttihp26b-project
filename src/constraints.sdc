# constraints.sdc -- timing constraints for the tile, on top of Tiny Tapeout's
#
# LibreLane's base.sdc constrains the reference clock `clk` and the pins. It
# knows nothing about the eight ring oscillators, each of which is a clock
# source of its own, so left alone STA would either time the ring loops or
# ignore the whole ring domain. This file sources the base and then tells STA
# what docs/constraints.md planned:
#
#   * every ring output is a clock, with the period of the fastest that ring
#     can plausibly run;
#   * the selected ring, after the mux, is the clock of the divider's first
#     flop (the fastest flop in the design);
#   * the divided ring, after the tap mux, is the clock of the window logic
#     in measure_core, and it is constrained to 250 MHz. That is the one
#     usage rule of the instrument: a ring faster than 250 MHz must be
#     measured through tap 1 or higher. The tap-0 path is for slow rings.
#   * all of these are asynchronous to `clk` and to each other;
#   * the ring loops themselves are not timing paths.
#
# The pins named below are stable across synthesis because they belong to
# `(* keep *)` cell instances: the output buffer of each standard-cell ring,
# the analog macro, and the two named buffers in ring_mux and ring_divider.

source $::env(SCRIPTS_DIR)/base.sdc

# ---------------------------------------------------------------- ring clocks
# Period = fastest expected, with margin: simulated 350 MHz for the 21-stage
# minimum-size rings (2.86 ns), ~700 MHz for the 11-stage ring; the analog
# macro at code 255 is 332 MHz typical and 544 MHz at the fast corner, cold,
# 1.32 V (analog/verify/ring.py). Fast-corner factor ~1.6 on the standard
# cell rings too, so 1.6 ns / 0.8 ns / 1.6 ns, and the selected-ring clock
# takes the fastest of them.
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

# clk, the ring sources, the selected ring and the divided ring are mutually
# asynchronous: no path between them is a timing path. The two-flop
# synchronisers in cdc_sync are the only crossings and are false by
# construction; the divider's ripple stages q2..q7 are each clocked by the
# previous stage and are left unconstrained (each runs at half the rate of
# q1, which is constrained at the selected ring's period).
set_clock_groups -asynchronous {*}$groups

# ------------------------------------------------------------------ the loops
# Each standard-cell ring is a combinational loop through its NAND. OpenSTA
# would break the loop somewhere on its own; break it at the NAND's feedback
# input so the choice is recorded here rather than in a warning.
foreach r {0 1 2 3 4 5 6} {
    set nand [get_cells -quiet u_rings.u_ring$r.u_en]
    if { [llength $nand] > 0 } {
        set_disable_timing $nand -from B -to Y
    }
}
