#!/usr/bin/env bash
# Run a command in the IIC-OSIC-TOOLS container, repo mounted at /work, cwd /work/analog, PDK=ihp-sg13g2.
#
#   ./run.sh klayout -v
#   ./run.sh bash -lc 'ngspice -b sim/tb.spice'
#
# OMP_NUM_THREADS=1 (override in the environment): the decks are small and parallel sweeps would oversubscribe.
# VERIFY_REUSE is passed through: VERIFY_REUSE=1 make verify re-analyses the stored runs in out/verify.
# --skip must be the entrypoint's first argument or the image starts a UI.
set -euo pipefail
IMAGE=${IMAGE:-hpretl/iic-osic-tools:latest}
exec docker run --rm \
    -v "$(git rev-parse --show-toplevel):/work" -w /work/analog \
    --user "$(id -u):$(id -g)" \
    -e PDK=ihp-sg13g2 \
    -e XDG_CACHE_HOME=/work/analog/out/.cache \
    -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" \
    -e VERIFY_REUSE="${VERIFY_REUSE:-}" \
    "$IMAGE" --skip "$@"
