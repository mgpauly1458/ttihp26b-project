"""Layout generator for the tt_analog_ring hard macro: current-starved ring oscillator + 8-bit current DAC (IHP SG13G2).

    klayout -b -r analog/layout/build_tt_analog_ring.py      (or: make gds)

Writes macro/tt_analog_ring.gds, macro/tt_analog_ring.lef, spice/tt_analog_ring.spice (X calls, one per finger,
for ngspice) and spice/tt_analog_ring.lvs.spice (M lines, for KLayout LVS). Ports: code[7:0] enable clk_out VPWR VGND.

Circuit: DAC = 255 unit NMOS fingers (0.15/8 um) binary weighted, gates on the code bits, drains on vbp, + NG_ON
always-on units so code 0 oscillates; vbp = diode PMOS MPD (24 x 2/0.5), so a stage's 1 um starve PMOS gets I_dac/48;
MPM mirrors into diode NMOS MND for vbn; ring = starved NAND(enable, feedback) + 10 starved inverters (starve devices
1/0.5 PMOS on vbp, 0.5/0.5 NMOS on vbn); buffer = two plain inverters to clk_out.
Layout: DAC rows at the bottom (34 rows in mirrored pairs sharing a Metal1 vbp bar, VGND bars outside, one poly gate
bar per row jogged in Metal1 to a vertical Metal2 code bus from the south-edge pins); one standard-cell-like row on top
(NMOS below, PMOS above, rails outside) with bias, feedback and enable on Metal2 in the gap and stage-to-stage Metal1
jogs there; VPWR/VGND as full-width Metal4 bars for the tile's PDN; grounded p+ guard ring; LEF OBS on Metal1..4 except pins.
- Every finger is placed through Mos, which records its nets; both netlists come from those records, so LVS checks
  the drawn metal and poly against the circuit this script meant.
- Coordinates in nm (dbu = 1 nm). Design-rule numbers from sg13g2_tech_default.json.
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

MACRO = "tt_analog_ring"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_MACRO = os.path.join(ROOT, "macro")
OUT_SPICE = os.path.join(ROOT, "spice")

# ------------------------------------------------------------------- layers
ACTIV, GATPOLY, CONT, METAL1 = (1, 0), (5, 0), (6, 0), (8, 0)
PSD = (14, 0)                   # pSD.drawing: marks Activ as p+
VIA1, METAL2, VIA2, METAL3 = (19, 0), (10, 0), (29, 0), (30, 0)
NWELL, METAL4 = (31, 0), (50, 0)
PRBOUND = (189, 4)             # prBoundary.boundary
HEATTRANS = (51, 0)            # drawn by the device PCells; not allowlisted
NBULAY = (32, 0)               # buried layer, drawn by ntap1 - not used here
M1_TEXT, M2_TEXT, M3_TEXT, M4_TEXT = (8, 25), (10, 25), (30, 25), (50, 25)

# ---------------------------------------------------------- design rules (nm)
# The numbers this layout is drawn against, from sg13g2_tech_default.json.
ACT_SP = 210          # Act.b   Activ space
GAT_SP = 180          # Gat.b   GatPoly space
GAT_EXT = 180         # Gat.c   GatPoly extension past Activ
CNT = 160             # Cnt.a   contact size
CNT_SP = 180          # Cnt.b   contact space
CNT_ENC = 70          # Cnt.c/d Activ / GatPoly enclosure of contact
M1_W, M1_SP = 160, 180
MN_W, MN_SP = 200, 210
NW_ENC = 310          # NW.c    NWell enclosure of p+ Activ
PSD_ENC = 180         # pSD.c   pSD enclosure of Activ (PCell value)
PSD_SP = 180          # pSD.d   pSD to n+ Activ

# ---------------------------------------------------------------- floorplan
SITE_W, ROW_H = 480, 3780      # CoreSite: 0.48 x 3.78 um

# ------------------------------------------------------------ device sizing
WU, LU = 0.15, 8.0             # DAC unit finger
WPS, LPS = 1.0, 0.5            # PMOS starve / mirror
WNS, LNS = 0.5, 0.5            # NMOS starve / mirror
WPI, WNI, LI = 0.5, 0.3, 0.13  # inverter devices
NG_MP0, WP0F = 24, 2.0         # diode PMOS: 24 fingers of 2um -> DAC-to-stage ratio 48
NG_ON = 2                      # always-on DAC units, so code 0 still oscillates
WNAND = 0.6                    # NAND series NMOS
WBP2, WBN2 = 2.0, 1.0          # output inverter

# --------------------------------------------------------------- setup
ly = pya.Layout()
ly.dbu = 0.001
devlib = pya.Library.library_by_name("SG13_dev", "sg13g2")


def L_(t):
    return ly.layer(*t)


def box(cell, layer, x1, y1, x2, y2):
    assert x2 > x1 and y2 > y1, (layer, x1, y1, x2, y2)
    cell.shapes(L_(layer)).insert(pya.Box(x1, y1, x2, y2))


def label(cell, text, x, y, layer=M1_TEXT):
    cell.shapes(L_(layer)).insert(pya.Text(text, pya.Trans(pya.Point(x, y))))


def pcell_var(name, **params):
    pid = devlib.layout().pcell_id(name)
    return ly.add_pcell_variant(devlib, pid, params)


def pcell(cell, name, x, y, **params):
    var = pcell_var(name, **params)
    cell.insert(pya.CellInstArray(var, pya.Trans(pya.Point(x, y))))
    return var


def cont(cell, cx, cy):
    """One contact centred at (cx, cy)."""
    box(cell, CONT, cx - CNT // 2, cy - CNT // 2, cx + CNT // 2, cy + CNT // 2)


def via12(cell, cx, cy):
    """Metal1 -> Metal2 via, single cut, with its own landing pads."""
    pcell(cell, "via_stack", cx, cy, b_layer="Metal1", t_layer="Metal2",
          vn_columns=1, vn_rows=1)


def via13(cell, cx, cy):
    pcell(cell, "via_stack", cx, cy, b_layer="Metal1", t_layer="Metal3",
          vn_columns=1, vn_rows=1)


def via14(cell, cx, cy):
    pcell(cell, "via_stack", cx, cy, b_layer="Metal1", t_layer="Metal4",
          vn_columns=3, vn_rows=3)


def um(v):
    return f"{v / 1000.0:.3f}"


# ================================================================ netlist
# Every transistor finger placed through Mos is recorded here.
DEVICES = []   # (name, kind, wf_um, l_um, drain, gate, source, bulk)


class Mos:
    """A PCell transistor at (x, y); pad and gate boxes are read back off the PCell, and every finger is recorded in DEVICES.

    kind    'nmos' | 'pmos'
    w, l    per-finger width and length in um
    ng      number of fingers
    cols    ng+1 net names, one per source/drain column, left to right
    gate    net name of the gate (all fingers share it)
    """

    def __init__(self, cell, name, kind, x, y, w, l, ng, cols, gate):
        assert len(cols) == ng + 1, (name, cols)
        self.name, self.kind, self.x, self.y = name, kind, x, y
        self.w, self.l, self.ng = w, l, ng
        self.cols, self.gate = cols, gate
        var = pcell(cell, kind, x, y, w=f"{w * ng:.3g}u", l=f"{l:.3g}u", ng=str(ng))
        vc = ly.cell(var)

        def boxes(layer):
            out = {}
            for s in vc.shapes(L_(layer)).each():
                b = s.bbox()
                if b.width() > 0 and b.height() > 0:
                    out[str(b)] = (b.left + x, b.bottom + y, b.right + x, b.top + y)
            return sorted(out.values())

        self.pads = boxes(METAL1)          # one per S/D column, left->right
        self.gates = boxes(GATPOLY)        # one per finger, left->right
        a = boxes(ACTIV)
        self.activ = (min(r[0] for r in a), min(r[1] for r in a),
                      max(r[2] for r in a), max(r[3] for r in a))
        assert len(self.pads) == ng + 1 and len(self.gates) == ng, (name, len(self.pads), len(self.gates))
        bulk = "VGND" if kind == "nmos" else "VPWR"
        for k in range(ng):
            DEVICES.append((f"{name}_{k}", kind, w, l, cols[k + 1], gate, cols[k], bulk))

    def pad(self, k):
        return self.pads[k]

    def gate_box(self, k=0):
        return self.gates[k]

    @property
    def right(self):
        return self.activ[2]


def write_netlists():
    ports = [f"code[{k}]" for k in range(8)] + ["enable", "clk_out", "VPWR", "VGND"]
    head = f".subckt {MACRO} " + " ".join(ports) + "\n"
    sim, lvs = [head], [head]
    for name, kind, w, l, d, g, s, b in DEVICES:
        model = "sg13_lv_" + kind
        sim.append(f"X{name} {d} {g} {s} {b} {model} w={w:.3g}u l={l:.3g}u ng=1\n")
        lvs.append(f"M{name} {d} {g} {s} {b} {model} w={w:.3g}u l={l:.3g}u\n")
    tail = ".ends\n"
    os.makedirs(OUT_SPICE, exist_ok=True)
    banner = (f"* {MACRO}: current-starved ring oscillator + 8-bit binary current DAC\n"
              f"* GENERATED by analog/layout/build_tt_analog_ring.py - do not edit.\n"
              f"* One line per transistor finger, as placed in the layout.\n")
    with open(os.path.join(OUT_SPICE, f"{MACRO}.spice"), "w") as fh:
        fh.write(banner + "* ngspice form: subcircuit calls into the PDK models.\n" + "".join(sim) + tail)
    with open(os.path.join(OUT_SPICE, f"{MACRO}.lvs.spice"), "w") as fh:
        fh.write(banner + "* LVS form: device lines, for KLayout.\n" + "".join(lvs) + tail)


# ===================================================================== DAC
# Unit finger nmos 0.15/8: PCell pads (Metal1, 160 wide) on y 20..280, channel Activ 75..225, gate poly -105..405.
# Rows are paired: lower row's poly bar above its fingers, upper row's below, the shared Metal1 vbp bar between
# the two poly bars, the VGND bar shared with the neighbouring pair outside.
DAC_UNITS = [(7, 8)] * 16 + [(6, 8)] * 8 + [(5, 8)] * 4 + [(4, 8)] * 2 + [(3, 8), (2, 4), (1, 2), (0, 1)]
NROWS = len(DAC_UNITS)                  # 34
for _b in range(8):
    assert sum(ng for b, ng in DAC_UNITS if b == _b) == 2 ** _b, _b
assert NROWS % 2 == 0

PAIR_PITCH = 2300
ROW1_DY = 1310                          # upper row of a pair, relative to the lower
BAR_LO = (405, 705)                     # poly bar y for the lower row
BAR_HI = (905, 1205)                    # poly bar y for the upper row
VBP_BAR = (660, 960)                    # shared Metal1 vbp bar
VGND_BAR = (1800, 2100)                 # shared Metal1 VGND bar, above the pair
NG_SPLIT = 4                            # fingers left of the substrate-tie column
TIE_GAP = 1500                          # gap between the two half-rows
TIE_W = 640                             # tie island: two contacts at 340 pitch

BUS_PITCH = 800                         # Metal2 code/enable bus, left of the DAC
BUS_X0 = -1200                          # bit 0 line, relative to the DAC origin
BUS_LINES = 9                           # code[7:0] + enable
DAC_X, DAC_Y = 12000, 4200


def bus_x(k):
    return DAC_X + BUS_X0 - k * BUS_PITCH


def build_dac(cell, ox, oy):
    """The DAC rows at (ox, oy) = bottom-left of the first row's Activ; returns (x right of the rows, y top)."""
    row_end = None
    yfirst = oy
    for r, (bit, ng) in enumerate(DAC_UNITS):
        pair, upper = divmod(r, 2)
        y = oy + pair * PAIR_PITCH + (ROW1_DY if upper else 0)
        halves = [(0, min(ng, NG_SPLIT))]
        if ng > NG_SPLIT:
            halves.append((1, ng - NG_SPLIT))
        bar_y = BAR_HI if upper else BAR_LO
        bar_y = (bar_y[0] + y - (ROW1_DY if upper else 0), bar_y[1] + y - (ROW1_DY if upper else 0))
        # The poly bar's y is defined relative to the pair's base (lower row).
        ybase = y - (ROW1_DY if upper else 0)
        bar_y = (BAR_HI if upper else BAR_LO)
        bar_y = (ybase + bar_y[0], ybase + bar_y[1])
        vbp_y = (ybase + VBP_BAR[0], ybase + VBP_BAR[1])
        vgnd_y = ((ybase + VGND_BAR[0], ybase + VGND_BAR[1]) if upper
                  else (ybase + VGND_BAR[0] - PAIR_PITCH, ybase + VGND_BAR[1] - PAIR_PITCH))
        x = ox
        last_gate_right = None
        for half, n in halves:
            hx = ox + half * (300 + NG_SPLIT * 8440 + TIE_GAP)
            cols = ["VGND" if k % 2 == 0 else "vbp" for k in range(n + 1)]
            m = Mos(cell, f"D{bit}r{r}h{half}", "nmos", hx, y, WU, LU, n, cols, f"code[{bit}]")
            for k, net in enumerate(cols):
                px1, py1, px2, py2 = m.pad(k)
                if net == "vbp":
                    y1, y2 = (vbp_y[1], py2) if upper else (py1, vbp_y[0])
                else:
                    y1, y2 = (py1, vgnd_y[0]) if upper else (vgnd_y[1], py2)
                box(cell, METAL1, px1, min(y1, y2), px2, max(y1, y2))
            # poly bar over this half's fingers
            g0, g1 = m.gate_box(0), m.gate_box(n - 1)
            box(cell, GATPOLY, g0[0], bar_y[0], g1[2], bar_y[1])
            last_gate_right = g1[2]
            row_end = max(row_end or 0, m.right)
        # bridge the bar across the tie gap and out to the left for its contact
        bar_x0 = ox - 620
        box(cell, GATPOLY, bar_x0, bar_y[0], last_gate_right, bar_y[1])
        cy = (bar_y[0] + bar_y[1]) // 2
        cont(cell, ox - 460, cy)
        # Metal1 jog to the bus line, via onto it
        box(cell, METAL1, bus_x(bit) - 145, cy - 100, ox - 300, cy + 100)
        via12(cell, bus_x(bit), cy)
    # the rows all done: shared bars span the full row width to the trunks
    ytop = oy + (NROWS // 2 - 1) * PAIR_PITCH + ROW1_DY + 300
    return row_end, ytop


# ================================================================= the macro
macro = ly.create_cell(MACRO)

# ------------------------------------------------------------- floorplan
GUARD_MARGIN, GUARD_W = 1200, 700
ROW_W = 2 * (300 + NG_SPLIT * 8440) + TIE_GAP           # 69420
TRUNK_VBP_X = DAC_X + ROW_W + 500                        # Metal2 vertical, 400 wide
TRUNK_VGND_X = TRUNK_VBP_X + 400 + 400                    # Metal1 vertical, 800 wide
X_RIGHT = TRUNK_VGND_X + 800

row_end, dac_top = build_dac(macro, DAC_X, DAC_Y)

# shared Metal1 bars: vbp between the rows of a pair, VGND above each pair
# and below the first, all spanning from the first column to the trunks.
NPAIRS = NROWS // 2
for pair in range(NPAIRS):
    yb = DAC_Y + pair * PAIR_PITCH
    box(macro, METAL1, DAC_X + 70, yb + VBP_BAR[0], TRUNK_VBP_X + 400, yb + VBP_BAR[1])
    via12(macro, TRUNK_VBP_X + 200, yb + (VBP_BAR[0] + VBP_BAR[1]) // 2)
    box(macro, METAL1, DAC_X + 70, yb + VGND_BAR[0], X_RIGHT, yb + VGND_BAR[1])
y0 = DAC_Y + VGND_BAR[0] - PAIR_PITCH
box(macro, METAL1, DAC_X + 70, y0, X_RIGHT, y0 + 300)
DAC_VGND_BOT = y0
DAC_VGND_TOP = DAC_Y + (NPAIRS - 1) * PAIR_PITCH + VGND_BAR[0]

# substrate tie islands under every VGND bar (middle column and both row ends): no finger further than LU.b (20 um)
# from a tie. The bars extend left over the second island; the poly-bar jogs use other y slots.
TIE_X = DAC_X + 300 + NG_SPLIT * 8440 + (TIE_GAP - TIE_W) // 2
TIE_XL = DAC_X - 1000 - TIE_W
TIE_XR = DAC_X + ROW_W + 400
for pair in range(NPAIRS + 1):
    yb = DAC_VGND_BOT + pair * PAIR_PITCH
    box(macro, METAL1, TIE_XL - 100, yb, DAC_X + 100, yb + 300)
    for tx in (TIE_X, TIE_XL, TIE_XR):
        box(macro, ACTIV, tx, yb, tx + TIE_W, yb + 300)
        box(macro, PSD, tx - PSD_ENC, yb - PSD_ENC, tx + TIE_W + PSD_ENC, yb + 300 + PSD_ENC)
        cont(macro, tx + 150, yb + 150)
        cont(macro, tx + 490, yb + 150)

# trunks: vbp on Metal2 (vertical) up to the ring row, VGND on Metal1
box(macro, METAL2, TRUNK_VBP_X, DAC_Y + VBP_BAR[0], TRUNK_VBP_X + 400, DAC_VGND_TOP + 300)
box(macro, METAL1, TRUNK_VGND_X, DAC_VGND_BOT, TRUNK_VGND_X + 800, DAC_VGND_TOP + 300)

# Metal2 code bus from the south-edge pins up to the last row using each bit (enable continues to the ring row)
PIN_H = 1200
row_top_of_bit = {}
for r, (bit, ng) in enumerate(DAC_UNITS):
    pair, upper = divmod(r, 2)
    ybase = DAC_Y + pair * PAIR_PITCH
    bar = BAR_HI if upper else BAR_LO
    row_top_of_bit[bit] = ybase + (bar[0] + bar[1]) // 2
for bit in range(8):
    box(macro, METAL2, bus_x(bit) - 100, 0, bus_x(bit) + 100, row_top_of_bit[bit])
ENABLE_X = bus_x(8)

# ================================================================ ring row
# y positions inside the row, relative to the NMOS Activ bottom (RY).
Y_IN = 1500                     # slot A: stage inputs, Metal1 jogs
Y_BN = 2100                     # slot B: vbn, Metal2 line
Y_BP = 2650                     # slot C: vbp, Metal2 line
Y_FB = 3200                     # slot D: feedback, Metal2 line
Y_EN = 3750                     # slot E: enable, Metal2 line
YP = 4300                       # PMOS Activ bottom
Y_CLK = 1200                    # clk_out on Metal3 (its Metal2 pad sits in slot A)
RAIL_H = 1100
VGND_RAIL = (-1500, -400)
VPWR_RAIL = (YP + 2000 + 300 + 200, YP + 2000 + 300 + 200 + RAIL_H)   # above the tallest PMOS

RY = DAC_VGND_TOP - VGND_RAIL[0]   # ring row origin y: its VGND rail starts on the DAC's top bar
RX = DAC_X


def ry(v):
    return RY + v


def slot_pad(y):
    """Metal1 pad box y-range for a contact slot centred on y+80."""
    return (y - 70, y + 230)


def m2_line(y):
    return (y - 20, y + 180)


class Row:
    """Places devices left to right in the ring row and wires them."""

    def __init__(self, cell, x0):
        self.cell = cell
        self.x = x0
        self.vbn_x = []      # x positions of vbn contact pads (for the Metal2 line extent)
        self.vbp_x = []

    # -- primitives ------------------------------------------------------
    def strap_down(self, pad):
        """Metal1 from an NMOS pad down to the VGND rail."""
        box(self.cell, METAL1, pad[0], ry(VGND_RAIL[1]) - 10, pad[2], pad[3])

    def strap_up(self, pad):
        """Metal1 from a PMOS pad up to the VPWR rail."""
        box(self.cell, METAL1, pad[0], pad[1], pad[2], ry(VPWR_RAIL[0]) + 10)

    def strap_to(self, pad, y):
        """Metal1 from a pad to the row-relative y (through the gap)."""
        y1, y2 = sorted((ry(y), (pad[1] + pad[3]) // 2))
        box(self.cell, METAL1, pad[0], min(y1, pad[1]), pad[2], max(y2, pad[3]))

    def bias_stub(self, gate, net, slot_y, up):
        """Poly stub from a gate finger to a contact in slot B or C, Metal1 pad,
        via onto the Metal2 bias line. Returns the pad box."""
        gx1, gy1, gx2, gy2 = gate
        cy = ry(slot_y) + 80
        if up:      # NMOS gate: stub goes up from the gate top
            box(self.cell, GATPOLY, gx1, gy2 - 10, gx2, cy + CNT // 2 + CNT_ENC)
        else:       # PMOS gate: stub goes down from the gate bottom
            box(self.cell, GATPOLY, gx1, cy - CNT // 2 - CNT_ENC, gx2, gy1 + 10)
        cx = (gx1 + gx2) // 2
        cont(self.cell, cx, cy)
        p1, p2 = slot_pad(slot_y)
        pad = (cx - 160, ry(p1), cx + 160, ry(p2))
        box(self.cell, METAL1, *pad)
        via12(self.cell, cx, cy)
        (self.vbn_x if net == "vbn" else self.vbp_x).append(cx)
        return pad

    def in_bridge(self, ng, pg, slot_y=Y_IN, pad_left=True, net_line=None):
        """Poly bridge joining an NMOS gate and the PMOS gate above it, contact + Metal1 pad in the slot (widened to the
        left so the pad clears the output strap on the right); via to Metal2 if net_line. Returns the Metal1 pad box."""
        nx1, ny1, nx2, ny2 = ng
        px1, py1, px2, py2 = pg
        assert nx1 == px1, "gates must align"
        box(self.cell, GATPOLY, nx1, ny2 - 10, nx2, py1 + 10)
        cy = ry(slot_y) + 80
        if pad_left:
            poly = (nx1 - 280, cy - 150, nx2, cy + 150)
            cx = nx1 - 130
        else:
            poly = (nx1, cy - 150, nx2 + 420, cy + 150)
            cx = nx2 + 250
        box(self.cell, GATPOLY, *poly)
        cont(self.cell, cx, cy)
        pad = (cx - 160, cy - 150, cx + 160, cy + 150)
        box(self.cell, METAL1, *pad)
        if net_line is not None:
            via12(self.cell, cx, cy)
        return pad

    def jog(self, x1, x2, slot_y=Y_IN):
        """Metal1 jog in a slot between two x positions."""
        cy = ry(slot_y) + 80
        box(self.cell, METAL1, min(x1, x2), cy - 80, max(x1, x2), cy + 80)

    # -- cells ------------------------------------------------------------
    def stage(self, i, net_in, net_out):
        """Starved inverter: [Mns|Mn] below, [Mps|Mp] above. Returns (input pad box, (output strap centre x, x1, x2))."""
        x = self.x
        mns = Mos(self.cell, f"MNS{i}", "nmos", x, ry(0), WNS, LNS, 1, ["VGND", f"n{i}"], "vbn")
        mps = Mos(self.cell, f"MPS{i}", "pmos", x, ry(YP), WPS, LPS, 1, ["VPWR", f"p{i}"], "vbp")
        xi = mns.right + ACT_SP
        mn = Mos(self.cell, f"MN{i}", "nmos", xi, ry(0), WNI, LI, 1, [f"n{i}", net_out], net_in)
        mp = Mos(self.cell, f"MP{i}", "pmos", xi, ry(YP), WPI, LI, 1, [f"p{i}", net_out], net_in)
        self.strap_down(mns.pad(0))
        self.strap_up(mps.pad(0))
        # internal nodes: short Metal1 straps along the bottom / top pad edges
        a, b = mns.pad(1), mn.pad(0)
        box(self.cell, METAL1, a[0], a[1], b[2], a[1] + M1_W)
        a, b = mps.pad(1), mp.pad(0)
        box(self.cell, METAL1, a[0], a[1], b[2], a[1] + M1_W)
        self.bias_stub(mns.gate_box(), "vbn", Y_BN, up=True)
        self.bias_stub(mps.gate_box(), "vbp", Y_BP, up=False)
        pad = self.in_bridge(mn.gate_box(), mp.gate_box())
        # output: one Metal1 strap from the NMOS drain pad to the PMOS drain pad
        o1, o2 = mn.pad(1), mp.pad(1)
        box(self.cell, METAL1, o1[0], o1[1], o2[2], o2[3])
        label(self.cell, net_out, (o1[0] + o1[2]) // 2, ry(Y_IN) + 80)
        self.x = mn.right + 400
        return pad, ((o1[0] + o1[2]) // 2, o1[0], o1[2])

    def nand(self, net_out, net_fb):
        x = self.x
        mns = Mos(self.cell, "MNS0", "nmos", x, ry(0), WNS, LNS, 1, ["VGND", "n0"], "vbn")
        mps = Mos(self.cell, "MPS0", "pmos", x, ry(YP), WPS, LPS, 1, ["VPWR", "p0"], "vbp")
        xi = mns.right + ACT_SP
        mn = Mos(self.cell, "MNA0", "nmos", xi, ry(0), WNAND, LI, 2, ["n0", "na0", net_out], "enable")
        # two fingers with different gates: the PCell gives separate poly, finger 1 is relabelled to net_fb below
        mp = Mos(self.cell, "MPA0", "pmos", xi, ry(YP), WPI, LI, 2, ["p0", net_out, "p0"], "enable")
        # fix the netlist records for finger 1 (gate = feedback)
        for idx, d in enumerate(DEVICES):
            if d[0] in ("MNA0_1", "MPA0_1"):
                DEVICES[idx] = (d[0], d[1], d[2], d[3], d[4], net_fb, d[6], d[7])
        self.strap_down(mns.pad(0))
        self.strap_up(mps.pad(0))
        a, b = mns.pad(1), mn.pad(0)
        box(self.cell, METAL1, a[0], a[1], b[2], a[1] + M1_W)
        a, b = mps.pad(1), mp.pad(0)
        box(self.cell, METAL1, a[0], a[1], b[2], a[1] + M1_W)
        # PMOS finger 1's outer column is p0 too: jog over the top of the device
        c0, c2 = mp.pad(0), mp.pad(2)
        yj = c0[3] + GAT_EXT + M1_SP + 20
        box(self.cell, METAL1, c0[0], c0[3] - 10, c0[2], yj + M1_W)
        box(self.cell, METAL1, c2[0], c2[3] - 10, c2[2], yj + M1_W)
        box(self.cell, METAL1, c0[0], yj, c2[2], yj + M1_W)
        self.bias_stub(mns.gate_box(), "vbn", Y_BN, up=True)
        self.bias_stub(mps.gate_box(), "vbp", Y_BP, up=False)
        # enable gate (finger 0): contact in slot E, via to the enable line
        en_pad = self.in_bridge(mn.gate_box(0), mp.gate_box(0), slot_y=Y_EN, pad_left=True, net_line="enable")
        # feedback gate (finger 1): contact in slot D, pad to the right
        self.in_bridge(mn.gate_box(1), mp.gate_box(1), slot_y=Y_FB, pad_left=False, net_line="fb")
        # output: NMOS column 2 up into slot A, PMOS column 1 down into slot A, jog
        on, op = mn.pad(2), mp.pad(1)
        self.strap_to(on, Y_IN + 80)
        self.strap_to(op, Y_IN + 80)
        self.jog(op[0], on[2])
        label(self.cell, net_out, (on[0] + on[2]) // 2, ry(Y_IN) + 80)
        self.en_x = (en_pad[0] + en_pad[2]) // 2
        self.x = mn.right + 400
        return ((on[0] + on[2]) // 2, on[0], on[2])

    def inverter(self, name, net_in, net_out, wp, wn, cols_out_right=True):
        """Unstarved inverter [VGND|in|out] / [VPWR|in|out]."""
        x = self.x
        mn = Mos(self.cell, f"{name}N", "nmos", x, ry(0), wn, LI, 1, ["VGND", net_out], net_in)
        mp = Mos(self.cell, f"{name}P", "pmos", x, ry(YP), wp, LI, 1, ["VPWR", net_out], net_in)
        self.strap_down(mn.pad(0))
        self.strap_up(mp.pad(0))
        pad = self.in_bridge(mn.gate_box(), mp.gate_box())
        o1, o2 = mn.pad(1), mp.pad(1)
        box(self.cell, METAL1, o1[0], o1[1], o2[2], o2[3])
        label(self.cell, net_out, (o1[0] + o1[2]) // 2, ry(Y_IN) + 80)
        self.x = mn.right + 400
        return pad, ((o1[0] + o1[2]) // 2, o1[0], o1[2])


row = Row(macro, RX + 600)

# --- always-on units: NMOS 0.15/8 fingers, gate on VPWR, drain on vbp -------
don_cols = ["VGND" if k % 2 == 0 else "vbp" for k in range(NG_ON + 1)]
don = Mos(macro, "DON", "nmos", row.x, ry(0), WU, LU, NG_ON, don_cols, "VPWR")
p1, p2 = slot_pad(Y_BP)
for k, net in enumerate(don_cols):
    if net == "VGND":
        row.strap_down(don.pad(k))
    else:
        row.strap_to(don.pad(k), Y_BP + 80)
        d1 = don.pad(k)
        box(macro, METAL1, d1[0] - 80, ry(p1), d1[2] + 80, ry(p2))
        via12(macro, (d1[0] + d1[2]) // 2, ry(Y_BP) + 80)
        row.vbp_x.append((d1[0] + d1[2]) // 2)
# gate: poly bar over the fingers' top ends, stub to a contact in slot A, Metal1 straight up through the empty PMOS row to VPWR
g0, gl = don.gate_box(0), don.gate_box(NG_ON - 1)
box(macro, GATPOLY, g0[0], g0[3] - 10, gl[2], g0[3] + 300)
gx = g0[0] + 150
box(macro, GATPOLY, g0[0], g0[3] + 290, g0[0] + 300, ry(Y_IN) + 80 + CNT // 2 + CNT_ENC)
cont(macro, gx, ry(Y_IN) + 80)
box(macro, METAL1, gx - 130, ry(Y_IN) - 70, gx + 130, ry(VPWR_RAIL[0]) + 10)
row.x = don.right + 600

# --- bias: MPD diode PMOS (24 fingers), MND diode NMOS, MPM mirror PMOS (names distinct from the stages' MP<i>/MN<i>)
mp0_cols = ["VPWR" if k % 2 == 0 else "vbp" for k in range(NG_MP0 + 1)]
mp0 = Mos(macro, "MPD", "pmos", row.x, ry(YP), WP0F, LPS, NG_MP0, mp0_cols, "vbp")
for k, net in enumerate(mp0_cols):
    if net == "VPWR":
        row.strap_up(mp0.pad(k))
    else:
        row.strap_to(mp0.pad(k), Y_BP + 80)
# vbp bar under Mp0 in slot C, joining all drain straps, via to the vbp line
p1, p2 = slot_pad(Y_BP)
box(macro, METAL1, mp0.pad(1)[0] - 80, ry(p1), mp0.pad(NG_MP0 - 1)[2] + 80, ry(p2))
for k in (1, NG_MP0 // 2 + 1, NG_MP0 - 1):
    via12(macro, (mp0.pad(k)[0] + mp0.pad(k)[2]) // 2, ry(Y_BP) + 80)
    row.vbp_x.append((mp0.pad(k)[0] + mp0.pad(k)[2]) // 2)
# gate bar below the fingers, contact at its left end, Metal1 down to the vbp bar
g0, gl = mp0.gate_box(0), mp0.gate_box(NG_MP0 - 1)
bar_y2 = g0[1] + 10
bar_y1 = bar_y2 - 300 - 10
box(macro, GATPOLY, g0[0] - 620, bar_y1, gl[2], bar_y2)
cy = (bar_y1 + bar_y2) // 2
cont(macro, g0[0] - 460, cy)
box(macro, METAL1, g0[0] - 590, ry(Y_BP) - 70, g0[0] - 330, cy + 150)
box(macro, METAL1, g0[0] - 590, ry(p1), mp0.pad(1)[2], ry(p2))

# MND sits under MPD in the free NMOS row; MPM needs free PMOS row, so it goes after MPD
row.x = mp0.right + 600
mn0 = Mos(macro, "MND", "nmos", mp0.x + 1000, ry(0), WNS, LNS, 1, ["VGND", "vbn"], "vbn")
row.strap_down(mn0.pad(0))
row.strap_to(mn0.pad(1), Y_BN + 80)
pad = row.bias_stub(mn0.gate_box(), "vbn", Y_BN, up=True)
d1 = mn0.pad(1)
box(macro, METAL1, pad[0], pad[1], d1[2] + 80, pad[3])

mp1 = Mos(macro, "MPM", "pmos", row.x, ry(YP), WPS, LPS, 1, ["VPWR", "vbn"], "vbp")
row.strap_up(mp1.pad(0))
row.strap_to(mp1.pad(1), Y_BN + 80)
row.bias_stub(mp1.gate_box(), "vbp", Y_BP, up=False)
d1 = mp1.pad(1)
p1, p2 = slot_pad(Y_BN)
box(macro, METAL1, d1[0] - 80, ry(p1), d1[2] + 80, ry(p2))
via12(macro, (d1[0] + d1[2]) // 2, ry(Y_BN) + 80)
row.vbn_x.append((d1[0] + d1[2]) // 2)
row.x = mp1.right + 600

# --- the ring: NAND then ten stages -----------------------------------------
nand_out = row.nand("s0", "s10")
prev = nand_out
for i in range(1, 11):
    pad, out = row.stage(i, f"s{i - 1}", f"s{i}")
    row.jog(prev[2] - 10, pad[0] + 10)
    prev = out
# feedback: last stage output strap up to slot D, via onto the fb line
fb_x = prev[0]
via12(macro, fb_x, ry(Y_FB) + 80)
# --- buffer from s10 --------------------------------------------------------
pad, b1 = row.inverter("MB1", "s10", "b1", WPI, WNI)
row.jog(prev[2] - 10, pad[0] + 10)
pad, clk = row.inverter("MB2", "b1", "clk_out", WBP2, WBN2)
row.jog(b1[2] - 10, pad[0] + 10)
ROW_END = row.x

# --- Metal2 lines in the gap -------------------------------------------------
xl, xr = min(row.vbn_x) - 200, max(row.vbn_x) + 200
box(macro, METAL2, xl, ry(m2_line(Y_BN)[0]), xr, ry(m2_line(Y_BN)[1]))
xl = min(row.vbp_x) - 200
box(macro, METAL2, xl, ry(m2_line(Y_BP)[0]), TRUNK_VBP_X + 400, ry(m2_line(Y_BP)[1]))
# vbp trunk continues up from the DAC into slot C
box(macro, METAL2, TRUNK_VBP_X, DAC_VGND_TOP, TRUNK_VBP_X + 400, ry(m2_line(Y_BP)[1]))
# feedback line: from the NAND's fb pad to the last stage's via
box(macro, METAL2, row.en_x, ry(m2_line(Y_FB)[0]), fb_x + 150, ry(m2_line(Y_FB)[1]))
# enable line: from the bus line, up and across slot E to the NAND
box(macro, METAL2, ENABLE_X - 100, 0, ENABLE_X + 100, ry(m2_line(Y_EN)[1]))
box(macro, METAL2, ENABLE_X - 100, ry(m2_line(Y_EN)[0]), row.en_x + 150, ry(m2_line(Y_EN)[1]))

# --- clk_out: via stack to Metal3 on the output strap, east to the pin ------
via13(macro, clk[0], ry(Y_CLK))
CLK_Y = ry(Y_CLK)
# the stack's Metal2 landing pad is alone on Metal2: pad it out to Mn.d min area
box(macro, METAL2, clk[0] - 200, CLK_Y - 200, clk[0] + 200, CLK_Y + 200)

# --- rails ------------------------------------------------------------------
RAIL_X1, RAIL_X2 = RX, ROW_END + 2000
box(macro, METAL1, RAIL_X1, ry(VGND_RAIL[0]), X_RIGHT, ry(VGND_RAIL[1]))
box(macro, METAL1, RAIL_X1, ry(VPWR_RAIL[0]), RAIL_X2, ry(VPWR_RAIL[1]))
# VGND rail meets the DAC's VGND trunk (they overlap in y by construction)
assert ry(VGND_RAIL[0]) < DAC_VGND_TOP + 300, "ring VGND rail must overlap the DAC's top bar"

# well and implant bands over the PMOS row; taps under the rails
NW_Y1 = ry(YP) - NW_ENC
NW_Y2 = ry(VPWR_RAIL[1]) + NW_ENC
box(macro, NWELL, RAIL_X1 - 600, NW_Y1, RAIL_X2 + 600, NW_Y2)
box(macro, PSD, RAIL_X1 - 600, ry(YP) - 300, RAIL_X2 + 600, ry(YP) + 2000 + 300)
for x in range(RAIL_X1 + 1500, RAIL_X2 - 1500, 9000):
    # n+ NWell tie under the VPWR rail
    y = ry(VPWR_RAIL[0]) + 300
    box(macro, ACTIV, x, y, x + 640, y + 640)
    for dx in (150, 490):
        for dy in (150, 490):
            cont(macro, x + dx, y + dy)
    # p+ substrate tie under the VGND rail
    y = ry(VGND_RAIL[0]) + 300
    box(macro, ACTIV, x, y, x + 640, y + 640)
    box(macro, PSD, x - PSD_ENC, y - PSD_ENC, x + 640 + PSD_ENC, y + 640 + PSD_ENC)
    for dx in (150, 490):
        for dy in (150, 490):
            cont(macro, x + dx, y + dy)

# --- macro outline ---------------------------------------------------------
W = max(X_RIGHT, RAIL_X2) + 2600
H = ry(VPWR_RAIL[1]) + 2600
W = -(-W // SITE_W) * SITE_W
H = -(-H // ROW_H) * ROW_H
box(macro, PRBOUND, 0, 0, W, H)

# --- guard ring ------------------------------------------------------------
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
    step, size = 380, 160
    if x2 - x1 > y2 - y1:                        # horizontal edge
        cy = (y1 + y2) // 2 - size // 2
        for cx in range(x1 + GUARD_W + 200, x2 - GUARD_W - 200 - size, step):
            box(macro, CONT, cx, cy, cx + size, cy + size)
    else:                                        # vertical edge
        cx = (x1 + x2) // 2 - size // 2
        for cy in range(y1 + 200, y2 - 200 - size, step):
            box(macro, CONT, cx, cy, cx + size, cy + size)
# tie the guard ring to VGND: the VGND rail and the DAC's VGND trunk reach the east edge
box(macro, METAL1, X_RIGHT - 10, ry(VGND_RAIL[0]), GX2, ry(VGND_RAIL[1]))
box(macro, METAL1, X_RIGHT - 10, DAC_VGND_BOT, GX2, DAC_VGND_BOT + 300)

# --- Metal4 power bars ------------------------------------------------------
TM_H = 2400
tm_straps = {}
for net, rail in (("VGND", VGND_RAIL), ("VPWR", VPWR_RAIL)):
    yc = ry((rail[0] + rail[1]) // 2)
    rect = (0, yc - TM_H // 2, W, yc + TM_H // 2)
    tm_straps[net] = rect
    box(macro, METAL4, *rect)
    label(macro, net, W // 2, yc, layer=M4_TEXT)
    xs = range(RAIL_X1 + 3000, (X_RIGHT if net == "VGND" else RAIL_X2) - 2000, 12000)
    for x in xs:
        if abs(x - TRUNK_VBP_X - 200) < 1500 or abs(x - ENABLE_X) < 1500:
            continue
        via14(macro, x, yc)

# --- signal pins ------------------------------------------------------------
PIN_W = 400
pins = {}
for k in range(8):
    x = bus_x(k)
    pins[f"code[{k}]"] = ("Metal2", (x - PIN_W // 2, 0, x + PIN_W // 2, PIN_H))
    box(macro, METAL2, x - PIN_W // 2, 0, x + PIN_W // 2, PIN_H)
    label(macro, f"code[{k}]", x, PIN_H // 2, layer=M2_TEXT)
pins["enable"] = ("Metal2", (ENABLE_X - PIN_W // 2, 0, ENABLE_X + PIN_W // 2, PIN_H))
box(macro, METAL2, ENABLE_X - PIN_W // 2, 0, ENABLE_X + PIN_W // 2, PIN_H)
label(macro, "enable", ENABLE_X, PIN_H // 2, layer=M2_TEXT)
box(macro, METAL3, clk[0] - 145, CLK_Y - 200, W, CLK_Y + 200)
pins["clk_out"] = ("Metal3", (W - PIN_H, CLK_Y - 200, W, CLK_Y + 200))
label(macro, "clk_out", W - PIN_H // 2, CLK_Y, layer=M3_TEXT)
label(macro, "vbp", TRUNK_VBP_X + 200, DAC_Y + 5000, layer=M2_TEXT)
label(macro, "vbn", row.vbn_x[0], ry(Y_BN) + 80, layer=M2_TEXT)

# ------------------------------------------------------------- housekeeping
for cell in ly.each_cell():
    cell.shapes(L_(HEATTRANS)).clear()
    cell.shapes(L_(NBULAY)).clear()

opts = pya.SaveLayoutOptions()
opts.write_context_info = False
os.makedirs(OUT_MACRO, exist_ok=True)
ly.write(os.path.join(OUT_MACRO, f"{MACRO}.gds"), opts)
write_netlists()

# =========================================================== LEF generation


def rect(r):
    return f"        RECT {um(r[0])} {um(r[1])} {um(r[2])} {um(r[3])} ;"


def pin(name, direction, use, ports, extra=None):
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
GUARD = 200


def grow(r, d):
    return (r[0] - d, r[1] - d, r[2] + d, r[3] + d)


obs = {
    "Metal1": [FOOT],
    "Metal2": subtract_windows(FOOT, [grow(r, GUARD) for l, r in pins.values() if l == "Metal2"]),
    "Metal3": subtract_windows(FOOT, [grow(r, GUARD) for l, r in pins.values() if l == "Metal3"]),
    "Metal4": subtract_windows(FOOT, [grow(r, GUARD) for r in tm_straps.values()]),
}

# antenna: code[k] drives 2^k unit gates, enable the two NAND gates; clk_out sees the output inverter's two drains
unit_gate = WU * LU
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
for k in range(8):
    layer, r = pins[f"code[{k}]"]
    lines += pin(f"code[{k}]", "INPUT", "SIGNAL", [(layer, [r])],
                 extra=["    ANTENNAMODEL OXIDE1 ;",
                        f"      ANTENNAGATEAREA {unit_gate * 2 ** k:.3f} LAYER {layer} ;"])
layer, r = pins["enable"]
lines += pin("enable", "INPUT", "SIGNAL", [(layer, [r])],
             extra=["    ANTENNAMODEL OXIDE1 ;",
                    f"      ANTENNAGATEAREA {(WNAND + WPI) * LI:.3f} LAYER {layer} ;"])
layer, r = pins["clk_out"]
lines += pin("clk_out", "OUTPUT", "SIGNAL", [(layer, [r])],
             extra=[f"    ANTENNADIFFAREA {(WBP2 + WBN2) * 0.34:.3f} LAYER {layer} ;"])
lines += pin("VPWR", "INOUT", "POWER", [("Metal4", [tm_straps["VPWR"]])])
lines += pin("VGND", "INOUT", "GROUND", [("Metal4", [tm_straps["VGND"]])])
lines.append("  OBS")
for layer, rects in obs.items():
    lines.append(f"    LAYER {layer} ;")
    lines += [rect(r) for r in rects]
lines.append("  END")
lines += [f"END {MACRO}", "", "END LIBRARY", ""]
with open(os.path.join(OUT_MACRO, f"{MACRO}.lef"), "w") as fh:
    fh.write("\n".join(lines))

print(f"wrote {MACRO}.gds, {MACRO}.lef, {MACRO}.spice  ({um(W)} x {um(H)} um, "
      f"{W // SITE_W} sites x {H // ROW_H} rows, {len(DEVICES)} transistor fingers)")
