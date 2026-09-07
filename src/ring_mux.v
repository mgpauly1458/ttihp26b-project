// ============================================================================
// ring_mux.v -- selects one of eight rings, and enables only that one
// ----------------------------------------------------------------------------
// What it does
//   Routes ring number `sel` to the divider, and drives the per-ring enable
//   lines so that ONLY the selected ring runs. This is the component that
//   makes the shared-instrument argument true: every ring is measured by the
//   same divider, counter and FSM, so a difference between rings is a real
//   difference.
//
// Clock domain
//   None -- pure combinational logic on the ring clocks. It is in the ring
//   domain in the sense that its output is a clock.
//
// Interface
//   ring_in [7:0]  the eight ring outputs
//   sel     [2:0]  which one
//   enable         master enable; 0 stops every ring
//   ring_out       the selected ring
//   ring_en [7:0]  one-hot enable back to the rings (all zero if !enable)
//
// Unselected rings are disabled -- the tradeoff
//   On:   seven free-running rings at hundreds of MHz would burn power and
//         inject supply and substrate noise into the one being measured,
//         which is the opposite of what a characterisation instrument wants.
//         Off, they cost nothing.
//   Cost: a ring that was off needs time to start after enable. For a
//         standard-cell ring that is a few gate delays; for the analog ring
//         it is whatever its start-up transient is. The selected ring is
//         enabled from the moment RING_SEL is written, not from START, so by
//         the time the host has also written START (several clock periods
//         later at the very least) the ring has been running for far longer
//         than any plausible start-up. The FSM's ARM state additionally
//         begins the window on a clean edge, never mid-period. If a ring
//         turns out to need milliseconds, the host inserts a delay between
//         writing RING_SEL and START; nothing in hardware has to change.
//
// Assumptions
//   * sel changes only while idle. A combinational clock mux switching
//     between two unrelated waveforms can produce a runt pulse, exactly as
//     the divider's tap mux can. The register file refuses writes to
//     RING_SEL while busy.
// ============================================================================
`default_nettype none

module ring_mux (
    input  wire [7:0] ring_in,
    input  wire [2:0] sel,
    input  wire       enable,
    output reg        ring_out,
    output reg  [7:0] ring_en
);

  always @(*) begin
    case (sel)
      3'd0:    begin ring_out = ring_in[0]; ring_en = 8'b0000_0001; end
      3'd1:    begin ring_out = ring_in[1]; ring_en = 8'b0000_0010; end
      3'd2:    begin ring_out = ring_in[2]; ring_en = 8'b0000_0100; end
      3'd3:    begin ring_out = ring_in[3]; ring_en = 8'b0000_1000; end
      3'd4:    begin ring_out = ring_in[4]; ring_en = 8'b0001_0000; end
      3'd5:    begin ring_out = ring_in[5]; ring_en = 8'b0010_0000; end
      3'd6:    begin ring_out = ring_in[6]; ring_en = 8'b0100_0000; end
      default: begin ring_out = ring_in[7]; ring_en = 8'b1000_0000; end
    endcase
    if (!enable) ring_en = 8'b0000_0000;
  end

endmodule

`default_nettype wire
