"""Render the macro to PNGs using the PDK layer colours.

    klayout -b -z -r analog/layout/render.py      (or: make png)

  docs/macro_layout.png      the whole macro: DAC, ring row, guard ring, pins
  docs/ring_row_layout.png   the ring row, close up
  docs/dac_rows_layout.png   a few DAC rows, close up
"""
import os
import sys
import pya

GDS = os.environ.get("GDS", "macro/tt_analog_ring.gds")
LYP = "/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyp"
OUTDIR = os.environ.get("OUTDIR", "../docs")
os.makedirs(OUTDIR, exist_ok=True)

# (output, width, height, box in um or None for the whole cell)
VIEWS = [
    ("macro_layout.png", 1600, 1000, None),
    ("ring_row_layout.png", 1800, 700, (11, 40, 60, 50)),
    ("dac_rows_layout.png", 1800, 700, (2, 3, 32, 9)),
]

for out, w, h, bx in VIEWS:
    lv = pya.LayoutView()
    lv.load_layout(GDS, 0)
    lv.load_layer_props(LYP)
    lv.max_hier()
    if bx is None:
        lv.zoom_fit()
    else:
        lv.zoom_box(pya.DBox(*bx))
    lv.save_image(os.path.join(OUTDIR, out), w, h)
    print("wrote", os.path.join(OUTDIR, out))
