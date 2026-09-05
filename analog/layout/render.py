"""Render out/inverter.gds to a PNG using the PDK layer colours."""
import pya, os
lv = pya.LayoutView()
lv.load_layout("../gds/tt_um_mgpauly1458_inverter.gds", 0)
lv.load_layer_props("/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyp")
lv.max_hier()
lv.zoom_fit()
lv.zoom_box(lv.box().enlarged(0.25, 0.25))
os.makedirs("../docs", exist_ok=True)
lv.save_image("../docs/inverter_layout.png", 460, 1750)
print("wrote docs/inverter_layout.png")
