import sys, os
KT="/foss/pdks/ihp-sg13g2/libs.tech/klayout"
sys.path += [os.path.join(KT,"python"), os.path.join(KT,"python","pycell4klayout-api","source","python")]
import pya, sg13g2_pycell_lib
lib = pya.Library.library_by_name("SG13_dev","sg13g2")
ly = pya.Layout(); ly.dbu=0.001
def dump(name, **p):
    pid = lib.layout().pcell_id(name)
    var = ly.add_pcell_variant(lib, pid, p)
    c = ly.cell(var)
    print("==", name, p, "bbox", str(c.bbox()))
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        shapes = list(c.shapes(li).each())
        if shapes:
            print("  layer %d/%d" % (info.layer, info.datatype), len(shapes), [str(s.bbox()) for s in shapes][:6])
dump("nmos", w="0.15u", l="8.0u", ng="1")
dump("nmos", w="0.6u", l="8.0u", ng="4")
dump("nmos", w="0.6u", l="0.13u", ng="1")
dump("pmos", w="24.0u", l="0.5u", ng="24")
dump("via_stack", b_layer="Metal1", t_layer="Metal3", vn_columns=1, vn_rows=1)
dump("via_stack", b_layer="Metal2", t_layer="Metal3", vn_columns=1, vn_rows=1)
dump("via_stack", b_layer="Metal1", t_layer="Metal4", vn_columns=3, vn_rows=3)
