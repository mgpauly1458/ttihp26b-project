"""Build the Tiny Tapeout analog tile containing a hand-drawn CMOS inverter.

    klayout -b -r analog/layout/build_gds.py

Produces gds/<TOP>.gds. Two cells:

  inverter_core   the transistors, their taps, and the local interconnect,
                  plus four Metal1 landing pads (A, Y, VDD, VSS)
  <TOP>           the tile: core + Metal4 power stripes + via stacks up to
                  TopMetal1 + routing out to the ua[] pads

Coordinates are nm throughout (layout dbu = 1nm).

Signal-to-pin assignment is deliberate. The gate contact leaves the core on the
left and the drain strap on the right, so the input takes ua[1] (the more
leftward pad at x=166560) and the output takes ua[0] (x=191040). Assigning them
the other way round would force the two TopMetal1 routes to cross.
"""

import sys, os, re, pya

KT = "/foss/pdks/ihp-sg13g2/libs.tech/klayout"
sys.path += [os.path.join(KT, "python"),
             os.path.join(KT, "python", "pycell4klayout-api", "source", "python")]
import sg13g2_pycell_lib  # noqa: E402

TOP = "tt_um_mgpauly1458_inverter"

# --------------------------------------------------------------- constants
DIE_W, DIE_H = 202080, 313740          # tt_analog_1x2.def DIEAREA

# ua[n] pad centres from tt_analog_1x2.def, on TopMetal1, 1750 x 2000 at y=0..2000
UA_X = {0: 191040, 1: 166560, 2: 142080, 3: 117600, 4: 93120, 5: 68640}
UA_HW, UA_TOP = 875, 2000

ACTIV, GATPOLY, CONT, METAL1 = (1, 0), (5, 0), (6, 0), (8, 0)
NWELL, METAL4, TOPMETAL1 = (31, 0), (50, 0), (126, 0)
PRBOUND = (189, 4)          # prBoundary.boundary; 189/0 (.drawing) is rejected
HEATTRANS = (51, 0)         # HeatTrans.drawing, drawn by the device PCells
PIN_PURPOSE = {"Metal4": (50, 2), "TopMetal1": (126, 2)}
M1_TEXT = (8, 25)                       # LVS: metal1_text = labels(8, 25)

W_P, W_N, L = "2.0u", "1.0u", "0.13u"
Y_PTAP, Y_NMOS, Y_PMOS, Y_NTAP = -1400, 0, 2400, 4800

# Core landing pads, in core-local coordinates. The A and Y pads reach well out
# to either side so their via stacks end up far enough apart that the two
# TopMetal1 routes clear minimum spacing.
PAD_A   = (-4000,   700,  -250, 2760)
PAD_Y   = (  580,  1500,  4300, 3560)
PAD_VDD = ( -800,  4890,  1000, 8000)
PAD_VSS = ( -800, -3800,  1000, -700)

CORE_X, CORE_Y = 178000, 40000          # where the core sits in the tile

ly = pya.Layout()
ly.dbu = 0.001
lib = pya.Library.library_by_name("SG13_dev", "sg13g2")


def L_(t):
    return ly.layer(*t)


def box(cell, layer, x1, y1, x2, y2):
    cell.shapes(L_(layer)).insert(pya.Box(x1, y1, x2, y2))


def label(cell, text, x, y):
    cell.shapes(L_(M1_TEXT)).insert(pya.Text(text, pya.Trans(pya.Point(x, y))))


def pcell(cell, name, x, y, **params):
    pid = lib.layout().pcell_id(name)
    var = ly.add_pcell_variant(lib, pid, params)
    cell.insert(pya.CellInstArray(var, pya.Trans(pya.Point(x, y))))


def centre(pad):
    x1, y1, x2, y2 = pad
    return (x1 + x2) // 2, (y1 + y2) // 2


# ============================================================== inverter core
core = ly.create_cell("inverter_core")

pcell(core, "ptap1", 0, Y_PTAP)
pcell(core, "nmos",  0, Y_NMOS, w=W_N, l=L, ng="1")
pcell(core, "pmos",  0, Y_PMOS, w=W_P, l=L, ng="1")
pcell(core, "ntap1", 0, Y_NTAP)

# One generous well over the whole p-side: the pmos and ntap PCells each draw
# their own, and where those meet the tie is only marginally enclosed, which
# trips NW.d (min NWell space to external N+ Activ = 0.31).
box(core, NWELL, -500, Y_PMOS - 500, 1300, Y_NTAP + 1300)

# Gate: bridge the two polys, then an arm left to the contact. The contact goes
# out here rather than inside the cell because at the gate's height the left
# column is empty, whereas anywhere inside, the Metal1 pad would land within
# minimum spacing of the Y strap.
box(core, GATPOLY, 340, Y_NMOS + 1180, 470, Y_PMOS - 180)
box(core, GATPOLY, -560, 1560, 470, 1900)
box(core, CONT,   -480, 1650, -320, 1810)

