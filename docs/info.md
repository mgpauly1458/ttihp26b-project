<!---
This file is published as your project page. Keep the section headings; the
docs workflow checks for them.
-->

## How it works

Placeholder while the real design is chosen. At present this is the stock
Tiny Tapeout example: a combinational 8-bit adder that sums the dedicated
inputs with the bidirectional inputs and presents the result on the dedicated
outputs. There is no sequential state, so `clk` and `rst_n` are unused.

## How to test

Set a value on `ui_in` and another on `uio_in`; `uo_out` shows the low 8 bits
of their sum, with the carry discarded.

Locally, `cd test && make -B` runs the cocotb bench. On a Basys3 (see
`fpga/basys3/`), `sw[7:0]` and `sw[15:8]` are the two operands and `led[7:0]`
plus the 7-segment display show the sum.

## External hardware

None.
