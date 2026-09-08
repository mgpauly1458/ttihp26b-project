"""Print the nets, devices and pins that did not match in a KLayout LVS run, with layout-side locations.

    klayout -b -r analog/layout/lvs_diff.py -rd db=out/lvs/<cell>.lvsdb      (or: make lvs-diff)
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


def name_of(o):
    """name of a pya object, exposed as a property or a method depending on the build"""
    v = getattr(o, "name", None)
    if isinstance(v, str):
        return v
    try:
        return o().name
    except Exception:
        return str(v() if callable(v) else v)


def v(x):
    """call it if this build exposes it as a method"""
    return x() if callable(x) else x


def desc_net(n):
    if n is None:
        return "-"
    return f"{n.expanded_name()} ({v(n.pin_count)}p {v(n.terminal_count)}t)"


def desc_dev(d):
    if d is None:
        return "-"
    terms = []
    dc = v(d.device_class)
    for td in v(dc.terminal_definitions):
        net = d.net_for_terminal(v(td.id))
        terms.append(f"{name_of(td)}={net.expanded_name() if net else '?'}")
    p = name_of(d.device_class)
    try:
        w = d.parameter("W")
    except Exception:
        w = ""
    return f"{d.expanded_name()} {p} W={w} [{' '.join(terms)}] @({v(d.trans).disp.x:.2f},{v(d.trans).disp.y:.2f})"


for cp in xref.each_circuit_pair():
    print(f"circuit {name_of(v(cp.first)) if v(cp.first) else '-'} / {name_of(v(cp.second)) if v(cp.second) else '-'}: {status_name.get(v(cp.status), v(cp.status))}")
    print("-- nets (layout | schematic)")
    for np_ in xref.each_net_pair(cp):
        if v(np_.status) != pya.NetlistCrossReference.Match:
            print(f"   {status_name.get(v(np_.status), v(np_.status)):9} {desc_net(v(np_.first)):40} | {desc_net(v(np_.second))}")
    print("-- devices (layout | schematic)")
    for dp in xref.each_device_pair(cp):
        if v(dp.status) != pya.NetlistCrossReference.Match:
            print(f"   {status_name.get(v(dp.status), v(dp.status)):9} {desc_dev(v(dp.first))}\n             | {desc_dev(v(dp.second))}")
    print("-- pins")
    for pp in xref.each_pin_pair(cp):
        if v(pp.status) != pya.NetlistCrossReference.Match:
            print(f"   {status_name.get(v(pp.status), v(pp.status)):9} {v(pp.first).expanded_name() if v(pp.first) else '-'} | {v(pp.second).expanded_name() if v(pp.second) else '-'}")