# Risers from each device's left source/drain metal to its tap, and the output
# strap tying the two drains together on the right.
box(core, METAL1, 70, Y_PTAP + 90, 230, Y_NMOS + 1000)
box(core, METAL1, 70, Y_PMOS, 230, Y_NTAP + 690)
box(core, METAL1, 580, Y_NMOS, 740, Y_PMOS + 2000)

for pad in (PAD_A, PAD_Y, PAD_VDD, PAD_VSS):
    box(core, METAL1, *pad)

# Net names for LVS. Layer 8/25 is the only one the deck reads
# (metal1_text = labels(8, 25), attached via connect(metal1_con, metal1_text)).
label(core, "ua[1]",  *centre(PAD_A))
label(core, "ua[0]",  *centre(PAD_Y))
label(core, "VDPWR",  *centre(PAD_VDD))
label(core, "VGND",   *centre(PAD_VSS))

# ======================================================================= tile
top = ly.create_cell(TOP)
top.insert(pya.CellInstArray(core.cell_index(),
                             pya.Trans(pya.Point(CORE_X, CORE_Y))))
box(top, PRBOUND, 0, 0, DIE_W, DIE_H)


def abs_centre(pad):
    x, y = centre(pad)
    return x + CORE_X, y + CORE_Y


AX, AY = abs_centre(PAD_A)
YX, YY = abs_centre(PAD_Y)
VDX, VDY = abs_centre(PAD_VDD)
VSX, VSY = abs_centre(PAD_VSS)

# Via stacks: signals go all the way to TopMetal1, power only as far as Metal4
# (the power stripes the shuttle connects to are Metal4).
pcell(top, "via_stack", AX,  AY,  b_layer="Metal1", t_layer="TopMetal1", vn_columns=3, vn_rows=3)
pcell(top, "via_stack", YX,  YY,  b_layer="Metal1", t_layer="TopMetal1", vn_columns=3, vn_rows=3)
pcell(top, "via_stack", VDX, VDY, b_layer="Metal1", t_layer="Metal4", vn_columns=3, vn_rows=3)
pcell(top, "via_stack", VSX, VSY, b_layer="Metal1", t_layer="Metal4", vn_columns=3, vn_rows=3)

# ------------------------------------------------------------ power stripes
# Precheck is the authority here, and it wants TopMetal1 at least 2.1um wide:
#   ERROR: Port VDPWR has wrong layer ...: Metal4 != TopMetal1
#   ERROR: Port VGND has too small width ...: 2.0 < 2.1 um
# (The published analog spec quotes Metal4 and 1.2um, which is the sky130
# guidance, not IHP's.)
#
# That puts the stripes on the same layer as the ua routing, so they are placed
# well clear of the signal corridor at x = 165560..192040 and are fed from the
# core by Metal4 spurs, which pass underneath the signal routes harmlessly.
STRIPE_HW = 1300                        # 2.6um wide, over the 2.1um floor
STRIPE_Y0, STRIPE_Y1 = 6000, DIE_H - 3000
VDPWR_X, VGND_X = 100000, 130000

box(top, TOPMETAL1, VDPWR_X - STRIPE_HW, STRIPE_Y0, VDPWR_X + STRIPE_HW, STRIPE_Y1)
box(top, TOPMETAL1, VGND_X - STRIPE_HW, STRIPE_Y0, VGND_X + STRIPE_HW, STRIPE_Y1)

# Metal4 spurs from each power via stack across to its stripe, and a
# Metal4 -> TopMetal1 stack where the spur meets it.
box(top, METAL4, VDPWR_X, VDY - 555, VDX + 555, VDY + 555)
box(top, METAL4, VSX - 555, VSY - 555, VGND_X, VSY + 555)
pcell(top, "via_stack", VDPWR_X, VDY, b_layer="Metal4", t_layer="TopMetal1", vn_columns=3, vn_rows=3)
pcell(top, "via_stack", VGND_X, VSY, b_layer="Metal4", t_layer="TopMetal1", vn_columns=3, vn_rows=3)

# --------------------------------------------------- TopMetal1 to the ua pads
TM_HW = 1000            # 2um wide, comfortably over TopMetal1 minimum width


def ua_route(net_x, net_y, ua_index):
    """Route a signal from its via stack out to a ua pad on the bottom edge."""
    px = UA_X[ua_index]
    box(top, TOPMETAL1, px - UA_HW, 0, px + UA_HW, UA_TOP)      # the pad itself
    if px < net_x:                                              # exits left
        box(top, TOPMETAL1, px - TM_HW, net_y - TM_HW, net_x, net_y + TM_HW)
    else:                                                       # exits right
        box(top, TOPMETAL1, net_x, net_y - TM_HW, px + TM_HW, net_y + TM_HW)
    box(top, TOPMETAL1, px - TM_HW, 0, px + TM_HW, net_y + TM_HW)


