"""Shared plumbing for analog/verify/*.py: deck pieces, parallel ngspice runner, log parsing, CSV and Markdown output.

    corner(c, temp)    .lib/.option lines for a process corner and temperature
    mc(kind, seed)     the PDK's mos_tt_stat (global) or mos_tt_mismatch (per device) section plus a seed
    blocks()           .include of out/blocks/blocks.spice (netlist_blocks.py): csro_dac, csro_stage, csro_nand, csro_inv
    dut(mismatch)      .include of spice/tt_analog_ring.spice (the LVS reference); mismatch=True adds mm_ok=1 per finger
    code_bits(vdd)     eight B-sources deriving code[k] from V(sw), so one `.dc Vsw 0 255 1` covers all 256 codes
    run_decks(...)     parallel ngspice; VERIFY_REUSE=1 re-reads finished runs whose deck text is unchanged
    meas(log, name)    `name = value` from a log; None if absent or failed
    table(...)         Markdown table

PVT is the 5 corner x 3 temperature x 3 supply box; SIGNOFF the three LibreLane STA corners.
Each run gets its own .spiceinit with num_threads=1 plus the PDK osdi lines: the container's
spinit uses 8 threads per process, and a local .spiceinit replaces it entirely.
"""
import csv
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "out", "verify")
DOCS = os.path.join(os.path.dirname(ROOT), "docs")
# per-run .spiceinit: one thread per deck (parallelism is across decks), plus the PDK lines the replaced spinit carried
SPICEINIT = """set num_threads=1
set ngbehavior=hsa
set ng_nomodcheck
set enable_noisy_r
osdi /foss/pdks/ihp-sg13g2/libs.tech/ngspice/osdi/psp103.osdi
osdi /foss/pdks/ihp-sg13g2/libs.tech/ngspice/osdi/psp103_nqs.osdi
osdi /foss/pdks/ihp-sg13g2/libs.tech/ngspice/osdi/r3_cmc.osdi
"""
MODELS = os.path.join(os.environ.get("PDK_ROOT", "/foss/pdks"),
                      os.environ.get("PDK", "ihp-sg13g2"),
                      "libs.tech/ngspice/models/cornerMOSlv.lib")
DUT_NETLIST = os.path.join(ROOT, "spice", "tt_analog_ring.spice")
BLOCKS_NETLIST = os.path.join(ROOT, "out", "blocks", "blocks.spice")

VDD_NOM = 1.2
CORNERS = ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"]
TEMPS = [-40, 27, 125]
VDDS = [1.08, 1.2, 1.32]
# PVT: the 5 x 3 x 3 box; SIGNOFF: the three LibreLane STA corners
PVT = [(c, t, v) for c in CORNERS for t in TEMPS for v in VDDS]
SIGNOFF = [("mos_tt", 27, 1.2), ("mos_ss", 125, 1.08), ("mos_ff", -40, 1.32)]

# f(code) at typical 27 C 1.2 V (make sim); sizes transients so every code gets equal periods and points per period
F_NOM = {0: 3.8e6, 1: 5.8e6, 2: 7.8e6, 3: 9.8e6, 4: 11.9e6, 6: 15.9e6, 8: 20.2e6,
         12: 28.5e6, 16: 36.9e6, 24: 53.5e6, 32: 68.5e6, 48: 96.5e6, 63: 124e6,
         64: 126e6, 96: 172e6, 127: 215e6, 128: 216e6, 160: 253e6, 191: 288e6,
         192: 290e6, 224: 315e6, 255: 332e6}


def f_nom(code):
    """interpolate F_NOM for any code"""
    ks = sorted(F_NOM)
    if code in F_NOM:
        return F_NOM[code]
    lo = max(k for k in ks if k < code)
    hi = min(k for k in ks if k > code)
    return F_NOM[lo] + (F_NOM[hi] - F_NOM[lo]) * (code - lo) / (hi - lo)


def pvt_name(c, t, v):
    return f"{c[4:]}_{t:+d}C_{v:.2f}V".replace("+", "")


# --------------------------------------------------------------- deck pieces
def corner(c="mos_tt", temp=27):
    return f".lib {MODELS} {c}\n.option temp={temp}\n"


def mc(kind, seed, temp=27):
    """'stat': global process variation; 'mismatch': per-device variation (needs mm_ok=1 on the instances). seed makes the sample reproducible."""
    section = {"stat": "mos_tt_stat", "mismatch": "mos_tt_mismatch"}[kind]
    return f".lib {MODELS} {section}\n.option temp={temp}\n.option seed={seed}\n"


