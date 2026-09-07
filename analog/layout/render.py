"""Render the tile to PNGs using the PDK layer colours.

    klayout -b -z -r analog/layout/render.py      (or: make png)

Two views of the analog macro, because one is not enough: at the scale that
shows the guard ring and the power straps, the transistors are a smudge.

  docs/macro_layout.png      the whole macro: guard ring, straps, pins
  docs/inverter_layout.png   the inverter core, close up

The hardened tile is rendered by the flow itself (`tt_tool.py --create-png`,
which CI also runs), so it is not repeated here.
"""
import os
import pya

GDS = "macro/tt_analog_inverter.gds"
LYP = "/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyp"

# Cell name -> (output, width, height). The core and the macro are rendered by
# looking up their bounding boxes in the layout, so they follow the build.
VIEWS = [
    (None,            "macro_layout.png",    760, 840),
    ("inverter_core", "inverter_layout.png", 640, 900),
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
