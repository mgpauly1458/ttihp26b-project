# Digital half of the mixed-signal tile: RTL -> GDS with LibreLane, inside the
# IIC-OSIC-TOOLS container via ./run.sh (Docker only).
#
#   make          harden ms_hello and stage the artefacts in out/
#   make harden   run the LibreLane Classic flow
#   make stage    copy GDS / LEF / SPICE / netlist out of the run directory
#   make klayout  open the hardened macro
#   make clean    remove runs/ and out/
#
# The staged out/ms_hello.{gds,lef,spice} are what analog/layout/build_gds.py
# reads; runs/ is disposable.

DESIGN := ms_hello
RUN    := ./run.sh
GUI    := ./gui.sh
TAG    := hardened
FINAL  := runs/$(TAG)/final
PDKTECH := /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech

.PHONY: all harden stage klayout clean

all: stage

harden:
	@rm -rf runs/$(TAG)
	$(RUN) bash -lc 'cd /work/digital && librelane --pdk-root /foss/pdks --run-tag $(TAG) config.json'

# LibreLane writes several views per stage; only these four are consumed
# downstream, so they are copied out and the run directory stays disposable.
stage: harden
	@mkdir -p out
	cp $(FINAL)/gds/$(DESIGN).gds       out/$(DESIGN).gds
	cp $(FINAL)/lef/$(DESIGN).lef       out/$(DESIGN).lef
	cp $(FINAL)/spice/$(DESIGN).spice   out/$(DESIGN).spice
	cp $(FINAL)/nl/$(DESIGN).nl.v       out/$(DESIGN).nl.v
	@echo "staged out/$(DESIGN).{gds,lef,spice,nl.v}"

klayout:
	$(GUI) klayout -e -l $(PDKTECH)/sg13g2.lyp /work/digital/out/$(DESIGN).gds

clean:
	rm -rf runs out
