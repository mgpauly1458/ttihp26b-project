"""Generate a GDS3D process file for ihp-sg13g2 from the PDK's own 2.5D stack.

    ./run.sh python3 layout/build_gds3d_tech.py      (or: make gds3d-tech)

GDS3D is installed in the container and the container even ships a wrapper for
it, but the wrapper wants `$PDKPATH/libs.tech/gds3d/gds3d_tech.txt` and no open
PDK here provides one -- not ihp-sg13g2, not sky130A, not gf180mcuD. So the
process file is derived instead of hand-written, from
`libs.tech/klayout/tech/d25/sg13g2_beol.lyd25`, which is the PDK's definition of
the same thing for KLayout's 2.5D view. Both viewers then show the same stack,
and there is one place to fix if the PDK revises a layer height.

The two formats are not quite the same shape. The KLayout stack computes some
entries with boolean algebra -- separating a contact landing on poly from one
landing on active, or splitting GatPoly into the four kinds of resistor -- and
GDS3D maps one raw layer/datatype directly to one slab, with no booleans. Those
entries are flattened here, which is what FLATTEN below is for.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

PDK = "/foss/pdks/ihp-sg13g2"
LYD25 = f"{PDK}/libs.tech/klayout/tech/d25/sg13g2_beol.lyd25"

HERE = os.path.dirname(os.path.realpath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "tech", "sg13g2_gds3d.txt")

# Entries in the KLayout stack whose layer expression is not a plain input().
#
#   name in the .lyd25   -> (emit as, raw layer, datatype, why)
#
# `None` means drop the entry: it would draw a second slab on the same geometry
# at the same height as one that is already emitted.
FLATTEN = {
    # Cont is split by what it lands on. GDS3D cannot do that, so Cont is drawn
    # once, over the full range the two variants span (0.400 -> 1.040).
    "Cont->Activ":   ("Cont", 6, 0, "Cont, both variants merged"),
    "Cont->Gatpoly": None,
    # GatPoly is split four ways by which resistor module sits on it. All four
    # occupy the same z, so the two underlying drawn layers are emitted once
    # each and the resistor distinction is dropped -- it is a materials
    # difference, not a geometric one, and nothing in 3D would show it.
    "GatPoly": ("GatPoly", 5, 0, "GatPoly, resistor variants merged"),
    "Rsil":    ("PolyRes", 128, 0, "PolyRes, resistor variants merged"),
    "Rhigh":   None,
    "Rppd":    None,
}

# The PDK stack is BEOL only -- it starts at Activ and goes up. For a layout
# whose analog half is two transistors, that means the NWell under the PMOS
# simply is not drawn, which is a conspicuous hole in the picture. It is added
# here, below the surface, and it is the one entry in the output that the PDK
# did not supply: the depth is a plausible drawing convention, not a process
# number. Nothing else infers geometry the PDK has not stated.
EXTRA = [
    # name,    layer, datatype, zstart, height, rgb,        note
    ("NWell",     31, 0, -0.600, 0.600, (0.55, 0.35, 0.75),
     "NOT from the PDK stack: depth is illustrative, not a process value"),
]

# Layers GDS3D should shade as metal rather than as a dielectric or a device.
METAL = {"Metal1", "Metal2", "Metal3", "Metal4", "Metal5",
         "TopMetal1", "TopMetal2", "Via1", "Via2", "Via3", "Via4",
         "TopVia1", "TopVia2", "Vmim", "Cont"}

# Transparency. The two top metals are wide power stripes that would otherwise
# hide the whole tile under them, so they get more of it.
FILTER_DEFAULT, FILTER_TOP = 0.35, 0.6
TOP_LAYERS = {"TopMetal1", "TopMetal2"}

Z_RE = re.compile(
    r"z\(\s*(\w+)\s*,\s*name:\s*\"([^\"]+)\"\s*,\s*zstart:\s*([-\d.]+)\s*,"
    r"\s*height:\s*([-\d.]+)\s*,\s*color:\s*0x([0-9a-fA-F]{6})\s*\)")
INPUT_RE = re.compile(r"^\s*(\w+)\s*=\s*input\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*$")


def main():
    if not os.path.exists(LYD25):
        sys.exit(f"missing {LYD25} -- is the ihp-sg13g2 PDK mounted?")
    text = ET.parse(LYD25).getroot().findtext("text")
    if not text:
        sys.exit(f"{LYD25}: no <text> stack definition found")

    # name -> (layer, datatype) for the plain `X = input(l, d)` declarations.
    inputs = {m.group(1): (int(m.group(2)), int(m.group(3)))
              for m in (INPUT_RE.match(line) for line in text.splitlines()) if m}

    entries, dropped = [], []
    for expr, name, zstart, height, color in Z_RE.findall(text):
        if name in FLATTEN:
            mapped = FLATTEN[name]
            if mapped is None:
                dropped.append(name)
                continue
            name, layer, datatype, note = mapped
            if name == "Cont":                  # span both Cont variants
                zstart, height = "0.400", "0.640"
        elif expr in inputs:
            layer, datatype = inputs[expr]
            note = ""
        else:
            sys.exit(f"{name}: expression {expr!r} is neither a plain input() "
                     f"nor listed in FLATTEN -- the PDK stack has changed")
        rgb = [int(color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
        entries.append((name, layer, datatype, float(zstart), float(height),
                        rgb, note))

    if not entries:
        sys.exit(f"{LYD25}: parsed no z() entries")

    seen = {(e[1], e[2]) for e in entries}
    for name, layer, datatype, zstart, height, rgb, note in EXTRA:
        if (layer, datatype) in seen:
            continue            # the PDK added it since; its version wins
        entries.append((name, layer, datatype, zstart, height, list(rgb), note))

    # GDS3D draws in file order; bottom-up reads better in the layer panel.
    entries.sort(key=lambda e: e[3])

    lines = [
        "# GDS3D process file for ihp-sg13g2.",
        "#",
        "# GENERATED -- do not edit. Regenerate with:",
        "#     cd analog && make gds3d-tech",
        "#",
        f"# Derived from {LYD25},",
        "# the PDK's own 2.5D stack definition, so GDS3D and KLayout's 2.5D view",
        "# show the same heights and the same colours. The one exception is NWell,",
        "# which the BEOL-only PDK stack does not cover -- see EXTRA in the",
        "# generator; its depth is illustrative.",
        "#",
        "# Format: one LayerStart/LayerEnd block per layer. Height is the bottom",
        "# of the slab in um and Thickness its extent; Red/Green/Blue and Filter",
        "# are 0..1, Filter being transparency -- turn it up if the upper metals",
        "# hide what you are trying to see.",
        "",
    ]
    if dropped:
        lines += [f"# Dropped as duplicate geometry: {', '.join(dropped)}.", ""]

    for name, layer, datatype, zstart, height, rgb, note in entries:
        if note:
            lines.append(f"# {note}")
        lines += [
            f"LayerStart: {name}",
            f"Layer: {layer}",
            f"Datatype: {datatype}",
            f"Height: {zstart:.3f}",
            f"Thickness: {height:.3f}",
            f"Red: {rgb[0]:.3f}",
            f"Green: {rgb[1]:.3f}",
            f"Blue: {rgb[2]:.3f}",
            f"Filter: {FILTER_TOP if name in TOP_LAYERS else FILTER_DEFAULT}",
            f"Metal: {1 if name in METAL else 0}",
            "Show: 1",
            "LayerEnd",
            "",
        ]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        fh.write("\n".join(lines))
    print(f"wrote {OUT} with {len(entries)} layers"
          + (f" ({len(dropped)} dropped)" if dropped else ""))


if __name__ == "__main__":
    main()
