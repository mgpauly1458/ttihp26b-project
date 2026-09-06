"""Render the tile to PNGs using the PDK layer colours.

    klayout -b -z -r analog/layout/render.py      (or: make png)

Three views, because one is not enough any more. The tile is 202 x 314 um and
the analog inverter is about 8 um across, so a whole-tile image that shows the
routing renders the circuit itself as a smudge.

  docs/tile_layout.png       the whole tile: both blocks and all the routing
  docs/inverter_layout.png   the analog core, close up
  docs/digital_layout.png    the hardened macro
"""
import os
import pya

GDS = "../gds/tt_um_mgpauly1458_inverter.gds"
LYP = "/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyp"

# Cell name -> (output, width, height). The core and the macro are rendered by
# looking up their bounding boxes in the layout, so they follow the build.
VIEWS = [
    (None,           "tile_layout.png",     620, 960),
    ("inverter_core", "inverter_layout.png", 640, 900),
    ("ms_hello",     "digital_layout.png",  760, 760),
]

os.makedirs("../docs", exist_ok=True)

# One LayoutView per image: zoom state is per-view and reloading is cheap.
for cell_name, out, w, h in VIEWS:
    lv = pya.LayoutView()
    lv.load_layout(GDS, 0)
    lv.load_layer_props(LYP)
    lv.max_hier()
    if cell_name is None:
        lv.zoom_fit()
        box = lv.box()
    else:
        ly = lv.active_cellview().layout()
        cell = ly.cell(cell_name)
        if cell is None:
            raise SystemExit(f"no cell {cell_name} in {GDS}")
        # bbox() is cell-local; the instance is placed in the tile, so find
        # where it actually sits rather than assuming the placement constants.
        top = ly.cell(ly.top_cell().name)
        boxes = [inst.bbox() for inst in top.each_inst()
                 if inst.cell.name == cell_name]
        if not boxes:
            raise SystemExit(f"{cell_name} is not instantiated in the top cell")
        bb = boxes[0]
        box = pya.DBox(bb.left * ly.dbu, bb.bottom * ly.dbu,
                       bb.right * ly.dbu, bb.top * ly.dbu)
    lv.zoom_box(box.enlarged(box.width() * 0.04 + 0.25,
                             box.height() * 0.04 + 0.25))
    lv.save_image(f"../docs/{out}", w, h)
    print(f"wrote docs/{out}")
