#!/usr/bin/env python3
"""Characterise the hand-drawn inverter and emit a Liberty model for it.

    ./run.sh python3 char/characterize.py

LibreLane needs timing for tt_analog_inverter or it cannot synthesise, place or
sign off around the macro. Rather than assert plausible numbers, this sweeps the
real transistor-level netlist in ngspice over the same kind of input-slew x
output-load grid a standard cell library is built on, and writes the measured
delays and transitions into lib/tt_analog_inverter.lib as an NLDM table.

The grid, the units and the measurement thresholds are taken from the PDK's own
sg13g2_stdcell_typ_1p20V_25C.lib so the macro's numbers compose with the
standard cells' rather than being on a different footing:

  * capacitive_load_unit 1 pF, time_unit 1 ns, voltage_unit 1 V
  * delay measured 50% to 50%, transition measured 20% to 80%
  * index_1 = input transition (ns), index_2 = output load (pF)

Input capacitance is measured too, by integrating the current into the gate
over a slow ramp - the value the synthesiser uses to load whatever drives A.
"""

import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "out", "char")
NETLIST = os.path.join(ROOT, "out", "inverter.sim.spice")

# The netlist xschem writes for simulation is flat, with the schematic's own
# net names (A, Y, VDD, VSS) at the top level and a trailing .end. It is
# .include-d and driven directly rather than instantiated as a subcircuit.
LIB = os.path.join(ROOT, "lib", "tt_analog_inverter.lib")

VDD = 1.2
CELL = "tt_analog_inverter"

# The PDK's own 7x7 axes, trimmed to 4x4: the macro is one gate, and a finer
# grid would be spurious precision on a block this simple.
SLEWS = [0.0186, 0.174, 0.6408, 2.5074]      # ns, input transition (20-80%)
LOADS = [0.001, 0.0234, 0.108, 0.3]          # pF, output load

MODELS = os.path.join(os.environ.get("PDK_ROOT", "/foss/pdks"), os.environ.get("PDK", "ihp-sg13g2"), "libs.tech/ngspice/models/cornerMOSlv.lib")


def deck(slew, load, edge):
    """A single-point deck: one ramp on A, measure delay and output transition.

    The ramp is written 20-80%, the same definition the index axis uses, so the
    slew asked for is the slew applied. It is stretched to full swing at both
    ends, which is what a real driver does.
    """
    t_full = slew / 0.6                       # 20-80% -> 0-100%
    t0 = 1.0                                  # settle first
    if edge == "rise":
        v1, v2 = 0.0, VDD
    else:
        v1, v2 = VDD, 0.0
    # Output moves the other way: a rising input gives a falling output.
    out_edge = "fall" if edge == "rise" else "rise"
    lo, hi = (0.2 * VDD, 0.8 * VDD)
    return f"""* {CELL} characterisation: {edge} input, slew={slew}ns load={load}pF
.lib {MODELS} mos_tt

Vdd VDD 0 {VDD}
Vss VSS 0 0
Va A 0 pwl(0 {v1} {t0}n {v1} {t0 + t_full}n {v2} 20n {v2})
.include {NETLIST}
Cl Y 0 {load}p

.control
tran 1p 20n
meas tran delay trig v(A) val={VDD / 2} {edge}=1 targ v(Y) val={VDD / 2} {out_edge}=1
meas tran t20 when v(Y)={lo} {out_edge}=1
meas tran t80 when v(Y)={hi} {out_edge}=1
.endc
"""


def cap_deck():
    """Input capacitance: charge delivered to A over a slow full-swing ramp.

    Slow enough that the gate is quasi-static, so Q/V is the small-signal input
    capacitance the synthesiser wants and not a transient artefact.
    """
    return f"""* {CELL} input capacitance
.lib {MODELS} mos_tt

Vdd VDD 0 {VDD}
Vss VSS 0 0
Va A 0 pwl(0 0 1n 0 101n {VDD} 200n {VDD})
.include {NETLIST}
Cl Y 0 0.01p

.control
tran 10p 150n
let q = integ(-i(Va))
meas tran qtot find q at=101n
.endc
"""


def run(name, text):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".spice")
    with open(path, "w") as fh:
        fh.write(text)
    p = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True,
                       cwd=OUT)
    return p.stdout + p.stderr


