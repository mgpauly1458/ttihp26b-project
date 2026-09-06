"""Extrude the tile GDS into a 3D model (glTF binary).

    ./run.sh python3 layout/build_glb.py        (or: make glb)

The other two 3D viewers -- GDS3D and KLayout's 2.5D view -- both need an X
display. This one does not: it writes out/tile_3d.glb, which opens in any glTF
viewer, a browser, or a phone, and can be attached to a review. Reach for it
over ssh, or anywhere a window is not going to appear.

Layer heights, thicknesses and colours come from the same generated GDS3D
process file, so all three views agree by construction.

Polygons are triangulated with mapbox_earcut (via trimesh) and extruded. GDS
polygons from PCells are not always simple, so anything that fails to
triangulate is reported rather than silently dropped.
"""

import os
import sys
from collections import defaultdict

import gdstk
import trimesh
from shapely.geometry import Polygon

HERE = os.path.dirname(os.path.realpath(__file__))
ANALOG = os.path.dirname(HERE)

TOP = "tt_um_mgpauly1458_inverter"
GDS = f"{ANALOG}/../gds/{TOP}.gds"
PROCESS = f"{ANALOG}/tech/sg13g2_gds3d.txt"
OUT = f"{ANALOG}/out/tile_3d.glb"


def read_process(path):
    """Parse the GDS3D process file into (layer, datatype) -> properties."""
    if not os.path.exists(path):
        sys.exit(f"missing {path} -- run 'make gds3d-tech' first")
    stack, block = {}, {}
    for line in open(path):
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        if line.startswith("LayerStart:"):
            block = {"name": line.split(":", 1)[1].strip()}
        elif line == "LayerEnd":
            key = (int(block["Layer"]), int(block["Datatype"]))
            stack[key] = {
                "name": block["name"],
                "z": float(block["Height"]),
                "h": float(block["Thickness"]),
                "rgba": [int(255 * float(block[c])) for c in
                         ("Red", "Green", "Blue")] + [255],
            }
            block = {}
        elif ":" in line and block:
            k, v = line.split(":", 1)
            block[k.strip()] = v.strip()
    if not stack:
        sys.exit(f"{path}: parsed no layers")
    return stack


def main():
    if not os.path.exists(GDS):
        sys.exit(f"missing {GDS} -- run 'make gds' first")
    stack = read_process(PROCESS)

    lib = gdstk.read_gds(GDS)
    top = next((c for c in lib.top_level() if c.name == TOP), None)
    if top is None:
        sys.exit(f"{GDS}: no top cell named {TOP}")
    flat = top.copy("__flat__")
    flat.flatten()

    by_layer = defaultdict(list)
    for poly in flat.polygons:
        key = (poly.layer, poly.datatype)
        if key in stack:
            by_layer[key].append(poly)

    if not by_layer:
        sys.exit("no polygons matched the process file -- wrong GDS?")

    geometry, skipped, counts = [], 0, {}
    for key, polys in sorted(by_layer.items()):
        spec = stack[key]
        # Merge first: overlapping slabs on one layer otherwise produce
        # coincident faces, which render as z-fighting stripes.
        merged = gdstk.boolean(polys, [], "or", layer=key[0], datatype=key[1])
        parts = []
        for poly in merged:
            pts = poly.points
            if len(pts) < 3:
                continue
            try:
                shape = Polygon(pts)
                if not shape.is_valid:
                    shape = shape.buffer(0)
                if shape.is_empty:
                    continue
                part = trimesh.creation.extrude_polygon(
                    shape, height=spec["h"], engine="earcut")
            except Exception:
                skipped += 1
                continue
            part.apply_translation((0.0, 0.0, spec["z"]))
            parts.append(part)
        if not parts:
            continue
        mesh = trimesh.util.concatenate(parts)
        mesh.visual.face_colors = spec["rgba"]
        geometry.append((spec["name"], mesh))
        counts[spec["name"]] = len(parts)

    # One named geometry per layer, so a viewer's outline panel is the layer
    # list and layers can be toggled individually.
    scene = trimesh.Scene()
    for name, mesh in geometry:
        scene.add_geometry(mesh, geom_name=name)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    scene.export(OUT)
    total = sum(counts.values())
    print(f"wrote {os.path.relpath(OUT, ANALOG)}"
          f" -- {total} solids across {len(counts)} layers")
    for name in sorted(counts, key=lambda n: -counts[n]):
        print(f"    {name:<12} {counts[name]}")
    if skipped:
        print(f"  WARNING: {skipped} polygons could not be triangulated")


if __name__ == "__main__":
    main()
