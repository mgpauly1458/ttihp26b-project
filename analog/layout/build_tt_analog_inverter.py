"""Build the hand-drawn CMOS inverter as a placeable hard macro.

    klayout -b -r analog/layout/build_tt_analog_inverter.py

Writes macro/tt_analog_inverter.gds and macro/tt_analog_inverter.lef. LibreLane
consumes both when it hardens the tile: the LEF for placement, routing and
keep-out, the GDS for the final stream-out. Nothing here knows about the tile.

The macro is shaped so the digital flow can treat it like an (oversized)
standard cell:

  * its footprint is a whole number of CoreSite widths (0.48um) by a whole
    number of rows (3.78um), so it lands row-aligned;
  * VPWR and VGND are horizontal Metal4 bars - one layer below the TopMetal1
    the tile's PDN runs vertically on, so pdngen has somewhere to drop a via,
    and spanning the full width so it does not matter where the pitch lands. Putting them
    on TopMetal1 itself leaves it nothing to connect ("[PDN-0232] the grid
    macro - u_inv does not contain any shapes or vias"). There are no Metal1
    rails: at this size a full-width rail crosses the core;
  * everything else inside the footprint is declared OBS on Metal1..Metal4, so
    the router cannot cross the analog block on any signal layer.

Shielding: the core sits inside a continuous p+ guard ring tied to VGND, and
the Metal1 inside the ring is a grounded plate wherever the core does not need
it, so the block is boxed in below the routing layers as well as beside them.

Coordinates are nm throughout (layout dbu = 1nm).
"""

import os
import sys

import pya

KT = "/foss/pdks/ihp-sg13g2/libs.tech/klayout"
sys.path += [
    os.path.join(KT, "python"),
    os.path.join(KT, "python", "pycell4klayout-api", "source", "python"),
]
import sg13g2_pycell_lib  # noqa: E402,F401  (registers the SG13_dev library)

MACRO = "tt_analog_inverter"
# The macro's GDS and LEF are COMMITTED, not build scratch: CI has no KLayout
# and no PDK PCell library, so LibreLane has to find them in the repository.
# Same reason analog/lib/tt_analog_inverter.lib is committed.
OUT = os.path.join(os.path.dirname(__file__), "..", "macro")

# ------------------------------------------------------------------- layers
ACTIV, GATPOLY, CONT, METAL1 = (1, 0), (5, 0), (6, 0), (8, 0)
PSD = (14, 0)                   # pSD.drawing: marks Activ as p+
METAL2, METAL3 = (10, 0), (30, 0)
NWELL, METAL4, TOPMETAL1 = (31, 0), (50, 0), (126, 0)
PWELL_BLOCK = (46, 0)          # not drawn; here so the numbers stay in one place
PRBOUND = (189, 4)             # prBoundary.boundary. 189/0 is not allowlisted.
HEATTRANS = (51, 0)            # drawn by the device PCells; not allowlisted
NBULAY = (32, 0)               # buried layer, drawn by the ntap1 PCell

# LVS reads net names off a .text purpose, one per metal layer. Labels on any
# other layer are silently ignored and the extracted netlist comes back with
# unnamed nets.
M1_TEXT, M2_TEXT, M4_TEXT = (8, 25), (10, 25), (50, 25)

# ---------------------------------------------------------------- floorplan
SITE_W, ROW_H = 480, 3780      # CoreSite: 0.48 x 3.78 um
COLS, ROWS = 42, 6
W, H = COLS * SITE_W, ROWS * ROW_H     # 20.16 x 22.68 um

# ------------------------------------------------------------ device sizing
W_P, W_N, L = "2.0u", "1.0u", "0.13u"

# Core-local device positions, unchanged from the standalone block: the devices
# are PDK PCells, so they are correct by construction and only the interconnect
# around them is hand-drawn.
Y_PTAP, Y_NMOS, Y_PMOS, Y_NTAP = -1400, 0, 2400, 4800

