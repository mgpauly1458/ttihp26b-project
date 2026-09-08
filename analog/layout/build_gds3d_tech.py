"""Generate the GDS3D process file for ihp-sg13g2 from the PDK's KLayout 2.5D stack (libs.tech/klayout/tech/d25/sg13g2_beol.lyd25).

    ./run.sh python3 layout/build_gds3d_tech.py      (or: make gds3d-tech)   ->  tech/sg13g2_gds3d.txt

- No open PDK ships the gds3d_tech.txt the container's wrapper wants; deriving it from the .lyd25 keeps GDS3D and KLayout's 2.5D view on the same heights and colours.
- The .lyd25 computes some entries with booleans (contact on poly vs active, GatPoly resistor kinds); GDS3D maps one raw layer/datatype to one slab, so FLATTEN merges or drops those.
- The PDK stack is BEOL only; EXTRA adds NWell at an illustrative depth, the one value not from the PDK.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

PDK = "/foss/pdks/ihp-sg13g2"
LYD25 = f"{PDK}/libs.tech/klayout/tech/d25/sg13g2_beol.lyd25"

HERE = os.path.dirname(os.path.realpath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "tech", "sg13g2_gds3d.txt")

# .lyd25 entries whose expression is not a plain input(): name -> (emit as, layer, datatype, note), None = drop (same geometry already emitted)
FLATTEN = {
    # Cont drawn once over the span of both landing variants (0.400 -> 1.040)
    "Cont->Activ":   ("Cont", 6, 0, "Cont, both variants merged"),
    "Cont->Gatpoly": None,
    # the four resistor kinds share z; a materials difference, not geometry
    "GatPoly": ("GatPoly", 5, 0, "GatPoly, resistor variants merged"),
    "Rsil":    ("PolyRes", 128, 0, "PolyRes, resistor variants merged"),
    "Rhigh":   None,
    "Rppd":    None,
}

# NWell is not in the BEOL-only PDK stack; added below the surface at an illustrative depth
EXTRA = [
    # name,    layer, datatype, zstart, height, rgb,        note
    ("NWell",     31, 0, -0.600, 0.600, (0.55, 0.35, 0.75),
     "NOT from the PDK stack: depth is illustrative, not a process value"),
]

# shaded as metal in GDS3D
METAL = {"Metal1", "Metal2", "Metal3", "Metal4", "Metal5",
         "TopMetal1", "TopMetal2", "Via1", "Via2", "Via3", "Via4",
         "TopVia1", "TopVia2", "Vmim", "Cont"}

# transparency; the wide top-metal power stripes get more so they do not hide the tile
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
            continue            # the PDK now defines it; its version wins
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