def measure(log, name):
    m = re.search(rf"^\s*{name}\s*=\s*([-\d.eE+]+)", log, re.M)
    if not m:
        raise SystemExit(f"ngspice did not report '{name}':\n{log[-2000:]}")
    return float(m.group(1))


def table(edge, what):
    """what: 'delay' or 'transition'. Returns rows[slew][load] in ns."""
    rows = []
    for slew in SLEWS:
        row = []
        for load in LOADS:
            log = run(f"{edge}_{slew}_{load}", deck(slew, load, edge))
            if what == "delay":
                v = measure(log, "delay")
            else:
                v = abs(measure(log, "t80") - measure(log, "t20"))
            row.append(v * 1e9)               # ngspice reports seconds
        rows.append(row)
    return rows


def fmt(rows):
    body = ", \\\n".join(
        '            "' + ", ".join(f"{v:.6g}" for v in row) + '"' for row in rows
    )
    return body


def index(values):
    return ", ".join(f"{v:g}" for v in values)


print("measuring input capacitance ...")
cin = measure(cap_deck_log := run("cin", cap_deck()), "qtot") / VDD * 1e12   # pF
print(f"  Cin = {cin * 1000:.3f} fF")

tables = {}
for edge in ("rise", "fall"):
    for what in ("delay", "transition"):
        print(f"measuring {edge} input {what} ...")
        tables[(edge, what)] = table(edge, what)

# A rising input produces a falling output, so the rising-input sweep fills
# cell_fall/fall_transition. Getting this backwards would make STA optimistic
# on exactly the path that is slowest.
cell_fall, fall_trans = tables[("rise", "delay")], tables[("rise", "transition")]
cell_rise, rise_trans = tables[("fall", "delay")], tables[("fall", "transition")]

os.makedirs(os.path.dirname(LIB), exist_ok=True)
with open(LIB, "w") as fh:
    fh.write(f"""/*
 * Liberty model of the hand-drawn CMOS inverter macro.
 *
 * GENERATED by analog/char/characterize.py from the transistor-level netlist -
 * do not edit. Every number below was measured in ngspice on out/inverter.sim.spice
 * at the typical corner, 1.2 V, 25 C, on the same axes and with the same
 * thresholds the PDK's own standard-cell library uses.
 */
library (tt_analog_inverter) {{
  comment : "Characterised from layout-matching netlist; see analog/char/";
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
  default_max_transition : {max(SLEWS)};

  /* No operating_conditions group. OpenSTA derives its corner ("scene") names
     from the libraries it reads, and a macro library that declares its own
     conditions makes it look for a scene that the PDK's corners do not define:
     "_b01c32d530560000_p_Scene is not the name of a scene", and every STA
     corner fails before placement. The macro is read into whichever corner the
     flow is analysing, which is what the "*" key in MACROS.lib asks for. */

  voltage_map (VPWR, {VDD});
  voltage_map (VGND, 0);

  lu_table_template (inv_4x4) {{
    variable_1 : input_net_transition;
    variable_2 : total_output_net_capacitance;
    index_1 ("{index(SLEWS)}");
    index_2 ("{index(LOADS)}");
  }}

  cell ({CELL}) {{
    area : {20.16 * 22.68:.4f};
    is_macro_cell : true;
    dont_touch : true;
    dont_use : true;

    pg_pin (VPWR) {{ voltage_name : VPWR; pg_type : primary_power; }}
    pg_pin (VGND) {{ voltage_name : VGND; pg_type : primary_ground; }}

    pin (A) {{
      direction : "input";
      related_power_pin : VPWR;
      related_ground_pin : VGND;
      capacitance : {cin:.6f};
      max_transition : {max(SLEWS)};
    }}

    pin (Y) {{
      direction : "output";
      function : "!(A)";
      related_power_pin : VPWR;
      related_ground_pin : VGND;
      max_capacitance : {max(LOADS)};
      timing () {{
        related_pin : "A";
        timing_sense : negative_unate;
        timing_type : combinational;
        cell_rise (inv_4x4) {{
          values ( \\
{fmt(cell_rise)} \\
          );
        }}
        rise_transition (inv_4x4) {{
          values ( \\
{fmt(rise_trans)} \\
          );
        }}
        cell_fall (inv_4x4) {{
          values ( \\
{fmt(cell_fall)} \\
          );
        }}
        fall_transition (inv_4x4) {{
          values ( \\
{fmt(fall_trans)} \\
          );
        }}
      }}
    }}
  }}
}}
""")
print(f"wrote {LIB}")
