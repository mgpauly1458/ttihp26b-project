# SPDX-FileCopyrightText: © 2026 Maxwell Pauly
# SPDX-License-Identifier: Apache-2.0

"""cocotb bench for the ring oscillator meter: the CI smoke test.

Thorough verification is sim/ (`make test`) and the sweep (`make sweep`). This drives the tile
through its pins as a host would: ID readback, one measurement on ring 7 checked against the
reciprocal formula, and a dead-slow code that must time out rather than hang.

Rings are sim/ring_model.v instances (-DSIM), so the answer is exact: ring 7, the analog macro's
model, runs at 164 MHz at code 255 and 2.0 MHz at code 0 (its post-layout simulation).

GATES=yes runs the same tests on the hardened netlist. There the seven standard-cell rings are
zero-delay cells, and a zero-delay ring loop never advances simulation time (iverilog hangs), so
`ena` (which gates every ring enable) stays low until ring 7 is selected and no other slot is
ever selected. Ring 7 is the hard macro: a blackbox with the model inside at RTL and gate level.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer

# Register map, mirroring src/regfile.v
A_TRIM, A_RING_SEL, A_TAP_SEL, A_TARGET_L, A_TARGET_H, A_TIMEOUT_L, A_TIMEOUT_H, A_CONTROL = range(8)
R_STATUS, R_RESULT0, R_RESULT1, R_RESULT2, R_RESULT3, R_TRIM, R_SEL, R_ID = range(8)
ST_DONE, ST_BUSY, ST_TIMEOUT, ST_IGNORED = 1, 2, 4, 8

T_REF_NS = 20          # 50 MHz, as declared in info.yaml
F_REF = 1e9 / T_REF_NS
F_RING7_MAX = 164e6    # src/rings/tt_analog_ring.v, F_MAX_HZ at code 255


def ui(addr=0, we=0, rsel=0):
    return (rsel << 4) | (we << 3) | addr


async def host_write(dut, addr, data):
    """ADDR/WDATA, WE high 4 clocks, WE low 4 (regfile.v protocol)."""
    await Timer(1, units="ns")                    # off the clock edge
    dut.uio_in.value = data
    dut.ui_in.value = ui(addr=addr, we=1)
    await ClockCycles(dut.clk, 4)
    await Timer(1, units="ns")
    dut.ui_in.value = ui(addr=addr, we=0)
    await ClockCycles(dut.clk, 4)


async def host_read(dut, rsel):
    await Timer(1, units="ns")
    dut.ui_in.value = ui(rsel=rsel)
    await ClockCycles(dut.clk, 3)
    await Timer(1, units="ns")
    return int(dut.uo_out.value)


async def wait_done(dut, max_polls=100000):
    for _ in range(max_polls):
        status = await host_read(dut, R_STATUS)
        if status & ST_DONE:
            return status
    raise AssertionError("measurement never finished")


async def read_result(dut):
    b = [await host_read(dut, r) for r in (R_RESULT0, R_RESULT1, R_RESULT2, R_RESULT3)]
    return b[0] | (b[1] << 8) | (b[2] << 16) | (b[3] << 24)


async def measure(dut, ring, code, tap, n, timeout):
    await host_write(dut, A_RING_SEL, ring)
    await host_write(dut, A_TAP_SEL, tap)
    await host_write(dut, A_TRIM, code)
    await host_write(dut, A_TARGET_L, n & 0xFF)
    await host_write(dut, A_TARGET_H, n >> 8)
    await host_write(dut, A_TIMEOUT_L, timeout & 0xFF)
    await host_write(dut, A_TIMEOUT_H, timeout >> 8)
    await host_write(dut, A_CONTROL, 1)
    status = await wait_done(dut)
    return status, await read_result(dut)


async def start(dut):
    # ena low through reset: no ring is enabled whatever the (reset, or X) ring select says. See the header.
    dut.ena.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await Timer(1, units="ns")
    cocotb.start_soon(Clock(dut.clk, T_REF_NS, units="ns").start())
    await ClockCycles(dut.clk, 5)
    await Timer(5, units="ns")                    # release reset between edges
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 3)
    await host_write(dut, A_RING_SEL, 7)          # the macro's slot, then
    await Timer(1, units="ns")
    dut.ena.value = 1                             # let the rings run
    await ClockCycles(dut.clk, 3)


@cocotb.test()
async def test_id(dut):
    """The ID byte reads back."""
    await start(dut)
    assert await host_read(dut, R_ID) == 0xA5


@cocotb.test()
async def test_one_measurement(dut):
    """Ring 7 at code 255 (164 MHz), tap 3, N=200: count 488 +/-1."""
    await start(dut)
    status, count = await measure(dut, ring=7, code=255, tap=3, n=200, timeout=16000)
    assert not (status & ST_TIMEOUT), "unexpected timeout"
    expected = 200 * 8 * F_REF / F_RING7_MAX
    dut._log.info(f"count {count}, expected {expected:.1f}")
    assert abs(count - expected) <= 1


@cocotb.test()
async def test_slow_code_times_out(dut):
    """Code 0 (2.0 MHz): 200 periods at tap 3 take 800 us, timeout is 40 us. timeout_error, then recovery."""
    await start(dut)
    status, _ = await measure(dut, ring=7, code=0, tap=3, n=200, timeout=2000)
    assert status & ST_TIMEOUT
    assert status & ST_DONE
    # and the instrument still works afterwards
    status, count = await measure(dut, ring=7, code=255, tap=3, n=200, timeout=16000)
    assert not (status & ST_TIMEOUT)
    assert abs(count - 200 * 8 * F_REF / F_RING7_MAX) <= 1
