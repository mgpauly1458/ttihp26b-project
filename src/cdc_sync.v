// cdc_sync.v -- two-flop synchroniser for one bit crossing into the clk domain
//   clk    destination clock (the domain that uses q)
//   reset  synchronous, active high. Tie to 0 in the ring domain (no clock to reset with); the flops then start X
//          and are valid after two edges, which every user allows for.
//   d      the bit, from any other domain
//   q      the same bit two clocks later, safe to use
// - s1 absorbs the metastability and gets a whole period to settle; s2 samples it clean. A hit here would not
//   crash anything, it would give an occasional wrong count that looks like ring noise.
// - Levels only, held until acknowledged: a pulse shorter than one clk period can fall between two edges. No multi-bit
//   value goes through two of these; in this design they are static during the crossing (target_n) or never cross.
// - src/constraints.sdc declares the domains asynchronous, so no path into s1 is timed; no don't-touch or
//   s1 -> s2 max-delay is applied.
`default_nettype none

module cdc_sync (
    input  wire clk,
    input  wire reset,
    input  wire d,
    output wire q
);

  reg s1, s2;   // s1 may go metastable; s2 is the clean copy

  always @(posedge clk) begin
    if (reset) begin
      s1 <= 1'b0;
      s2 <= 1'b0;
    end else begin
      s1 <= d;
      s2 <= s1;
    end
  end

  assign q = s2;

endmodule

`default_nettype wire
