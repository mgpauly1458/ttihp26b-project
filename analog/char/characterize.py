#!/usr/bin/env python3
"""Characterise the ring oscillator macro and emit its Liberty model.

    ./run.sh python3 char/characterize.py

LibreLane needs a Liberty description of the macro to synthesise, place and
sign off around it: pin directions, the capacitance every input presents to
the cell that drives it, and what the output can drive. Rather than assert
those numbers, this measures them in ngspice on spice/tt_analog_ring.spice,
the same finger-by-finger netlist LVS checks the layout against.

  * Input capacitance of each code bit and of enable: charge delivered over
    a slow full-swing ramp, Q/V. The code bits are the gates of 2^k long
    DAC fingers, so code[7] is over a picofarad - the driver on the tile
    side has to be sized for it, and this is where the tool learns that.
  * Output: clk_out's rise/fall transition against load, measured on the
    running oscillator. There is no timing arc: the output is a free-running
    clock, and the tile must declare it as one (create_clock on the macro
    pin) rather than time a path through the macro.

Units and thresholds follow the PDK's own standard-cell library so the
numbers compose: 1 pF, 1 ns, 50 % delay, 20-80 % transition.
"""

import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "out", "char")
NETLIST = os.path.join(ROOT, "spice", "tt_analog_ring.spice")
LIB = os.path.join(ROOT, "lib", "tt_analog_ring.lib")
MODELS = os.path.join(os.environ.get("PDK_ROOT", "/foss/pdks"),
                      os.environ.get("PDK", "ihp-sg13g2"),
                      "libs.tech/ngspice/models/cornerMOSlv.lib")

VDD = 1.2
CELL = "tt_analog_ring"
INPUTS = [f"code[{k}]" for k in range(8)] + ["enable"]
LOADS = [0.001, 0.0234, 0.05, 0.108]          # pF: the PDK axis, trimmed to what a clock net sees
AREA_UM2 = None                                  # filled from the LEF


def header(extra=""):
    ports = " ".join(f"code[{k}]" for k in range(8))
    return f"""* {CELL} characterisation
.lib {MODELS} mos_tt
.include {NETLIST}
Vdd VPWR 0 {VDD}
{extra}
Xdut {ports} enable clk_out VPWR 0 {CELL}
"""


def cap_deck(pin):
    """Charge into `pin` over a slow ramp; every other input held at its
    resting level (code bits low, enable high). Slow enough that the gate is
    quasi-static: Q/V is then the small-signal input capacitance."""
    srcs = []
    for p in INPUTS:
        if p == pin:
            srcs.append(f"Vin {p} 0 pwl(0 0 1n 0 201n {VDD} 300n {VDD})")
        else:
            srcs.append(f"V{p.replace('[', '').replace(']', '')} {p} 0 {VDD if p == 'enable' else 0}")
    return header("\n".join(srcs)) + f"""Cl clk_out 0 0.01p
.control
tran 50p 250n
let q = integ(-i(Vin))
meas tran qtot find q at=201n
.endc
.end
"""


def out_deck(load):
    """The oscillator running at mid code into `load`; transition times of
    clk_out from the 20-80 % crossings of one edge each way."""
    srcs = [f"V{p.replace('[', '').replace(']', '')} {p} 0 {VDD if p in ('enable', 'code[7]') else 0}"
            for p in INPUTS]
    return header("\n".join(srcs)) + f"""Cl clk_out 0 {load}p
.control
tran 10p 400n
meas tran r20 when v(clk_out)={0.2 * VDD} rise=LAST
meas tran r80 when v(clk_out)={0.8 * VDD} rise=LAST
meas tran f80 when v(clk_out)={0.8 * VDD} fall=LAST
meas tran f20 when v(clk_out)={0.2 * VDD} fall=LAST
meas tran ta when v(clk_out)={0.5 * VDD} rise=1 from=200n
meas tran tb when v(clk_out)={0.5 * VDD} rise=5 from=200n
.endc
.end
"""


def run(name, text):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".spice")
    with open(path, "w") as fh:
        fh.write(text)
    p = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True, cwd=OUT)
    return p.stdout + p.stderr


def measure(log, name):
    m = re.search(rf"^\s*{name}\s*=\s*([-\d.eE+]+)", log, re.M)
    if not m:
        raise SystemExit(f"ngspice did not report '{name}':\n{log[-2000:]}")
    return float(m.group(1))


def lef_size():
    with open(os.path.join(ROOT, "macro", f"{CELL}.lef")) as fh:
        m = re.search(r"SIZE\s+([\d.]+)\s+BY\s+([\d.]+)", fh.read())
    return float(m.group(1)) * float(m.group(2))


