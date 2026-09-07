# SPDX-FileCopyrightText: © 2026 Maxwell Pauly
# SPDX-License-Identifier: Apache-2.0

"""Cocotb bench for the mixed-signal hello world.

The analog inverter is a hard macro, so in simulation it is the behavioural
model in src/tt_analog_inverter.v (compiled in by -DSIM) that responds. What
these tests can therefore prove is that the tile is *wired* correctly - that
ui_in[0] reaches the macro, that its output reaches the pins and the flop, and
that the logic reference agrees with it. Whether the silicon inverter switches
at the right threshold is a question for ngspice, and lives in analog/.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer

# uo_out bit assignments, mirroring src/project.v and the pinout in info.yaml.
Y_COMB, Y_REG, Y_REF, MISMATCH = 0, 1, 2, 3


async def drive(dut, a):
    """Apply a new value to ui_in[0], between clock edges.

    cocotb's ClockCycles returns on an edge, so assigning straight afterwards
    puts the data change at the same instant as CLK. The gate-level flop's
    $setuphold check fires, its notifier goes X, and uo_out[1] is X from then
    on. Half a period away from the edge is the honest place to change an
    input, and it is what real stimulus does.
    """
    await Timer(5, units="ns")
    dut.ui_in.value = a


def SETTLE():
    """Wait for combinational logic to settle.

    Long enough for the gate-level cells' path delays, which are real (the PDK
    models carry specify blocks) and are what a 1ns wait was too short for -
    the RTL run passed while the same test read a stale uo_out under GATES=yes.
    Still far shorter than the 20ns clock, so no edge is crossed.
    """
    return Timer(5, units="ns")


def bit(dut, n):
    """One bit of uo_out.

    Read bit by bit rather than int(uo_out.value): in gate-level simulation a
    single X anywhere in the byte makes the whole conversion raise, and a test
    that only cares about bit 0 should not fail because of bit 1. uo_out is
    declared [7:0], so the LogicArray indexes by bit number directly.
    """
    value = dut.uo_out.value[n]
    assert value in ("0", "1"), f"uo_out[{n}] is '{value}', not a logic level"
    return int(value)


async def start(dut):
    dut._log.info("start")

    # Drive the inputs to known levels and let reset settle BEFORE the clock
    # starts. Starting the clock in the same delta as the first assignment puts
    # a CLK edge and the x->0 transition of RESET_B at the same instant, which
    # trips the gate-level flop's $width/$recrem checks: its notifier goes X and
    # Q never recovers, so uo_out[1] reads X for the whole run.
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await Timer(1, units="ns")

    clock = Clock(dut.clk, 20, units="ns")   # 50 MHz, as declared in info.yaml
    cocotb.start_soon(clock.start())
    await ClockCycles(dut.clk, 5)

    # Release reset between edges, not on one. The PDK's gate-level flop model
    # carries a $recrem check, and deasserting RESET_B at the same instant as a
    # rising CLK trips it: the notifier goes X and Q stays X for the rest of the
    # simulation. The RTL model does not care, so this only shows up under
    # `make GATES=yes`.
    await Timer(5, units="ns")
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)


@cocotb.test()
async def test_combinational_inversion(dut):
    """The macro's output tracks ~ui_in[0] on uo_out[0]."""
    await start(dut)

    for a in (0, 1, 0, 1):
        await drive(dut, a)
        await SETTLE()                       # settle, no clock edge involved
        assert bit(dut, Y_COMB) == (not a), \
            f"uo_out[0] should be {int(not a)} for ui_in[0]={a}"


@cocotb.test()
async def test_logic_reference_agrees(dut):
    """The standard-cell reference and the macro never disagree.

    uo_out[3] is the XOR of the two. On silicon it is the interesting pin: it
    goes high if the hand-drawn inverter does not do what the logic says it
    should.
    """
    await start(dut)

    for a in (0, 1):
        await drive(dut, a)
        await SETTLE()
        assert bit(dut, Y_REF) == (not a)
        assert bit(dut, MISMATCH) == 0, "analog and logic answers disagree"


@cocotb.test()
async def test_registered_output(dut):
    """uo_out[1] is the macro's output one clock edge late."""
    await start(dut)

    await drive(dut, 1)
    await ClockCycles(dut.clk, 2)
    assert bit(dut, Y_REG) == 0, "1 in should register as 0 out"

    await drive(dut, 0)
    await ClockCycles(dut.clk, 2)
    assert bit(dut, Y_REG) == 1, "0 in should register as 1 out"


@cocotb.test()
async def test_reset_clears_the_register(dut):
    """rst_n low forces the registered output low, whatever the input is."""
    await start(dut)

    await drive(dut, 0)                       # would otherwise register a 1
    await ClockCycles(dut.clk, 2)
    assert bit(dut, Y_REG) == 1

    await Timer(5, units="ns")                # off the edge, as above
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    assert bit(dut, Y_REG) == 0, "reset should clear the register"


@cocotb.test()
async def test_bidirectionals_are_inputs(dut):
    """Nothing drives the uio pins: oe is held low and the outputs at zero."""
    await start(dut)
    assert int(dut.uio_oe.value) == 0
    assert int(dut.uio_out.value) == 0
