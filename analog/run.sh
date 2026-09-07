#!/usr/bin/env bash
# Run a command inside the IIC-OSIC-TOOLS container with this directory mounted
# at /work. The container already defaults to PDK=ihp-sg13g2.
#
#   ./run.sh klayout -v
#   ./run.sh bash -lc 'ngspice -b sim/tb.spice'
#
# ngspice is single-threaded by default (OMP_NUM_THREADS=1): these decks are
# small, and a parallel sweep of them would otherwise oversubscribe the machine
# eightfold. Override with OMP_NUM_THREADS=n in the environment.
# --skip must be the first argument to the image's entrypoint or it starts a UI.
set -euo pipefail
IMAGE=${IMAGE:-hpretl/iic-osic-tools:latest}
exec docker run --rm \
    -v "$(git rev-parse --show-toplevel):/work" -w /work/analog \
    --user "$(id -u):$(id -g)" \
    -e PDK=ihp-sg13g2 \
    -e XDG_CACHE_HOME=/work/analog/out/.cache \
    -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" \
    "$IMAGE" --skip "$@"