PAD_A = (-4000, 700, -250, 2760)
PAD_Y = (580, 1500, 4300, 3560)
PAD_VDD = (-800, 4890, 1000, 8000)
PAD_VSS = (-800, -3800, 1000, -700)

# Where the core sits inside the macro footprint. Centred horizontally, and low
# enough that the VDD pad clears the guard ring at the top.
CORE_X, CORE_Y = 9000, 8000

GUARD_W = 700                  # p+ guard ring conductor width
GUARD_MARGIN = 1200            # ring inset from the macro edge

# --------------------------------------------------------------- setup
ly = pya.Layout()
ly.dbu = 0.001
devlib = pya.Library.library_by_name("SG13_dev", "sg13g2")


def L_(t):
    return ly.layer(*t)


def box(cell, layer, x1, y1, x2, y2):
    cell.shapes(L_(layer)).insert(pya.Box(x1, y1, x2, y2))


def label(cell, text, x, y, layer=M1_TEXT):
    cell.shapes(L_(layer)).insert(pya.Text(text, pya.Trans(pya.Point(x, y))))


def pcell(cell, name, x, y, **params):
    pid = devlib.layout().pcell_id(name)
    var = ly.add_pcell_variant(devlib, pid, params)
    cell.insert(pya.CellInstArray(var, pya.Trans(pya.Point(x, y))))


def centre(rect):
    x1, y1, x2, y2 = rect
    return (x1 + x2) // 2, (y1 + y2) // 2


def shifted(rect, dx, dy):
    x1, y1, x2, y2 = rect
    return (x1 + dx, y1 + dy, x2 + dx, y2 + dy)


# ============================================================ inverter core
core = ly.create_cell("inverter_core")

pcell(core, "ptap1", 0, Y_PTAP)
pcell(core, "nmos", 0, Y_NMOS, w=W_N, l=L, ng="1")
pcell(core, "pmos", 0, Y_PMOS, w=W_P, l=L, ng="1")
pcell(core, "ntap1", 0, Y_NTAP)

# One generous NWell over the whole p-side. The pmos and ntap PCells each draw
# their own, and where those meet the tie is only marginally enclosed, which
# trips NW.d (min NWell space to external N+ Activ = 0.31um).
box(core, NWELL, -500, Y_PMOS - 500, 1300, Y_NTAP + 1300)

# Gate: bridge the two polys, then an arm left to the contact. The contact goes
# out here rather than inside the cell because at the gate's height the left
# column is empty, whereas anywhere inside, the Metal1 pad would land within
# minimum spacing of the Y strap.
box(core, GATPOLY, 340, Y_NMOS + 1180, 470, Y_PMOS - 180)
box(core, GATPOLY, -560, 1560, 470, 1900)
box(core, CONT, -480, 1650, -320, 1810)

# Risers from each device's left source/drain metal to its tap, and the output
# strap tying the two drains together on the right.
box(core, METAL1, 70, Y_PTAP + 90, 230, Y_NMOS + 1000)
box(core, METAL1, 70, Y_PMOS, 230, Y_NTAP + 690)
box(core, METAL1, 580, Y_NMOS, 740, Y_PMOS + 2000)

for pad in (PAD_A, PAD_Y, PAD_VDD, PAD_VSS):
    box(core, METAL1, *pad)

# ================================================================ the macro
macro = ly.create_cell(MACRO)
macro.insert(pya.CellInstArray(core.cell_index(), pya.Trans(pya.Point(CORE_X, CORE_Y))))
box(macro, PRBOUND, 0, 0, W, H)

A_PAD = shifted(PAD_A, CORE_X, CORE_Y)
Y_PAD = shifted(PAD_Y, CORE_X, CORE_Y)
VDD_PAD = shifted(PAD_VDD, CORE_X, CORE_Y)
VSS_PAD = shifted(PAD_VSS, CORE_X, CORE_Y)