def blocks():
    if not os.path.exists(BLOCKS_NETLIST):
        sys.exit(f"{BLOCKS_NETLIST} missing: run `make verify-blocks` first")
    return f".include {BLOCKS_NETLIST}\n"


def dut(mismatch=False):
    """.include of the macro's netlist; mismatch=True uses a copy next to the decks with mm_ok=1 on every finger (the LVS reference is not edited)."""
    if not mismatch:
        return f".include {DUT_NETLIST}\n"
    path = os.path.join(OUT, os.path.basename(DUT_NETLIST).replace(".spice", ".mm.spice"))
    if not os.path.exists(path) or os.path.getmtime(path) < os.path.getmtime(DUT_NETLIST):
        os.makedirs(OUT, exist_ok=True)
        with open(DUT_NETLIST) as fh, open(path, "w") as out:
            for line in fh:
                if line.startswith("X") and "sg13_lv_" in line:
                    line = line.rstrip("\n") + " mm_ok=1\n"
                out.write(line)
    return f".include {path}\n"


def code_bits(vdd, node="sw"):
    """Eight B-sources: code[k] = vdd * bit k of V(sw), bit k = floor(c/2^k) - 2 floor(c/2^(k+1)); `.dc Vsw 0 255 1` then runs all 256 codes in one analysis."""
    lines = [f"Vsw {node} 0 dc 0"]
    for k in range(8):
        lines.append(f"Bc{k} code[{k}] 0 V = {vdd}*(floor(V({node})/{2**k}) - 2*floor(V({node})/{2**(k+1)}))")
    return "\n".join(lines) + "\n"


def code_dc(vdd, code):
    """the eight code bits as DC sources for one fixed code"""
    return "\n".join(f"Vc{k} code[{k}] 0 {vdd if (code >> k) & 1 else 0}" for k in range(8)) + "\n"


CODE_PORTS = " ".join(f"code[{k}]" for k in range(8))


# ------------------------------------------------------------------- running
def run_decks(decks, jobs=None, tag=""):
    """decks {name: text} -> {name: (log, rundir)}; each runs in its own out/verify/<tag>/<name>/."""
    jobs = jobs or max(1, (os.cpu_count() or 4) - 2)
    base = os.path.join(OUT, tag) if tag else OUT
    os.makedirs(base, exist_ok=True)

    def one(item):
        name, text = item
        d = os.path.join(base, name)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "deck.spice")
        logpath = os.path.join(d, "ngspice.log")
        # VERIFY_REUSE=1: reuse a finished run whose deck text is byte-identical
        if os.environ.get("VERIFY_REUSE") and os.path.exists(logpath) and \
                os.path.exists(path) and open(path).read() == text:
            return name, (open(logpath).read(), d)
        with open(path, "w") as fh:
            fh.write(text)
        # a .spiceinit in the cwd replaces the container's spinit (8 threads); see SPICEINIT
        with open(os.path.join(d, ".spiceinit"), "w") as fh:
            fh.write(SPICEINIT)
        p = subprocess.run(["ngspice", "-b", "deck.spice"], capture_output=True, text=True, cwd=d)
        log = p.stdout + p.stderr
        with open(logpath, "w") as fh:
            fh.write(log)
        return name, (log, d)

    with ThreadPoolExecutor(jobs) as ex:
        return dict(ex.map(one, decks.items()))


def meas(log, name):
    """value of a `meas` result or an `echo name=$&x` line; None if absent or failed"""
    r = re.search(rf"(?:^|\s){re.escape(name)}\s*=\s*([-+\d.eE]+)", log, re.M)
    if not r:
        return None
    try:
        return float(r.group(1))
    except ValueError:
        return None


def read_wrdata(path):
    """rows of floats from an ngspice `wrdata` file (x y1 x y2 ... per row)"""
    rows = []
    with open(path) as fh:
        for line in fh:
            parts = line.split()
            if parts:
                rows.append([float(p) for p in parts])
    return rows


# ------------------------------------------------------------------- output
def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def table(header, rows, fmt=None):
    """Markdown table. fmt: per-column format strings (None = str)."""
    fmt = fmt or [None] * len(header)

    def cell(v, f):
        if v is None:
            return "n/a"
        return (f % v) if f else str(v)
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        out.append("| " + " | ".join(cell(v, f) for v, f in zip(r, fmt)) + " |")
    return "\n".join(out) + "\n"


def write_md(name, text):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".md")
    with open(path, "w") as fh:
        fh.write(text)
    print(text)
    return path


def stats(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None, None, None, None
    n = len(xs)
    mu = sum(xs) / n
    sd = (sum((x - mu) ** 2 for x in xs) / max(1, n - 1)) ** 0.5
    return mu, sd, min(xs), max(xs)
