# Quick Reference

Terse. See [`CLAUDE.md`](CLAUDE.md) for the why behind any of this.

## Prereqs

- Docker running, and your user in the `docker` group (or `sudo`).
- `analog/` work needs no other host tooling — runs in `hpretl/iic-osic-tools`.
- `make harden`/`test`/`test-gl` need a host `venv`: `make tools` (root Makefile) sets it up + clones `tt/`.
- `PDK_ROOT` env var for `make harden`/`test-gl` — defaults to `~/pdk`.
- GUI targets (`xschem`, `klayout`, `d25`, `view3d`) need `DISPLAY` set and a working X socket. See [Troubleshooting → X11 / display](#x11--display).
- `gh` CLI authenticated, for `make ci`.

## Root-level make commands

Run from repo root. Full pipeline for the **tile**.

| command | does | runs in |
|---|---|---|
| `make macro` | builds+checks analog macro (`= make -C analog macro`) | Docker |
| `make harden` | LibreLane hardens the tile | host venv + LibreLane's own container |
| `make precheck` | Tiny Tapeout precheck on hardened GDS | Docker |
| `make test` | cocotb vs RTL | host venv |
| `make test-gl` | cocotb vs gate-level netlist | host venv |
| `make submission` | stage `tt_submission/` as CI would | host venv |
| `make all` | macro → harden → precheck → test | — |
| `make view` | glTF 3D export of hardened tile, no display | Docker |
| `make tools` | clone `tt/`, install venv deps | host |
| `make clean` | rm `runs/ tt_submission/` + generated configs | host |
| `make distclean` | clean + rm `tt/` + analog `distclean` | host |

Block-level analog work: `make -C analog help`. See [Analog `make` commands](#analog-make-commands).

## Analog make commands

Run from `analog/`. Every target takes `CELL=<name>` (default: `tt_analog_inverter`, the macro). `make list` shows available cells/scripts.

| command | does |
|---|---|
| `make netlist-lvs` | xschem → `out/<cell>.spice` (device lines, for LVS) |
| `make netlist-sim` | xschem → `out/<tb>.sim.spice` (subckt calls, for ngspice) |
| `make netlist` | both |
| `make sim` | ngspice on testbench — see [Simulating](#simulating) |
| `make plot` | waveforms → `docs/` — see [Plots](#plots) |
| `make gds` | `layout/build_<cell>.py` → GDS |
| `make lef` | LEF (macro only; generated alongside GDS, not separately) |
| `make lib` | ngspice characterization → Liberty (macro only) |
| `make png` | render layout to PNG |
| `make drc` | KLayout DRC — see [DRC](#drc) |
| `make lvs` | KLayout LVS — see [LVS](#lvs) |
| `make design` | netlist + sim + gds + drc + lvs (block correctness) |
| `make macro` | gds + lib + drc + lvs (ready for LibreLane) |
| `make all` | design + macro |
| `make glb` | 3D `.glb`, no display |
| `make d25` | KLayout 2.5D view (display) |
| `make view3d` | GDS3D view (display) |
| `make gds3d-tech` | regen GDS3D process file from PDK |
| `make xschem` | open xschem GUI — see [Opening files in xschem](#opening-files-in-xschem) |
| `make klayout` | open KLayout GUI on `$(GDS)` |
| `make shell` | interactive shell in the container |
| `make ci` | last 5 CI runs for current branch (needs `gh`) |
| `make clean` / `distclean` | rm `out/` / + committed gds/lef |

Force a rerun of any target: `make -B <target>`.

## Simulating

```bash
cd analog
make sim TB=inverter        # runs ngspice on xschem/inverter_tb.sch
```
- `TB` defaults to `<CELL>_tb`; **the default `CELL` (`tt_analog_inverter`) has no testbench** — always pass `TB=inverter` (or your block's tb name) explicitly.
- Analysis (`.control` block, what's written/plotted) lives **in the testbench schematic**, not the Makefile.
- Output: `out/<tb>_*.data`, `.raw` files.
- From the GUI instead: open the tb (see [Opening files in xschem](#opening-files-in-xschem)), then netlist+simulate hotkey inside xschem.
- Prereq: `make netlist-sim` runs automatically as a dependency.

## Plots

```bash
cd analog
make plot TB=inverter
```
- Runs [Simulating](#simulating) first, then `sim/plot.py` (matplotlib, `Agg` backend — **no window**).
- Output file: `analog/docs/inverter_sim.png` (script path is `../docs/...`, cwd is `analog/`).
- View it with any image viewer, or ask Claude to read/display it.
- `PLOT` var overrides the script (default `sim/plot.py`) — only wired up for the inverter today.

## DRC

```bash
cd analog
make drc CELL=<name>        # default CELL = tt_analog_inverter
```
- Runs KLayout's DRC deck from the PDK against `$(GDS)`.
- `--no_density --no_offgrid` always passed — density is **not checked at block level** (see [Notes](#notes)).
- Pass/fail marker: `out/<cell>/.drc-passed`; full run dir `out/<cell>/drc/`.
- Needs `make gds` first (auto-dependency).
- Tile-level signoff DRC (the one that counts for submission) happens inside `make harden` / LibreLane, not here.

## LVS

```bash
cd analog
make lvs CELL=<name>
```
- Compares `$(GDS)` against `$(NETLIST)` (`out/<cell>.spice`, device-line form).
- `--disable_tap_extraction` always passed (else well/substrate ties extract as resistors and bulks land on unnamed nets).
- Needs both `make gds` and `make netlist-lvs` (auto-dependencies).
- Pass/fail marker: `out/<cell>/.lvs-passed`; run dir `out/<cell>/lvs/`.
- **The macro is not checked in the tile's LVS** — tile-level LVS treats it as an empty placeholder (0 devices). This LVS is the only thing that actually verifies the inverter's internals. See [`CLAUDE.md`](CLAUDE.md) "Not done yet".

## Running the TT pipeline / checks

From repo root:

```bash
make macro      # analog/: gds, lib, drc, lvs -- see analog Makefile sections above
make harden     # LibreLane hardens the tile
make precheck   # Tiny Tapeout precheck
make test       # cocotb, RTL
# or just:
make all
```
- `make harden` generates `src/user_config.json` from `info.yaml`, merges over `src/config.json`, invokes LibreLane via `tt/tt_tool.py --harden --ihp`.
- **Must** use the venv's LibreLane (`pip install librelane==3.0.5`, via `make tools`) — the container's own LibreLane is a broken dev build. See [Troubleshooting](#librelane-version).
- `make precheck` needs `make submission` first (auto-dependency) — stages `tt_submission/<top>.gds`.
- `make test-gl` needs `make harden` first (auto-dependency) and Tiny Tapeout's iverilog 13 — see `test/README.md`.
- Push to GitHub → Actions runs the same steps. You never upload a GDS yourself; submit the repo URL at app.tinytapeout.com before the deadline.
- Check CI status: `make -C analog ci` (root Makefile has no `ci` target).

## Opening files in xschem

```bash
cd analog
make xschem TB=<name>          # opens xschem/<name>.sch
```
- **No default testbench exists for `tt_analog_inverter`** — bare `make xschem` opens a nonexistent file and xschem silently shows a blank untitled schematic. Always pass `TB=`.
- Files live in `analog/xschem/*.sch` / `*.sym` (container path: `/work/analog/xschem/`).
- Open another file from inside a running xschem: **File → Open** (or `Ctrl+O`), browse to `/work/analog/xschem/`.
- Jump into a symbol instance's definition: select it, press **E** (or double-click). Back out: **Ctrl+E**.
- Missing-symbol errors: see [Troubleshooting](#missing-symbol-in-xschem).

## Notes

- `analog/macro/*.gds`, `*.lef`, `analog/lib/*.lib` are **committed** — CI has no KLayout/PDK/ngspice, so LibreLane must find them in-repo. Rebuild with `make macro`, commit the result.
- Don't hand-edit `analog/macro/*.lef` — generated from the same constants as the GDS.
- Density/fill is **not** checked at block level (`--no_density` always passed to `make drc`); only the tile-level signoff run (inside `make harden`) checks it.
- Three branches hold three project variants (`main`, `digital-top`, `analog-inverter`) — merging to `main` is what commits to one. See [`CLAUDE.md`](CLAUDE.md).

## Troubleshooting

### Missing symbol in xschem
Symbol resolution depends on `XSCHEM_LIBRARY_PATH` in `analog/xschem/xschemrc`. It must point at `/work/analog/xschem` (container path) — if it says something else (e.g. `/work/xschem`), fix it there. Reopen the schematic after editing; xschem doesn't always reread `xschemrc` on a soft reload.

### X11 / display
GUI targets (`xschem`, `klayout`, `d25`, `view3d`) run `analog/gui.sh`, which preflights the display and prints a specific diagnosis. Common cause: snap-packaged Docker can't see `/tmp`, so `/tmp/.X11-unix` mounts empty in the container. Fix:
```bash
sudo snap stop --disable docker
sudo systemctl restart docker.socket docker.service
```
No display available at all → use `make glb` (3D export, no display needed) instead of `d25`/`view3d`.

### LibreLane version
Don't harden with the container's bundled LibreLane (dev build, broken OpenSTA). `make tools` installs `librelane==3.0.5` into the host venv; `make harden` always uses that.

### `make sim` says "No testbench"
You didn't pass `TB=`, or it doesn't exist. Run `make list` to see available schematics, then `make sim TB=<name>`.

### `//` comment key breaks LibreLane config
`"//"` keys are only stripped at the top level of `src/config.json`. One inside `MACROS` throws `unrecognized for dataclass Macro: //`. Don't nest comment keys.
