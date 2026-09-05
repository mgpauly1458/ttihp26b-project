#!/usr/bin/env bash
# Run a command inside the IIC-OSIC-TOOLS container with this directory mounted
# at /work. The container already defaults to PDK=ihp-sg13g2.
#
#   ./run.sh klayout -v
#   ./run.sh bash -lc 'ngspice -b sim/tb.spice'
#
# --skip must be the first argument to the image's entrypoint or it starts a UI.
set -euo pipefail
IMAGE=${IMAGE:-hpretl/iic-osic-tools:latest}
exec docker run --rm \
    -v "$(git rev-parse --show-toplevel):/work" -w /work/analog \
    --user "$(id -u):$(id -g)" \
    -e PDK=ihp-sg13g2 \
    -e XDG_CACHE_HOME=/work/out/.cache \
    "$IMAGE" --skip "$@"
