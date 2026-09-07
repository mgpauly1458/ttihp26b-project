"""Print what did not match in a KLayout LVS run.

    klayout -b -r analog/layout/lvs_diff.py -rd db=out/lvs/<cell>.lvsdb

Walks the cross-reference of the .lvsdb and lists every net and device that
has no partner or only a partial match, with the layout-side location, so
the mismatch can be found in the GDS instead of read out of a 300-device
netlist by eye.
"""
import pya

path = globals().get("db", "out/lvs/tt_analog_ring.lvsdb")
lvs = pya.LayoutVsSchematic()
lvs.read(path)
xref = lvs.xref()
if xref is None:
    raise SystemExit("no cross-reference in " + path)

status_name = {pya.NetlistCrossReference.Match: "match",
               pya.NetlistCrossReference.NoMatch: "NOMATCH",
               pya.NetlistCrossReference.Mismatch: "MISMATCH",
               pya.NetlistCrossReference.MatchWithWarning: "warning",
               pya.NetlistCrossReference.Skipped: "skipped"}


def desc_net(n):
    if n is None:
        return "-"
    return f"{n.expanded_name()} ({n.pin_count()}p {n.terminal_count()}t)"


def desc_dev(d):
    if d is None:
        return "-"
    terms = []
    for t in d.each_terminal():
        terms.append(f"{t.terminal_def().name}={t.net().expanded_name() if t.net() else '?'}")
    dc = d.device_class() if callable(d.device_class) else d.device_class
    p = dc.name
    w = d.parameter("W") if dc.has_parameter("W") else ""
    return f"{d.expanded_name()} {p} W={w} [{' '.join(terms)}] @({d.trans.disp.x:.2f},{d.trans.disp.y:.2f})"


for cp in xref.each_circuit_pair():
    print(f"circuit {cp.first.name if cp.first else '-'} / {cp.second.name if cp.second else '-'}: {status_name.get(cp.status, cp.status)}")
    print("-- nets (layout | schematic)")
    for np_ in xref.each_net_pair(cp):
        if np_.status != pya.NetlistCrossReference.Match:
            print(f"   {status_name.get(np_.status, np_.status):9} {desc_net(np_.first):40} | {desc_net(np_.second)}")
    print("-- devices (layout | schematic)")
    for dp in xref.each_device_pair(cp):
        if dp.status != pya.NetlistCrossReference.Match:
            print(f"   {status_name.get(dp.status, dp.status):9} {desc_dev(dp.first)}\n             | {desc_dev(dp.second)}")
    print("-- pins")
    for pp in xref.each_pin_pair(cp):
        if pp.status != pya.NetlistCrossReference.Match:
            print(f"   {status_name.get(pp.status, pp.status):9} {pp.first.expanded_name() if pp.first else '-'} | {pp.second.expanded_name() if pp.second else '-'}")
