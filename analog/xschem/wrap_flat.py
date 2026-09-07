#!/usr/bin/env python3
"""Wrap xschem's flat LVS netlist of tt_analog_ring in a .subckt with the
port order the layout uses, so KLayout can compare it with the GDS.

    python3 xschem/wrap_flat.py out/tt_analog_ring.spice out/tt_analog_ring.sch.lvs.spice
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
ports = [f"code[{k}]" for k in range(8)] + ["enable", "clk_out", "VPWR", "VGND"]
body = [l for l in open(src) if l.strip() and not l.startswith("*") and not l.startswith(".end")]
with open(dst, "w") as fh:
    fh.write("* tt_analog_ring, flat netlist from the xschem schematic (make lvs-sch)\n")
    fh.write(".subckt tt_analog_ring " + " ".join(ports) + "\n")
    fh.writelines(body)
    fh.write(".ends\n")
print("wrote", dst, len(body), "devices")
