"""Build the Tiny Tapeout mixed-signal tile.

    klayout -b -r analog/layout/build_gds.py

Produces gds/<TOP>.gds. Three cells:

  inverter_core   the hand-drawn analog inverter: transistors, their taps, the
                  local interconnect, and four Metal1 landing pads
                  (A, Y, VDD, VSS)
  ms_hello        the digital half, read in from digital/out/ms_hello.gds --
                  RTL hardened by LibreLane into a standard-cell macro
  <TOP>           the tile: both blocks, the TopMetal1 power stripes, and the
                  routing that takes the analog nets out to the ua[] pads and
                  the digital nets up to the Metal4 interface stubs

The two halves are independent circuits sharing a tile, a supply and a
substrate; nothing is routed between them. That is the smallest honest
mixed-signal design, and it keeps the two flows -- xschem/ngspice/KLayout for
the analog, LibreLane for the digital -- separable and separately verifiable.

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
METAL2, METAL3 = (10, 0), (30, 0)
NWELL, METAL4, TOPMETAL1 = (31, 0), (50, 0), (126, 0)
PRBOUND = (189, 4)          # prBoundary.boundary; 189/0 (.drawing) is rejected
HEATTRANS = (51, 0)         # HeatTrans.drawing, drawn by the device PCells
PIN_PURPOSE = {"Metal4": (50, 2), "TopMetal1": (126, 2)}
# LVS reads net names off a .text purpose per metal layer:
#   metal1_text = labels(8, 25), metal2_text = labels(10, 25),
#   metal3_text = labels(30, 25), metal4_text = labels(50, 25).
# Labels anywhere else are silently ignored.
M1_TEXT, M4_TEXT = (8, 25), (50, 25)
MACRO_TEXT_LAYERS = [(8, 25), (10, 25), (30, 25), (50, 25)]

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

# ------------------------------------------------------- tile interface pins
# The 51 pins of the tile interface are parsed out of the DEF template rather
# than hand-written: that guarantees the names, layers and positions agree with
# what the shuttle expects, both for the geometry drawn below and for the LEF
# emitted at the end.
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

DEF_PIN_RECT = {name: rect for name, _, _, _, rect in pins}

ly = pya.Layout()
ly.dbu = 0.001
lib = pya.Library.library_by_name("SG13_dev", "sg13g2")


def L_(t):
    return ly.layer(*t)


def box(cell, layer, x1, y1, x2, y2):
    cell.shapes(L_(layer)).insert(pya.Box(x1, y1, x2, y2))


def label(cell, text, x, y, layer=M1_TEXT):
    cell.shapes(L_(layer)).insert(pya.Text(text, pya.Trans(pya.Point(x, y))))


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

# ============================================================== digital macro
# The RTL half. digital/out/ms_hello.gds is produced by LibreLane
# (cd digital && make); it is a 50x50um standard-cell macro whose five signal
# pins sit on Metal2 along its north edge and whose supply reaches Metal4 as
# two VPWR and two VGND straps.
#
# It goes in the empty upper-left of the tile: clear of the analog core (bottom
# right), clear of the ua[] TopMetal1 routing (bottom edge), and clear in x of
# both TopMetal1 power stripes so the stripes never run over it.
MACRO = "ms_hello"
MACRO_GDS = "../digital/out/ms_hello.gds"
MACRO_W = MACRO_H = 50000
MACRO_X, MACRO_Y = 21600, 240000

# Pin centres in macro-local coordinates, from the LibreLane LEF. Each pin is a
# 400nm-wide Metal2 rectangle spanning y = 49600..50000.
MACRO_PIN_X = {"clk": 5280, "rst_n": 14880, "a": 24480,
               "y_comb": 34080, "y_reg": 43680}
MACRO_PIN_HW, MACRO_PIN_Y = 200, 49600                 # local, from the LEF

# Supply strap centres and extent, also from the LEF.
MACRO_VPWR_X = (15660 + 17860) // 2, (35660 + 37860) // 2
MACRO_VGND_X = (21860 + 24060) // 2, (41860 + 44060) // 2
MACRO_STRAP_HW = 1100
MACRO_STRAP_Y0 = 14900                                 # local, from the LEF

ly.read(MACRO_GDS)
macro = ly.cell(MACRO)
if macro is None:
    raise SystemExit(f"{MACRO_GDS} does not contain a cell named {MACRO}")
if (macro.bbox().width(), macro.bbox().height()) != (MACRO_W, MACRO_H):
    raise SystemExit(f"{MACRO} is {macro.bbox().to_s()}, expected "
                     f"{MACRO_W}x{MACRO_H} -- update MACRO_W/MACRO_H")

# LibreLane draws prBoundary over the macro die. Left in place it would appear
# inside the tile's own boundary as a second, smaller boundary rectangle, which
# is exactly what Tiny Tapeout's boundary precheck looks at. The tile draws its
# own prBoundary over the full die, so drop the macro's.
macro.shapes(L_(PRBOUND)).clear()

# LibreLane labels the macro's nets, including "clk", "rst_n" and its supplies,
# and the standard cells carry pin labels of their own. Those nets are the same
# physical nets the tile labels from the outside, so leaving both in place puts
# two names on one net and LVS keeps whichever it likes -- which is how the top
# level ends up looking as though it is missing a port. The tile's own labels
# are the ones that have to win, so the macro's are removed.
for _idx in (L_(t) for t in MACRO_TEXT_LAYERS):
    macro.shapes(_idx).clear()
    for _sub in macro.called_cells():
        ly.cell(_sub).shapes(_idx).clear()

top.insert(pya.CellInstArray(macro.cell_index(),
                             pya.Trans(pya.Point(MACRO_X, MACRO_Y))))


def macro_pin_x(name):
    return MACRO_X + MACRO_PIN_X[name]


# ------------------------------------------------- digital signal routing
# Every net crosses the tile the same way, and the layer assignment is what
# makes it tractable:
#
#   Metal4  vertical, from the interface stub on the top edge down to the bus
#   Metal3  horizontal, one bus per net, each at its own y
#   Metal2  vertical, from the bus down to the macro pin
#
# Because the two vertical layers are never the horizontal one, a vertical run
# may cross any bus it likes. Only bus-to-bus (all parallel, distinct y) and
# spur-to-spur (all parallel, distinct x) spacing has to be reasoned about, and
# both fall out for free. Route them all on one layer and the ordering
# constraints become a puzzle with no solution.
BUS_HW = 1000           # Metal3, 2.0um wide -- also covers the 1.11um Metal3
                        # pad of a 3x3 Metal3->TopMetal1 stack
SPUR_HW = 150           # Metal4, 0.3um wide, matching the DEF interface stubs
BUS_PITCH = 3000

STUB_Y = DIE_H          # the interface stubs run up to the top edge

# net -> (bus y, interface stub, macro pin). Order is free; see above.
DIGITAL_NETS = [
    ("clk",       298000, "clk",       "clk"),
    ("rst_n",     301000, "rst_n",     "rst_n"),
    ("a",         304000, "ui_in[0]",  "a"),
    ("y_comb",    307000, "uo_out[0]", "y_comb"),
    ("y_reg",     310000, "uo_out[1]", "y_reg"),
]

# The unused digital outputs. Tiny Tapeout's analog spec is explicit that these
# must not float: "Connect any unused uo_out, uio_out and uio_oe pins to GND."
GND_BUS_Y = 295000
GND_TIED = ([f"uo_out[{i}]" for i in range(2, 8)]
            + [f"uio_out[{i}]" for i in range(8)]
            + [f"uio_oe[{i}]" for i in range(8)])


def stub_x(name):
    """Centre x of an interface stub, from the DEF template."""
    x1, _, x2, _ = DEF_PIN_RECT[name]
    return (x1 + x2) // 2


def drop_from_stub(name, bus_y):
    """Metal4 from the top-edge stub down to bus_y, and a via into the bus."""
    x = stub_x(name)
    box(top, METAL4, x - SPUR_HW, bus_y - BUS_HW, x + SPUR_HW, STUB_Y)
    pcell(top, "via_stack", x, bus_y,
          b_layer="Metal3", t_layer="Metal4", vn_columns=1, vn_rows=2)
    return x


def rise_to_macro(pin, bus_y):
    """Metal2 from the macro pin up to bus_y, and a via into the bus.

    The riser is exactly as wide as the pin, so it inherits the clearances
    LibreLane's own router already signed off inside the macro.
    """
    x = macro_pin_x(pin)
    box(top, METAL2, x - MACRO_PIN_HW, MACRO_Y + MACRO_PIN_Y,
        x + MACRO_PIN_HW, bus_y + BUS_HW)
    pcell(top, "via_stack", x, bus_y,
          b_layer="Metal2", t_layer="Metal3", vn_columns=1, vn_rows=2)
    return x


for _net, bus_y, stub, pin in DIGITAL_NETS:
    xs = (drop_from_stub(stub, bus_y), rise_to_macro(pin, bus_y))
    box(top, METAL3, min(xs), bus_y - BUS_HW, max(xs), bus_y + BUS_HW)
    # Name the net for LVS, on the Metal4 stub, under the tile interface name.
    label(top, stub, stub_x(stub), STUB_Y - 500, layer=M4_TEXT)

# The ground bus collects every unused output and ends on the VGND stripe.
gnd_xs = [drop_from_stub(name, GND_BUS_Y) for name in GND_TIED] + [VGND_X]
box(top, METAL3, min(gnd_xs), GND_BUS_Y - BUS_HW, max(gnd_xs), GND_BUS_Y + BUS_HW)
pcell(top, "via_stack", VGND_X, GND_BUS_Y,
      b_layer="Metal3", t_layer="TopMetal1", vn_columns=3, vn_rows=3)

# -------------------------------------------------- digital supply routing
# The macro's straps interleave VPWR, VGND, VPWR, VGND, so a horizontal bar on
# one layer cannot reach both nets without crossing the other. The two feeds
# therefore leave the macro on different layers, in the empty band below it:
# VGND on Metal4, VPWR on Metal3, one under the other. VGND's bar also passes
# under the VDPWR TopMetal1 stripe on its way to x = VGND_X, which is only
# harmless because it is not on TopMetal1.
VGND_FEED_Y, VPWR_FEED_Y = 232000, 236000
FEED_HW = MACRO_STRAP_HW


def strap_feed(strap_xs, feed_y, layer, stripe_x, b_layer):
    """Drop each strap to feed_y, run across to stripe_x, and via up to it."""
    for sx in strap_xs:
        x = MACRO_X + sx
        box(top, METAL4, x - FEED_HW, feed_y - FEED_HW,
            x + FEED_HW, MACRO_Y + MACRO_STRAP_Y0 + 1000)
        if layer is METAL3:
            pcell(top, "via_stack", x, feed_y,
                  b_layer="Metal3", t_layer="Metal4", vn_columns=3, vn_rows=3)
    xs = [MACRO_X + sx for sx in strap_xs] + [stripe_x]
    box(top, layer, min(xs), feed_y - FEED_HW, max(xs), feed_y + FEED_HW)
    pcell(top, "via_stack", stripe_x, feed_y,
          b_layer=b_layer, t_layer="TopMetal1", vn_columns=3, vn_rows=3)


strap_feed(MACRO_VGND_X, VGND_FEED_Y, METAL4, VGND_X, "Metal4")
strap_feed(MACRO_VPWR_X, VPWR_FEED_Y, METAL3, VDPWR_X, "Metal3")

# ------------------------------------------------------------------- output
# Tiny Tapeout's precheck requires the LEF to declare every pin in the tile
# interface, not just the ones this design connects to, and every declared pin
# must be backed by real metal, so draw every one of them. The pins this design
# drives (ua[0..1], uo_out[0..1]) and the ones tied to ground already have
# routing on them and the DEF rectangle just merges with it; what is left are
# the unused inputs, which are legitimately stubs.
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