ua_route(AX, AY, 1)     # input  A -> ua[1], exits left
ua_route(YX, YY, 0)     # output Y -> ua[0], exits right

# ------------------------------------------------------------------- output
# Tiny Tapeout's precheck requires the LEF to declare every pin in the tile
# interface, not just the ones this design connects to. Rather than hand-write
# 51 entries, parse them straight out of the DEF template: that guarantees the
# names, layers and positions agree with what the shuttle expects, and it draws
# the matching metal in the GDS so the LEF is not describing geometry that
# isn't there.
DEF_TEMPLATE = "tech/tt_analog_1x2.def"
DEF_LAYER_GDS = {"Metal4": METAL4, "TopMetal1": TOPMETAL1}

PIN_RE = re.compile(
    r"-\s+(\S+)\s+\+\s+NET\s+\S+\s+\+\s+DIRECTION\s+(\S+)\s+\+\s+USE\s+(\S+)"
    r"\s*\+\s*PORT\s*\+\s*LAYER\s+(\S+)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)"
    r"\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*\+\s*PLACED\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)",
    re.S,
)


def def_pins(path):
    """Yield (name, direction, use, layer, (x1, y1, x2, y2)) for each DEF pin."""
    with open(path) as fh:
        text = fh.read()
    for name, direction, use, layer, ox1, oy1, ox2, oy2, px, py in PIN_RE.findall(text):
        px, py = int(px), int(py)
        yield (name, direction, use, layer,
               (px + int(ox1), py + int(oy1), px + int(ox2), py + int(oy2)))


pins = list(def_pins(DEF_TEMPLATE))
if len(pins) != 51:
    raise SystemExit(f"expected 51 pins in {DEF_TEMPLATE}, parsed {len(pins)}")

# Draw every interface pin. The ones this design uses (ua[0], ua[1]) already
# have routing on them; redrawing the DEF rectangle just merges with it. The
# rest are unconnected stubs, which is what an unused tile input should be.
for name, direction, use, layer, rect in pins:
    box(top, DEF_LAYER_GDS[layer], *rect)

# Power comes last: these are not in the DEF's PINS section (it declares VPWR
# and VGND as special nets with no geometry), so the stripes drawn above are
# the pin shapes.
PINS = [(name, use, layer, rect) for name, _, use, layer, rect in pins]
PINS += [
    ("VDPWR", "POWER",  "TopMetal1",
     (VDPWR_X - STRIPE_HW, STRIPE_Y0, VDPWR_X + STRIPE_HW, STRIPE_Y1)),
    ("VGND",  "GROUND", "TopMetal1",
     (VGND_X - STRIPE_HW, STRIPE_Y0, VGND_X + STRIPE_HW, STRIPE_Y1)),
]


def um(v):
    return f"{v / 1000.0:.3f}"


def write_lef(path):
    out = ["VERSION 5.7 ;", 'BUSBITCHARS "[]" ;', 'DIVIDERCHAR "/" ;', "",
           f"MACRO {TOP}", "  CLASS BLOCK ;", "  ORIGIN 0 0 ;",
           f"  SIZE {um(DIE_W)} BY {um(DIE_H)} ;"]
    for name, use, layer, (x1, y1, x2, y2) in PINS:
        out += [f"  PIN {name}", "    DIRECTION INOUT ;", f"    USE {use} ;",
                "    PORT", f"      LAYER {layer} ;",
                f"        RECT {um(x1)} {um(y1)} {um(x2)} {um(y2)} ;",
                "    END", f"  END {name}"]
    out += [f"END {TOP}", "", "END LIBRARY", ""]
    with open(path, "w") as fh:
        fh.write("\n".join(out))


# Every LEF port must also appear as a polygon on the matching <layer>.pin,
# containing the LEF rectangle -- pin_check verifies exactly that.
for name, use, layer, rect in PINS:
    box(top, PIN_PURPOSE[layer], *rect)

# The device PCells draw HeatTrans (51/0), which is not on Tiny Tapeout's
# allowed layer list. Clearing it across every cell keeps the layer check happy;
# it plays no part in DRC or LVS.
ly.clear_layer(L_(HEATTRANS))

os.makedirs("../gds", exist_ok=True)
os.makedirs("../lef", exist_ok=True)

# KLayout otherwise emits a hidden $$$CONTEXT_INFO$$$ cell holding PCell
# parameters. gdstk, which precheck uses, counts it as a second top-level cell
# and fails the boundary check -- and the analog pin check then inspects
# top_level()[0], which may not be our tile at all.
save_opts = pya.SaveLayoutOptions()
save_opts.write_context_info = False
ly.write(f"../gds/{TOP}.gds", save_opts)
write_lef(f"../lef/{TOP}.lef")
print(f"wrote gds/{TOP}.gds and lef/{TOP}.lef with {len(PINS)} pins")
print(f"  core={core.bbox().to_s()}  tile={top.bbox().to_s()}")
