/* Behavioural stubs for the Xilinx primitives used by the Basys3 wrapper, so
 * the wrapper can be linted and simulated with Icarus. Vivado uses the real
 * ones; this file is never read by build.tcl. */
`default_nettype none

module BUFG (input wire I, output wire O);
  assign O = I;
endmodule
