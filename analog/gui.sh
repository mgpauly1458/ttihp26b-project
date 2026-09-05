#!/usr/bin/env bash
# Launch a GUI tool from the IIC-OSIC-TOOLS container on the host's X display.
#
#   ./gui.sh xschem xschem/inverter.sch
#   ./gui.sh klayout out/inverter.gds
#
# If the window fails to open with an X authorization error, allow local
# container clients once with:   xhost +local:
set -euo pipefail
IMAGE=${IMAGE:-hpretl/iic-osic-tools:latest}
exec docker run --rm -it \
    -v "$(git rev-parse --show-toplevel):/work" -w /work/analog \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v "${XAUTHORITY:-$HOME/.Xauthority}:/headless/.Xauthority:ro" \
    -e DISPLAY="$DISPLAY" \
    -e XAUTHORITY=/headless/.Xauthority \
    --user "$(id -u):$(id -g)" \
    -e PDK=ihp-sg13g2 \
    "$IMAGE" --skip "$@"