# ------------------------------------------------------------- guard ring
# A continuous p+ ring tied to VGND: it collects substrate carriers injected by
# the switching logic outside and gives the inverter's bulk a low-impedance
# return right next to the devices. Drawn as four ptap-style edges rather than
# a PCell because no PCell draws a ring.
GX1, GY1 = GUARD_MARGIN, GUARD_MARGIN
GX2, GY2 = W - GUARD_MARGIN, H - GUARD_MARGIN

for x1, y1, x2, y2 in (
    (GX1, GY1, GX2, GY1 + GUARD_W),              # south
    (GX1, GY2 - GUARD_W, GX2, GY2),              # north
    (GX1, GY1, GX1 + GUARD_W, GY2),              # west
    (GX2 - GUARD_W, GY1, GX2, GY2),              # east
):
    box(macro, ACTIV, x1, y1, x2, y2)
    box(macro, METAL1, x1, y1, x2, y2)
    box(macro, PSD, x1 - 200, y1 - 200, x2 + 200, y2 + 200)
    # Contact array down the middle of the conductor. The vertical edges own
    # the corners; the horizontal ones stop short of them, because two rows of
    # contacts meeting at right angles merge into an L and every contact rule
    # (Cnt.b, CntB.a, CntB.a1, CntB.b2, M1.c1) is written for a square.
    step, size = 380, 160
    if x2 - x1 > y2 - y1:                        # horizontal edge
        cy = (y1 + y2) // 2 - size // 2
        for cx in range(x1 + GUARD_W + 200, x2 - GUARD_W - 200 - size, step):
            box(macro, CONT, cx, cy, cx + size, cy + size)
    else:                                        # vertical edge
        cx = (x1 + x2) // 2 - size // 2
        for cy in range(y1 + 200, y2 - 200 - size, step):
            box(macro, CONT, cx, cy, cx + size, cy + size)

# ------------------------------------------------------- power distribution
# No Metal1 rails. A hard macro of this shape cannot carry them: a rail spans
# the full width at every row line, and at this size some of those lines run
# straight across the core, shorting the output strap to the supply. (The first
# version did exactly that, and LVS extracted one merged `VPWR|Y` net.)
#
# Instead the supplies arrive the way a macro's supplies normally do: as straps
# on Metal4, which PDN_MACRO_CONNECTIONS then vias up to the tile's TopMetal1
# grid. The rows are blocked under the macro anyway, so there is nothing here
# for a rail to abut.
# The straps run HORIZONTALLY, spanning the full width. The tile's grid runs
# vertically at a 38.87um pitch, and a vertical macro strap only meets it where
# the two happen to line up: the first version put one strap under a grid strap
# and the other between two, and PSM found u_inv/VPWR unconnected while VGND
# was fine. A bar across the whole macro is met by any grid strap that crosses
# the macro at all, whatever the pitch does. The macro is placed so a full
# VPWR/VGND strap pair (8.4um apart) falls inside its 20.16um width, so both
# nets are always crossed.
#
# A grid strap of the other net simply passes over the bar without a via -
# pdngen only connects shapes of the same net - so the two bars can both span
# the full width without shorting.
TM_H = 2400                      # over PDN_VWIDTH, so the via array fits

# VGND sits over the guard ring's landing pad, VPWR over the core's VDD pad, so
# each bar has a Metal1 shape of its own net directly beneath it to via down to.
GND_LAND = (GX1, 5000, GX1 + 2400, 7400)
box(macro, METAL1, *GND_LAND)
box(macro, METAL1, GX1, VSS_PAD[1] + 400, VSS_PAD[2], VSS_PAD[1] + 1400)