def main():
    with ThreadPoolExecutor(8) as ex:
        cap_logs = list(ex.map(lambda p: run("cin_" + re.sub(r"\W", "", p), cap_deck(p)), INPUTS))
        out_logs = list(ex.map(lambda l: run(f"out_{l}", out_deck(l)), LOADS))
    cin = {}
    for p, log in zip(INPUTS, cap_logs):
        cin[p] = measure(log, "qtot") / VDD * 1e12          # pF
        print(f"  Cin({p}) = {cin[p] * 1000:.1f} fF")
    rise, fall, freq = [], [], []
    for load, log in zip(LOADS, out_logs):
        rise.append((measure(log, "r80") - measure(log, "r20")) * 1e9)
        fall.append((measure(log, "f20") - measure(log, "f80")) * 1e9)
        freq.append(4 / (measure(log, "tb") - measure(log, "ta")))
        print(f"  load {load} pF: rise {rise[-1]:.4f} ns, fall {fall[-1]:.4f} ns, f = {freq[-1] / 1e6:.1f} MHz")

    area = lef_size()
    idx = ", ".join(f"{v:g}" for v in LOADS)
    fmt = lambda vals: ", ".join(f"{v:.6g}" for v in vals)
    os.makedirs(os.path.dirname(LIB), exist_ok=True)
    pins = "\n".join(f"""      pin (code[{k}]) {{
        direction : "input";
        related_power_pin : VPWR;
        related_ground_pin : VGND;
        capacitance : {cin[f'code[{k}]']:.6f};
      }}""" for k in range(8))
    with open(LIB, "w") as fh:
        fh.write(f"""/*
 * Liberty model of the current-starved ring oscillator macro.
 *
 * GENERATED by analog/char/characterize.py from the transistor-level netlist -
 * do not edit. Input capacitances and the output's drive were measured in
 * ngspice on spice/{CELL}.spice at the typical corner, 1.2 V, 27 C.
 *
 * clk_out has NO timing arc on purpose: it is a free-running oscillator. The
 * tile must create_clock on it (see analog/README.md); a path through the
 * macro is not a thing STA can time.
 */
library ({CELL}) {{
  comment : "Characterised from the layout-matching netlist; see analog/char/";
  delay_model : table_lookup;
  capacitive_load_unit (1, pf);
  time_unit : "1ns";
  voltage_unit : "1V";
  current_unit : "1uA";
  pulling_resistance_unit : "1kohm";
  leakage_power_unit : "1pW";
  nom_process : 1;
  nom_temperature : 25;
  nom_voltage : {VDD};
  input_threshold_pct_rise : 50;
  input_threshold_pct_fall : 50;
  output_threshold_pct_rise : 50;
  output_threshold_pct_fall : 50;
  slew_lower_threshold_pct_rise : 20;
  slew_upper_threshold_pct_rise : 80;
  slew_lower_threshold_pct_fall : 20;
  slew_upper_threshold_pct_fall : 80;
  slew_derate_from_library : 1;
  default_max_transition : 2.5;

  /* No operating_conditions group: OpenSTA derives its corner names from the
     libraries it reads, and a macro library declaring its own makes every
     corner fail before placement. See the inverter macro on `main`. */

  voltage_map (VPWR, {VDD});
  voltage_map (VGND, 0);

  type (bus8) {{
    base_type : array;
    data_type : bit;
    bit_width : 8;
    bit_from : 7;
    bit_to : 0;
  }}

  cell ({CELL}) {{
    area : {area:.4f};
    is_macro_cell : true;
    dont_touch : true;
    dont_use : true;

    pg_pin (VPWR) {{ voltage_name : VPWR; pg_type : primary_power; }}
    pg_pin (VGND) {{ voltage_name : VGND; pg_type : primary_ground; }}

    /* The DAC code. Bit k is the gate of 2^k long unit transistors, so the
       capacitance doubles per bit; the tile's driver has to be sized for
       code[7]. Slow edges are harmless - it is a DC control. */
    bus (code) {{
      bus_type : bus8;
      direction : "input";
      related_power_pin : VPWR;
      related_ground_pin : VGND;
{pins}
    }}

    pin (enable) {{
      direction : "input";
      related_power_pin : VPWR;
      related_ground_pin : VGND;
      capacitance : {cin['enable']:.6f};
    }}

    /* Free-running clock output. Measured on the running ring at code 128:
       {freq[0] / 1e6:.0f} MHz into {LOADS[0]} pF, {freq[-1] / 1e6:.0f} MHz into {LOADS[-1]} pF.
       20-80 % transitions against load (ns): rise {fmt(rise)}; fall {fmt(fall)}
       at loads {idx} pF. */
    pin (clk_out) {{
      direction : "output";
      related_power_pin : VPWR;
      related_ground_pin : VGND;
      max_capacitance : {LOADS[-1]};
      max_transition : {max(rise + fall) * 1.5:.4f};
    }}
  }}
}}
""")
    print(f"wrote {LIB}")


if __name__ == "__main__":
    main()
