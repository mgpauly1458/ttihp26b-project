/*
 * The digital half of the mixed-signal hello world.
 *
 * It drives the analog inverter's gate, samples the inverter's output back
 * into the digital domain, and computes the same inversion in logic so the two
 * can be compared on the pins. The flop is not decoration: it forces CTS and
 * STA to run instead of the whole design collapsing into a wire.
 *
 * y_analog arrives from a CMOS drain node. That is a full-swing rail-to-rail
 * signal driving standard-cell gate inputs, which is exactly what an ordinary
 * cell output looks like - no level shifting or comparator is needed.
 */

`default_nettype none

module ms_hello (
    input  wire clk,
    input  wire rst_n,
    input  wire a,          // stimulus, from ui_in[0]
    input  wire y_analog,   // the hand-drawn inverter's output

    output wire y_comb,     // y_analog, combinationally
    output wire y_reg,      // y_analog, registered on clk
    output wire y_ref,      // ~a computed in standard cells
    output wire mismatch    // high when the analog and digital answers differ
);

  assign y_comb   = y_analog;
  assign y_ref    = ~a;
  assign mismatch = y_analog ^ y_ref;

  reg y_reg_q;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) y_reg_q <= 1'b0;
    else        y_reg_q <= y_analog;
  end
  assign y_reg = y_reg_q;

endmodule

`default_nettype wire
