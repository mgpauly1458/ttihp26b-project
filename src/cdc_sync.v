// ============================================================================
// cdc_sync.v -- two-flop synchroniser for a single bit crossing clock domains
// ----------------------------------------------------------------------------
// What it does
//   Takes a one-bit signal produced in some other clock domain and delivers a
//   version of it that is safe to use in THIS clock domain. One module,
//   instantiated wherever a bit crosses between the reference domain and the
//   ring domain.
//
// Clock domain
//   The destination's. `clk` is the clock of whoever is going to USE `q`.
//   `d` comes from anywhere.
//
// Interface
//   clk     destination clock
//   reset   synchronous, active high. Tie to 0 in a domain that has no reset
//           (the ring domain: no clock while the ring is off, so nothing to
//           reset with). The flops then start unknown and become valid after
//           two clock edges, which every user of this module allows for.
//   d       the bit from the other domain
//   q       the same bit, two clocks later, safe to use
//
// Why two flops -- the plain-English version
//   A flip-flop needs its D input to be steady for a short window around the
//   clock edge (setup before, hold after). A signal from another clock domain
//   has no relationship to our clock, so sooner or later it WILL change inside
//   that window. When that happens the flop does not cleanly pick old or new;
//   its output can hover between 0 and 1 for a while and then fall to one side
//   at random. That is metastability. The hovering usually ends within a
//   fraction of a clock period, but there is no hard bound -- only a
//   probability that falls off exponentially with the time allowed.
//
//   If the hovering output fed logic directly, different gates could read it
//   as different values, and the design would do something that no state of
//   the RTL describes. Instead, the first flop (s1) absorbs the hit: its only
//   job is to go metastable and be given a whole clock period to settle.
//   The second flop (s2) samples s1 one period later, by which time s1 has
//   settled with overwhelming probability, so s2 is clean. The cost is two
//   cycles of latency and a one-cycle uncertainty about exactly when the
//   change is seen. Nothing after s2 ever sees a half-way value.
//
//   Why this matters more than usual here: a metastability failure would not
//   crash anything, it would produce an occasional wrong count. Occasional
//   wrong counts look exactly like the measurement noise this instrument
//   exists to characterise. It would corrupt the result silently.
//
// What this module does NOT do
//   * Multi-bit values. Two bits through two of these can arrive in different
//     cycles. Multi-bit values in this design are either static during the
//     crossing (target_n) or are never read across the boundary at all
//     (the counters). measure_core.v explains the freeze-then-read ordering.
//   * Short pulses. A pulse shorter than one destination clock period can
//     fall entirely between two destination edges and be missed. Every
//     crossing in this design is a LEVEL that is held until acknowledged.
//
// Synthesis constraints this will eventually need (not applied yet)
//   * set_false_path -from <source domain> -to s1_reg, or equivalently
//     set_clock_groups -asynchronous between the reference and ring clocks,
//     so STA does not try to close timing on a crossing that by definition
//     has none.
//   * Ideally a max-delay constraint s1 -> s2 of one period with no other
//     logic between them, and a don't-touch on the pair so the optimiser
//     does not merge or move them. Some flows mark the pair with an
//     ASYNC_REG-style attribute; we note the intent here in the meantime.
// ============================================================================
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