via_x = {"VGND": (GND_LAND[0] + GND_LAND[2]) // 2,
         "VPWR": (VDD_PAD[0] + VDD_PAD[2]) // 2}
TM_Y = {"VGND": (GND_LAND[1] + GND_LAND[3]) // 2,
        "VPWR": (VDD_PAD[1] + VDD_PAD[3]) // 2}

tm_straps = {}
for net, y in TM_Y.items():
    rect = (0, y - TM_H // 2, W, y + TM_H // 2)
    tm_straps[net] = rect
    box(macro, METAL4, *rect)
    pcell(macro, "via_stack", via_x[net], y, b_layer="Metal1", t_layer="Metal4",
          vn_columns=3, vn_rows=3)

# --------------------------------------------------------------- signal pins
# A on the west edge, Y on the east, both brought up to Metal2 so the tile's
# router (which runs Metal1 horizontal, Metal2 vertical, ...) can reach them
# without having to enter the macro on Metal1.
PIN_W, PIN_H = 800, 1200
A_PIN = (0, 11000, PIN_W, 11000 + PIN_H)
Y_PIN = (W - PIN_W, 11000, W, 11000 + PIN_H)

for pin, pad in ((A_PIN, A_PAD), (Y_PIN, Y_PAD)):
    px, py = centre(pin)
    ax, ay = centre(pad)
    box(macro, METAL2, *pin)
    # Metal2 run from the edge pin across to over the core pad, then down.
    box(macro, METAL2, min(px, ax) - 200, py - 200, max(px, ax) + 200, py + 200)
    box(macro, METAL2, ax - 200, min(py, ay) - 200, ax + 200, max(py, ay) + 200)
    pcell(macro, "via_stack", ax, ay, b_layer="Metal1", t_layer="Metal2",
          vn_columns=2, vn_rows=2)

# ------------------------------------------------------------------ labels
label(macro, "VGND", W // 2, TM_Y["VGND"], layer=M4_TEXT)
label(macro, "VPWR", W // 2, TM_Y["VPWR"], layer=M4_TEXT)
label(macro, "A", *centre(A_PIN), layer=M2_TEXT)
label(macro, "Y", *centre(Y_PIN), layer=M2_TEXT)

# ------------------------------------------------------------- housekeeping
# HeatTrans is drawn by the device PCells, is not on Tiny Tapeout's allowlist,
# and plays no part in DRC or LVS.
#
# nBuLay goes too. ntap1 is the PDK's well-tap *device* - it has R and Rspec
# parameters - and draws a 1.26um buried-layer square as part of that device.
# A plain NWell tie does not need one, and Magic's signoff DRC measures it
# against the PMOS's own p+ diffusion 0.34um away: 33 NBL.f violations ("deep
# N-well spacing to P-diffusion < 0.5um"), which nothing in the tie can move
# far enough to satisfy. KLayout's deck never looks, which is why this only
# appeared once the tile went through LibreLane's signoff.
for cell in ly.each_cell():
    cell.shapes(L_(HEATTRANS)).clear()
    cell.shapes(L_(NBULAY)).clear()

# write_context_info off, or KLayout emits a hidden $$$CONTEXT_INFO$$$ cell
# holding the PCell parameters. It is a second top-level cell, and everything
# downstream that asks a GDS for "the" top cell then trips over it: LibreLane's
# render step fails with "the layout has multiple top cells", and Tiny Tapeout's
# precheck reads the wrong cell for its boundary and analog-pin checks.
opts = pya.SaveLayoutOptions()
opts.write_context_info = False
ly.write(os.path.join(OUT, f"{MACRO}.gds"), opts)

# =========================================================== LEF generation
# Emitted from the same constants as the geometry above, so the LEF can never
# describe a macro the GDS does not have.


def um(v):
    return f"{v / 1000.0:.3f}"


def rect(r):
    return f"        RECT {um(r[0])} {um(r[1])} {um(r[2])} {um(r[3])} ;"


def pin(name, direction, use, ports, extra=None):
    """ports: list of (layer_name, [rects])"""
    out = [f"  PIN {name}", f"    DIRECTION {direction} ;", f"    USE {use} ;"]
    if use in ("POWER", "GROUND"):
        out.append("    SHAPE ABUTMENT ;")
    out += extra or []
    for layer, rects in ports:
        out.append("    PORT")
        out.append(f"      LAYER {layer} ;")
        out += [rect(r) for r in rects]
        out.append("    END")
    out.append(f"  END {name}")
    return out


def subtract_windows(footprint, windows):
    """Footprint minus the pin windows, as a list of rectangles.

    KLayout does the geometry so the OBS can never accidentally overlap a pin,
    which a LEF reader rejects. The result is sliced into horizontal bands
    before it is read back, because a LEF OBS is a list of rectangles and the
    difference of two rectangles generally is not one.
    """
    reg = pya.Region(pya.Box(*footprint))
    for w in windows:
        reg -= pya.Region(pya.Box(*w))
    reg.merge()

    ys = {footprint[1], footprint[3]}
    for w in windows:
        ys.update((w[1], w[3]))
    ys = sorted(y for y in ys if footprint[1] <= y <= footprint[3])

    out = []
    for y1, y2 in zip(ys, ys[1:]):
        if y2 <= y1:
            continue
        band = reg & pya.Region(pya.Box(footprint[0], y1, footprint[2], y2))
        band.merge()
        for poly in band.each():
            b = poly.bbox()
            out.append((b.left, b.bottom, b.right, b.top))
    return out


FOOT = (0, 0, W, H)
GUARD = 200          # pull OBS back from a pin so no reader sees them touching


def grow(r, d):
    return (r[0] - d, r[1] - d, r[2] + d, r[3] + d)


obs = {
    # Metal1 carries nothing the tile may touch: the whole footprint is blocked.
    "Metal1": [FOOT],
    # Metal2: everything except the two signal pins.
    "Metal2": subtract_windows(FOOT, [grow(A_PIN, GUARD), grow(Y_PIN, GUARD)]),
    # Metal3 carries nothing of the macro's, so it is blocked outright.
    "Metal3": [FOOT],
    # Metal4 carries the two power straps and nothing else.
    "Metal4": subtract_windows(FOOT, [grow(r, GUARD) for r in tm_straps.values()]),
    # TopMetal1 is deliberately NOT blocked - that is where the PDN runs, and
    # a grounded strap over the block is a shield rather than a nuisance.
}

lines = [
    "VERSION 5.8 ;",
    'BUSBITCHARS "[]" ;',
    'DIVIDERCHAR "/" ;',
    "",
    f"MACRO {MACRO}",
    "  CLASS BLOCK ;",
    f"  FOREIGN {MACRO} 0 0 ;",
    "  ORIGIN 0 0 ;",
    f"  SIZE {um(W)} BY {um(H)} ;",
    "  SYMMETRY X Y ;",
    "  SITE CoreSite ;",
]
# Antenna areas, measured off the devices rather than guessed: A drives both
# gates (2.0 + 1.0 um of width at L = 0.13um), Y sees both drains (AD from the
# extracted netlist, 0.68p + 0.34p). Without these OpenROAD warns that the
# macro's pins "might not be connected to a gate" and skips antenna checking
# on every net that reaches them.
lines += pin("A", "INPUT", "SIGNAL", [("Metal2", [A_PIN])],
             extra=["    ANTENNAMODEL OXIDE1 ;",
                    "      ANTENNAGATEAREA 0.39 LAYER Metal2 ;"])
lines += pin("Y", "OUTPUT", "SIGNAL", [("Metal2", [Y_PIN])],
             extra=["    ANTENNADIFFAREA 1.02 LAYER Metal2 ;"])
lines += pin("VPWR", "INOUT", "POWER", [("Metal4", [tm_straps["VPWR"]])])
lines += pin("VGND", "INOUT", "GROUND", [("Metal4", [tm_straps["VGND"]])])
lines.append("  OBS")
for layer, rects in obs.items():
    lines.append(f"    LAYER {layer} ;")
    lines += [rect(r) for r in rects]
lines.append("  END")
lines += [f"END {MACRO}", "", "END LIBRARY", ""]

with open(os.path.join(OUT, f"{MACRO}.lef"), "w") as fh:
    fh.write("\n".join(lines))

print(f"wrote {MACRO}.gds and {MACRO}.lef  ({um(W)} x {um(H)} um, "
      f"{COLS} sites x {ROWS} rows)")
