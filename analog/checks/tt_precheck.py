"""Local stand-in for the Tiny Tapeout prechecks that inspect the GDS.

    ./run.sh python3 checks/tt_precheck.py        (or: make precheck)

Reproduces the four checks that are easy to get wrong and slow to iterate on in
CI, since a round trip through GitHub Actions is roughly seven minutes:

  layer check        no GDS layer outside Tiny Tapeout's allowlist
  boundary check     exactly one top-level cell, covering the full die
  pin check          every LEF port also drawn on the matching <layer>.pin
  analog pin check   ua[] pads wired iff info.yaml says they are

This is a convenience, not the authority. CI runs the real precheck, which does
more than this (DRC, zero-area, cell names, Verilog syntax). A pass here means
"don't bother pushing yet" has been ruled out, nothing stronger.

Everything is read from info.yaml, so this works unchanged for the next block.
"""

import os
import re
import sys

import gdstk
import yaml

REPO = "/work"
HERE = os.path.dirname(os.path.realpath(__file__))
LYP = "/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyp"

# <layer>.pin purposes that a LEF port may legally be drawn on.
PIN_PURPOSE = {"Metal4": (50, 2), "TopMetal1": (126, 2)}

# From tt-support-tools precheck/tech_data.py: analog_pin_rects() for
# ihp-sg13g2. ua[0] sits at x=190.165 and they step 24.48um to the left.
UA_X0, UA_STEP, UA_W, UA_H = 190.165, 24.48, 1.75, 2.0
UA_PIN_LAYER, UA_VIA_LAYER = (126, 0), (125, 0)

failures = []
notes = []


def fail(msg):
    failures.append(msg)


def lyp_layer_map():
    """name -> (layer, datatype), parsed from the PDK layer properties file."""
    text = open(LYP).read()
    pairs = re.findall(r"<name>([^<]*)</name>.*?<source>([^<]*)</source>", text, re.S)
    out = {}
    for name, source in pairs:
        m = re.match(r"(\d+)/(\d+)", source)
        if m:
            out[name] = (int(m.group(1)), int(m.group(2)))
    return out


def main():
    info = yaml.safe_load(open(f"{REPO}/info.yaml"))["project"]
    top_module = info["top_module"]
    analog_pins = int(info.get("analog_pins", 0))
    pinout = yaml.safe_load(open(f"{REPO}/info.yaml")).get("pinout", {})

    gds_path = f"{REPO}/gds/{top_module}.gds"
    lef_path = f"{REPO}/lef/{top_module}.lef"
    for path in (gds_path, lef_path):
        if not os.path.exists(path):
            print(f"missing {path} -- run 'make gds' first")
            return 1

    name2ld = lyp_layer_map()
    lib = gdstk.read_gds(gds_path)

    # ---------------------------------------------------------- layer check
    valid_names = [
        line.strip()
        for line in open(os.path.join(HERE, "tt_valid_layers.txt"))
        if line.strip() and not line.startswith("#")
    ]
    valid = {name2ld[n] for n in valid_names if n in name2ld}
    used = lib.layers_and_datatypes().union(lib.layers_and_texttypes())
    ld2name = {v: k for k, v in name2ld.items()}
    invalid = sorted(used - valid)
    if invalid:
        fail("layer check: " + ", ".join(
            f"{ld} ({ld2name.get(ld, 'unknown')})" for ld in invalid))
    notes.append(f"layer check: {len(used)} layers used, {len(invalid)} invalid")

    # ------------------------------------------------------- boundary check
    tops = lib.top_level()
    if len(tops) != 1:
        fail("boundary check: GDS top level not unique: "
             + ", ".join(c.name for c in tops)
             + "  (write the GDS with SaveLayoutOptions.write_context_info = False)")
    elif tops[0].name != top_module:
        fail(f"boundary check: top cell is {tops[0].name}, expected {top_module}")
    else:
        notes.append(f"boundary check: single top cell {tops[0].name}")

    top = next((c for c in tops if c.name == top_module), None)
    if top is None:
        for msg in failures:
            print("FAIL " + msg)
        return 1
    flat = top.copy("__flat__")
    flat.flatten()

    # ------------------------------------------------------------ pin check
    lef = open(lef_path).read()
    ports = re.findall(
        r"PIN (\S+).*?LAYER (\S+) ;\s*RECT ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) ;",
        lef, re.S)
    merged = {}
    for layer_name, ld in PIN_PURPOSE.items():
        polys = [p for p in flat.polygons if (p.layer, p.datatype) == ld]
        merged[layer_name] = gdstk.boolean(polys, [], "or")

    missing = []
    for name, layer_name, lx, by, rx, ty in ports:
        if layer_name not in PIN_PURPOSE:
            missing.append(f"{name}: unexpected LEF port layer {layer_name}")
            continue
        lx, by, rx, ty = float(lx), float(by), float(rx), float(ty)
        ok = any(
            poly.contain_all((lx + 0.001, by + 0.001), (rx - 0.001, by + 0.001),
                             (lx + 0.001, ty - 0.001), (rx - 0.001, ty - 0.001))
            for poly in merged[layer_name])
        if not ok:
            missing.append(f"{name} not covered on {layer_name}.pin")
    if missing:
        fail("pin check: " + "; ".join(missing))
    notes.append(f"pin check: {len(ports)} LEF ports, {len(missing)} missing")

    # ----------------------------------------------------- analog pin check
    # A pad counts as wired if TopMetal1 appears in a ring 0.1-0.5um outside it,
    # or TopVia1 overlaps it. Drawing the pad rectangle itself does not count.
    tm1 = [p for p in flat.polygons if (p.layer, p.datatype) == UA_PIN_LAYER]
    tv1 = [p for p in flat.polygons if (p.layer, p.datatype) == UA_VIA_LAYER]
    for pin in range(8):
        x1 = UA_X0 - UA_STEP * pin
        rect = gdstk.rectangle((x1, 0.0), (x1 + UA_W, UA_H))
        ring = gdstk.boolean(gdstk.offset(rect, 0.5), gdstk.offset(rect, 0.1), "not")
        connected = (bool(gdstk.boolean(tm1, ring, "and"))
                     or bool(gdstk.boolean(tv1, [rect], "and")))
        want_count = pin < analog_pins
        want_desc = bool(pinout.get(f"ua[{pin}]", ""))
        if connected != want_count:
            fail(f"analog pin check: ua[{pin}] connected={connected} but "
                 f"analog_pins={analog_pins} implies {want_count}")
        elif connected != want_desc:
            fail(f"analog pin check: ua[{pin}] connected={connected} but its "
                 f"info.yaml pinout description implies {want_desc}")
    notes.append(f"analog pin check: analog_pins={analog_pins}")

    for note in notes:
        print("  " + note)
    if failures:
        print()
        for msg in failures:
            print("FAIL " + msg)
        return 1
    print("\nlocal precheck: all clear (CI still has the final say)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
