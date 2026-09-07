#!/usr/bin/env bash
# Run a command inside the IIC-OSIC-TOOLS container with the repository root
# mounted at /work. The tile hardening flow runs from the root, exactly as
# tt-gds-action does in CI.
#
#   flow/run.sh python -m librelane --help
#
# --skip must be the first argument to the image's entrypoint or it starts a UI.
set -euo pipefail
IMAGE=${IMAGE:-hpretl/iic-osic-tools:latest}
ROOT=$(git rev-parse --show-toplevel)
# The image's login shell sources $HOME/.bashrc; give it a HOME that exists.
mkdir -p "$ROOT/analog/out/.home" "$ROOT/analog/out/.cache" && touch "$ROOT/analog/out/.home/.bashrc"
exec docker run --rm \
    -v "$ROOT:/work" -w /work \
    --user "$(id -u):$(id -g)" \
    -e PDK=ihp-sg13g2 \
    -e PDK_ROOT=/foss/pdks \
    -e XDG_CACHE_HOME=/work/analog/out/.cache \
    -e HOME=/work/analog/out/.home \
    "$IMAGE" --skip "$@"
