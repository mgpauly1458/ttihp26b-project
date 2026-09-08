#!/usr/bin/env python3
"""Write the xschem sheets (and a symbol for each instantiated one) of the ring oscillator macro.

    python3 xschem/make_sch.py          (or: make sch)   ->  xschem/*.sch, *.sym

    csro_stage      starved inverter, 4 transistors
    csro_nand       starved NAND closing the loop, 6 transistors
    csro_dac        8-bit binary array + always-on units
    csro_inv        plain inverter (the buffer uses two)
    tt_analog_ring  top: DAC, bias mirror, NAND, ten stages, buffer

- Scripted so the ten stages and eight DAC legs land on the grid; the outputs are ordinary xschem files (`make xschem`).
- Device sizes are the constants of layout/build_tt_analog_ring.py; `make lvs-sch` proves the drawing matches the layout.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "layout"))

# sizes (um), identical to build_tt_analog_ring.py
WU, LU = 0.15, 8.0
WPS, LPS = 1.0, 0.5
WNS, LNS = 0.5, 0.5
WPI, WNI, LI = 0.5, 0.3, 0.13
NG_MP0, WP0F = 24, 2.0
NG_ON = 2
WNAND = 0.6
WBP2, WBN2 = 2.0, 1.0

HEAD = "v {xschem version=3.4.8RC file_version=1.3}\nG {}\nK {}\nV {}\nS {}\nF {}\nE {}\n"
DEV = "sg13g2_pr/sg13_lv_{kind}.sym"


class Sheet:
    def __init__(self, title):
        self.lines = [HEAD]
        self.title = title
        self.n = 0

    def wire(self, x1, y1, x2, y2, lab=None):
        self.lines.append(f"N {x1} {y1} {x2} {y2} {{{'lab=' + lab if lab else ''}}}\n")

    def path(self, pts, lab=None):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            self.wire(x1, y1, x2, y2, lab)

    def lab(self, name, x, y, rot=0, flip=0):
        self.n += 1
        self.lines.append(f"C {{devices/lab_pin.sym}} {x} {y} {rot} {flip} {{name=l{self.n} sig_type=std_logic lab={name}}}\n")

    def pin(self, kind, name, x, y):
        """kind: ipin | opin | iopin. Placed in call order = subckt pin order."""
        self.n += 1
        self.lines.append(f"C {{devices/{kind}.sym}} {x} {y} 0 0 {{name=p{self.n} lab={name}}}\n")

    def mos(self, kind, name, x, y, w, l, ng=1, flip=0):
        """Transistor: gate at (x-20, y), channel pins at (x+20, y-30) and (x+20, y+30) (NMOS drain on top, PMOS source on top).
        w is the TOTAL width (PDK convention, ng fingers of w/ng). flip=1 puts the gate on the right. Returns (gate, top, bottom)."""
        self.lines.append(
            f"C {{{DEV.format(kind=kind)}}} {x} {y} 0 {flip} {{name={name}\nl={l:g}u\nw={w:g}u\nng={ng}\nm=1\n"
            f"model=sg13_lv_{kind}\nspiceprefix=X\n}}\n")
        # bulk: a short wire from the B pin out past the parameter text, then a label
        bx = x - 20 if flip else x + 20
        lx = bx - 60 if flip else bx + 60
        self.wire(bx, y, lx, y)
        self.lab("VPWR" if kind == "pmos" else "VGND", lx, y, rot=0, flip=0 if flip else 0)
        return (x - 20 if not flip else x + 20, y), (bx, y - 30), (bx, y + 30)

    def sub(self, sym, name, x, y):
        self.lines.append(f"C {{{sym}.sym}} {x} {y} 0 0 {{name={name}}}\n")

    def text(self, s, x, y, size=0.4):
        self.lines.append(f"T {{{s}}} {x} {y} 0 0 {size} {size} {{}}\n")

    def write(self, name):
        with open(os.path.join(HERE, name + ".sch"), "w") as fh:
            fh.write("".join(self.lines))
            fh.write(f"C {{devices/title.sym}} -300 400 0 0 {{name=t1 author=\"Maxwell Pauly\"}}\n")


def symbol(name, pins, w=120, h=None, title=None):
    """Box symbol. pins: (name, dir, side l|r|t|b, offset in grid units from the centre); their order is the subckt pin order,
    so the sheet must place its ipin/opin symbols in the same order. Returns ({pin: (side, offset)}, half width, half height)."""
    h = h or 20 * (max(sum(1 for p in pins if p[2] == s) for s in "lr") + 1)
    hw, hh = w // 2, h // 2
    out = ["v {xschem version=3.4.8RC file_version=1.3}\n",
           "K {type=subcircuit\nformat=\"@name @pinlist @symname\"\ntemplate=\"name=x1\"\n}\n",
           "G {}\nV {}\nS {}\nE {}\n",
           f"P 4 5 {-hw} {-hh} {hw} {-hh} {hw} {hh} {-hw} {hh} {-hw} {-hh} {{}}\n",
           f"T {{{title or name}}} {-hw + 5} {-hh + 25} 0 0 0.25 0.25 {{}}\n",
           f"T {{@name}} {-hw + 5} {hh - 15} 0 0 0.25 0.25 {{}}\n"]
    for pname, d, side, off in pins:
        if side == "l":
            x, y = -hw, off * 20
            out.append(f"L 4 {x} {y} {x + 20} {y} {{}}\n")
            out.append(f"T {{{pname}}} {x + 25} {y - 5} 0 0 0.2 0.2 {{}}\n")
        elif side == "r":
            x, y = hw, off * 20
            out.append(f"L 4 {x - 20} {y} {x} {y} {{}}\n")
            out.append(f"T {{{pname}}} {x - 25} {y - 5} 0 1 0.2 0.2 {{}}\n")
        elif side == "t":
            x, y = off * 20, -hh
            out.append(f"L 4 {x} {y} {x} {y + 20} {{}}\n")
            out.append(f"T {{{pname}}} {x + 5} {y + 5} 0 0 0.2 0.2 {{}}\n")
        else:
            x, y = off * 20, hh
            out.append(f"L 4 {x} {y - 20} {x} {y} {{}}\n")
            out.append(f"T {{{pname}}} {x + 5} {y - 15} 0 0 0.2 0.2 {{}}\n")
        out.append(f"B 5 {x - 2.5} {y - 2.5} {x + 2.5} {y + 2.5} {{name={pname} dir={d}}}\n")
    with open(os.path.join(HERE, name + ".sym"), "w") as fh:
        fh.write("".join(out))
    return {p[0]: (p[2], p[3]) for p in pins}, hw, hh


def pin_xy(sym, pname, x, y):
    """Absolute position of a symbol pin for an instance at (x, y)."""
    pins, hw, hh = sym
    side, off = pins[pname]
    return {"l": (x - hw, y + off * 20), "r": (x + hw, y + off * 20),
            "t": (x + off * 20, y - hh), "b": (x + off * 20, y + hh)}[side]


# ------------------------------------------------------------- csro_stage
STAGE_PINS = [("in", "in", "l", 0), ("out", "out", "r", 0),
              ("vbp", "in", "t", -1), ("VPWR", "inout", "t", 1),
              ("vbn", "in", "b", -1), ("VGND", "inout", "b", 1)]
stage_sym = symbol("csro_stage", STAGE_PINS, w=140, h=120, title="starved inv")

s = Sheet("csro_stage")
s.text("current-starved inverter: the ring stage", -200, -260, 0.4)
g, S, D = s.mos("pmos", "MPS", 0, -150, WPS, LPS)      # S top (20,-180), D (20,-120)
s.wire(20, -180, 20, -200); s.lab("VPWR", 20, -200)
s.wire(-20, -150, -60, -150); s.lab("vbp", -60, -150)
g, S, D = s.mos("pmos", "MP", 0, -60, WPI, LI)         # S (20,-90), D (20,-30)
s.wire(20, -120, 20, -90)
g, D, S = s.mos("nmos", "MN", 0, 60, WNI, LI)          # D (20,30), S (20,90)
s.wire(20, -30, 20, 30); s.wire(20, 0, 80, 0); s.lab("out", 80, 0)
g, D, S = s.mos("nmos", "MNS", 0, 150, WNS, LNS)       # D (20,120), S (20,180)
s.wire(20, 90, 20, 120)
s.wire(-20, 150, -60, 150); s.lab("vbn", -60, 150)
s.wire(20, 180, 20, 200); s.lab("VGND", 20, 200)
s.path([(-20, -60), (-60, -60), (-60, 60), (-20, 60)])
s.wire(-60, 0, -100, 0); s.lab("in", -100, 0)
for k, (n, d, _, _) in enumerate(STAGE_PINS):
    s.pin({"in": "ipin", "out": "opin", "inout": "iopin"}[d], n, -300, -200 + 40 * k)
s.write("csro_stage")

# -------------------------------------------------------------- csro_nand
NAND_PINS = [("a", "in", "l", -1), ("b", "in", "l", 1), ("out", "out", "r", 0),
             ("vbp", "in", "t", -1), ("VPWR", "inout", "t", 1),
             ("vbn", "in", "b", -1), ("VGND", "inout", "b", 1)]
nand_sym = symbol("csro_nand", NAND_PINS, w=140, h=120, title="starved nand")

s = Sheet("csro_nand")
s.text("current-starved NAND: enable (a) and feedback (b) close the loop", -260, -320, 0.4)
s.mos("pmos", "MPS0", 0, -240, WPS, LPS)               # S (20,-270), D (20,-210)
s.wire(20, -270, 20, -290); s.lab("VPWR", 20, -290)
s.wire(-20, -240, -60, -240); s.lab("vbp", -60, -240)
s.mos("pmos", "MPA0", -80, -120, WPI, LI)              # S (-60,-150), D (-60,-90)
s.mos("pmos", "MPB0", 160, -120, WPI, LI)              # S (180,-150), D (180,-90)
s.path([(20, -210), (20, -170), (-60, -170), (-60, -150)])
s.path([(20, -170), (180, -170), (180, -150)])
s.path([(-60, -90), (-60, -60), (180, -60), (180, -90)])
s.wire(20, -60, 20, 30); s.wire(20, 0, 240, 0); s.lab("out", 240, 0)
s.wire(-100, -120, -140, -120); s.lab("a", -140, -120)
s.wire(140, -120, 110, -120); s.lab("b", 110, -120)
s.mos("nmos", "MNB0", 0, 60, WNAND, LI)                # D (20,30), S (20,90)
s.wire(-20, 60, -60, 60); s.lab("b", -60, 60)
s.mos("nmos", "MNA0", 0, 150, WNAND, LI)               # D (20,120), S (20,180)
s.wire(20, 90, 20, 120)
s.wire(-20, 150, -60, 150); s.lab("a", -60, 150)
s.mos("nmos", "MNS0", 0, 240, WNS, LNS)                # D (20,210), S (20,270)
s.wire(20, 180, 20, 210)
s.wire(-20, 240, -60, 240); s.lab("vbn", -60, 240)
s.wire(20, 270, 20, 290); s.lab("VGND", 20, 290)
for k, (n, d, _, _) in enumerate(NAND_PINS):
    s.pin({"in": "ipin", "out": "opin", "inout": "iopin"}[d], n, -300, -260 + 40 * k)
s.write("csro_nand")

# --------------------------------------------------------------- csro_inv
INV_PINS = [("in", "in", "l", 0), ("out", "out", "r", 0),
            ("VPWR", "inout", "t", 0), ("VGND", "inout", "b", 0)]
inv_sym = symbol("csro_inv", INV_PINS, w=120, h=100, title="inv")
s = Sheet("csro_inv")
s.text("output buffer inverter: the second one is 4x this", -200, -200, 0.4)
s.mos("pmos", "MBP", 0, -60, WPI, LI)
s.mos("nmos", "MBN", 0, 60, WNI, LI)
s.wire(20, -90, 20, -110); s.lab("VPWR", 20, -110)
s.wire(20, 90, 20, 110); s.lab("VGND", 20, 110)
s.wire(20, -30, 20, 30); s.wire(20, 0, 80, 0); s.lab("out", 80, 0)
s.path([(-20, -60), (-60, -60), (-60, 60), (-20, 60)])
s.wire(-60, 0, -100, 0); s.lab("in", -100, 0)
for k, (n, d, _, _) in enumerate(INV_PINS):
    s.pin({"in": "ipin", "out": "opin", "inout": "iopin"}[d], n, -300, -160 + 40 * k)
s.write("csro_inv")

# --------------------------------------------------------------- csro_dac
DAC_PINS = [(f"code[{k}]", "in", "l", k - 4) for k in range(8)] + \
           [("vbp", "out", "r", 0), ("VPWR", "inout", "t", 0), ("VGND", "inout", "b", 0)]
dac_sym = symbol("csro_dac", DAC_PINS, w=200, h=240, title="8-bit current DAC")
s = Sheet("csro_dac")
s.text("binary-weighted current DAC: 2^k unit fingers (0.15u/8u) per bit, gate driven by the code bit; "
       f"+{NG_ON} always-on units", -100, -200, 0.4)
X0, PITCH = 0, 220
for k in range(9):
    x = X0 + k * PITCH
    if k < 8:
        s.mos("nmos", f"D{k}", x, 0, WU * 2 ** k, LU, ng=2 ** k)
        s.wire(x - 20, 0, x - 50, 0); s.lab(f"code[{k}]", x - 50, 0)
    else:
        s.mos("nmos", "DON", x, 0, WU * NG_ON, LU, ng=NG_ON)
        s.wire(x - 20, 0, x - 50, 0); s.lab("VPWR", x - 50, 0)
    s.wire(x + 20, -30, x + 20, -80)
    s.wire(x + 20, 30, x + 20, 80)
xl, xr = X0 + 20, X0 + 8 * PITCH + 20
s.wire(xl, -80, xr + 60, -80); s.lab("vbp", xr + 60, -80)
s.wire(xl, 80, xr + 60, 80); s.lab("VGND", xr + 60, 80)
for k, (n, d, _, _) in enumerate(DAC_PINS):
    s.pin({"in": "ipin", "out": "opin", "inout": "iopin"}[d], n, -300, -160 + 40 * k)
s.write("csro_dac")

# ---------------------------------------------------------- tt_analog_ring
s = Sheet("tt_analog_ring")
s.text("tt_analog_ring: current-starved ring oscillator with an 8-bit current DAC", -560, -620, 0.5)
# top-level pins, in the order the layout's netlist uses
for k, (n, kind) in enumerate([(f"code[{k}]", "ipin") for k in range(8)] +
                              [("enable", "ipin"), ("clk_out", "opin"), ("VPWR", "iopin"), ("VGND", "iopin")]):
    s.pin(kind, n, -760, -560 + 40 * k)

# DAC
dx, dy = -400, -300
s.sub("csro_dac", "XDAC", dx, dy)
for k in range(8):
    x, y = pin_xy(dac_sym, f"code[{k}]", dx, dy)
    s.wire(x, y, x - 40, y); s.lab(f"code[{k}]", x - 40, y)
for n in ("VPWR", "VGND"):
    s.lab(n, *pin_xy(dac_sym, n, dx, dy))
x, y = pin_xy(dac_sym, "vbp", dx, dy)
s.wire(x, y, x + 60, y)
# bias: diode PMOS MPD on the DAC's output node, mirror MPM -> diode NMOS MND
bx = x + 60 + 40                                        # MPD gate at (bx-20, y)
s.mos("pmos", "MPD", bx, y, WP0F * NG_MP0, LPS, ng=NG_MP0)   # w is the TOTAL width, ng fingers
s.wire(bx + 20, y - 30, bx + 20, y - 60); s.lab("VPWR", bx + 20, y - 60)
s.path([(bx + 20, y + 30), (bx + 20, y + 60), (bx - 40, y + 60), (bx - 40, y), (bx - 20, y)])  # diode: gate = drain
s.wire(bx - 40, y + 60, bx - 40, y + 90); s.lab("vbp", bx - 40, y + 90)
s.text("vbp = I_dac into the diode; each stage's PMOS starve is 1/48 of it", bx + 60, y - 70, 0.3)
mx = bx + 240
s.mos("pmos", "MPM", mx, y, WPS, LPS)
s.wire(mx - 20, y, mx - 60, y); s.lab("vbp", mx - 60, y)
s.wire(mx + 20, y - 30, mx + 20, y - 60); s.lab("VPWR", mx + 20, y - 60)
s.mos("nmos", "MND", mx, y + 120, WNS, LNS)             # D (mx+20,y+90) S (mx+20,y+150)
s.wire(mx + 20, y + 30, mx + 20, y + 90)
s.path([(mx + 20, y + 60), (mx - 40, y + 60), (mx - 40, y + 120), (mx - 20, y + 120)])   # diode
s.wire(mx - 40, y + 60, mx - 80, y + 60); s.lab("vbn", mx - 80, y + 60)
s.wire(mx + 20, y + 150, mx + 20, y + 180); s.lab("VGND", mx + 20, y + 180)
s.text("vbn: MPM copies the stage current into the diode MND", mx + 60, y + 100, 0.3)

# the ring: NAND then ten stages, left to right
ry0 = 260
nx = -400
s.sub("csro_nand", "XNAND", nx, ry0)
ax, ay = pin_xy(nand_sym, "a", nx, ry0)
s.wire(ax, ay, ax - 60, ay); s.lab("enable", ax - 60, ay)
bxp, byp = pin_xy(nand_sym, "b", nx, ry0)
for n in ("vbp", "VPWR", "vbn", "VGND"):
    s.lab(n, *pin_xy(nand_sym, n, nx, ry0))
prev = pin_xy(nand_sym, "out", nx, ry0)
STEP = 200
for i in range(1, 11):
    sx = nx + i * STEP
    s.sub("csro_stage", f"X{i}", sx, ry0)
    ix, iy = pin_xy(stage_sym, "in", sx, ry0)
    s.wire(prev[0], prev[1], ix, iy, lab=f"s{i - 1}")
    for n in ("vbp", "VPWR", "vbn", "VGND"):
        s.lab(n, *pin_xy(stage_sym, n, sx, ry0))
    prev = pin_xy(stage_sym, "out", sx, ry0)
# feedback from the last stage back to the NAND's b input, routed below the row
fx, fy = prev
s.path([(fx, fy), (fx + 30, fy), (fx + 30, fy + 120), (bxp - 40, fy + 120), (bxp - 40, byp), (bxp, byp)], lab="s10")
s.lab("s10", fx + 30, fy + 60)
# buffer
b1x = fx + 30 + 120
s.sub("csro_inv", "XB1", b1x, ry0 - 140)
i1 = pin_xy(inv_sym, "in", b1x, ry0 - 140)
s.path([(fx + 30, fy), (fx + 30, i1[1]), i1])
o1 = pin_xy(inv_sym, "out", b1x, ry0 - 140)
# the second inverter is 4x: drawn as transistors so its size is visible
b2x = b1x + 160
s.wire(o1[0], o1[1], b2x - 60, o1[1], lab="b1")
s.path([(b2x - 60, o1[1]), (b2x - 60, o1[1] - 60), (b2x - 20, o1[1] - 60)])
s.path([(b2x - 60, o1[1]), (b2x - 60, o1[1] + 60), (b2x - 20, o1[1] + 60)])
s.mos("pmos", "MBP2", b2x, o1[1] - 60, WBP2, LI)
s.mos("nmos", "MBN2", b2x, o1[1] + 60, WBN2, LI)
s.wire(b2x + 20, o1[1] - 90, b2x + 20, o1[1] - 110); s.lab("VPWR", b2x + 20, o1[1] - 110)
s.wire(b2x + 20, o1[1] + 90, b2x + 20, o1[1] + 110); s.lab("VGND", b2x + 20, o1[1] + 110)
s.wire(b2x + 20, o1[1] - 30, b2x + 20, o1[1] + 30)
s.wire(b2x + 20, o1[1], b2x + 80, o1[1]); s.lab("clk_out", b2x + 80, o1[1])
for n in ("VPWR", "VGND"):
    s.lab(n, *pin_xy(inv_sym, n, b1x, ry0 - 140))
s.write("tt_analog_ring")
print("wrote xschem sheets in", HERE)
