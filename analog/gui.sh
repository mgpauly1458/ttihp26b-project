#!/usr/bin/env bash
# Launch a GUI tool from the IIC-OSIC-TOOLS container on the host's X display.
#
#   ./gui.sh xschem xschem/inverter.sch
#   ./gui.sh klayout /work/gds/tt_um_mgpauly1458_inverter.gds
#   ./gui.sh GDS3D -p tech/sg13g2_gds3d.txt -i /work/gds/...
#
# Everything the container needs to reach the display is passed in below. When
# that does not work the failure is spectacularly unhelpful -- Qt aborts with
# "could not load the Qt platform plugin xcb" and then segfaults -- so the
# display is checked first and the likely cause reported. Set GUI_SKIP_CHECK=1
# to bypass it.
set -euo pipefail
IMAGE=${IMAGE:-hpretl/iic-osic-tools:latest}
XSOCK=/tmp/.X11-unix

# Hardware OpenGL if the render nodes are there. Without /dev/dri, Mesa cannot
# load the platform driver and silently falls back to llvmpipe -- software
# rendering, which still works but makes GDS3D and KLayout's 2.5D view crawl.
GPU=()
[ -d /dev/dri ] && GPU=(--device /dev/dri)

# -t only when there is actually a terminal, so this stays usable from scripts
# and from anything driving make non-interactively.
TTYFLAG=()
[ -t 0 ] && TTYFLAG=(-t)

preflight() {
    [ -n "${DISPLAY:-}" ] || {
        echo "gui.sh: DISPLAY is not set -- no X server to draw on." >&2
        echo "  Headless? 'make glb' builds a 3D model that needs no display." >&2
        return 1
    }
    # The real question is not whether the host can see the socket, but whether
    # a container can. Ask one.
    if docker run --rm -v "$XSOCK:$XSOCK" \
            -v "${XAUTHORITY:-$HOME/.Xauthority}:/headless/.Xauthority:ro" \
            -e DISPLAY="$DISPLAY" -e XAUTHORITY=/headless/.Xauthority \
            --user "$(id -u):$(id -g)" "$IMAGE" --skip \
            bash -lc 'xdpyinfo >/dev/null 2>&1' >/dev/null 2>&1; then
        return 0
    fi

    echo "gui.sh: the container cannot open DISPLAY=$DISPLAY." >&2
    echo >&2
    if [ ! -e "$XSOCK/X${DISPLAY##*:}" ]; then
        echo "  The X socket $XSOCK/X${DISPLAY##*:} does not exist on this host." >&2
    elif docker run --rm -v "$XSOCK:/s" "$IMAGE" --skip \
            bash -lc '[ -z "$(ls -A /s)" ]' >/dev/null 2>&1; then
        # The socket is there for us but the mount arrives empty, which means
        # the daemon resolved a different /tmp than the shell did.
        echo "  $XSOCK exists here but arrives EMPTY inside the container, so" >&2
        echo "  the Docker daemon is resolving a different /tmp than this shell." >&2
        echo "  That is what snap-packaged Docker does: snap confinement hides" >&2
        echo "  /tmp from the daemon, and only paths under \$HOME get through." >&2
        echo >&2
        echo "  Check with:  snap list docker; systemctl is-active snap.docker.dockerd" >&2
        echo "  If both a snap and an apt docker-ce daemon are installed, the snap" >&2
        echo "  one wins the socket. Hand it back to docker-ce with:" >&2
        echo >&2
        echo "      sudo snap stop --disable docker" >&2
        echo "      sudo systemctl restart docker" >&2
    else
        echo "  The socket is visible but the connection was refused, which is" >&2
        echo "  usually X access control. Allow local clients once with:" >&2
        echo >&2
        echo "      xhost +local:" >&2
    fi
    echo >&2
    echo "  Meanwhile 'make glb' produces a 3D model with no display at all." >&2
    return 1
}

[ "${GUI_SKIP_CHECK:-0}" = "1" ] || preflight

exec docker run --rm -i "${TTYFLAG[@]}" "${GPU[@]}" \
    -v "$(git rev-parse --show-toplevel):/work" -w /work/analog \
    -v "$XSOCK:$XSOCK" \
    -v "${XAUTHORITY:-$HOME/.Xauthority}:/headless/.Xauthority:ro" \
    -e DISPLAY="$DISPLAY" \
    -e XAUTHORITY=/headless/.Xauthority \
    --user "$(id -u):$(id -g)" \
    -e PDK=ihp-sg13g2 \
    "$IMAGE" --skip "$@"
