// tb_cdc_sync.v -- a level crossing from a 7.3 ns source clock to a 20 ns destination (edges walk every phase)
// Part 1: 500 level toggles, each held 3..6 source cycles (21.9..43.8 ns, always > one destination period).
//         Every toggle must appear exactly once, in order. Held 2 cycles (14.6 ns) lost 64 of 500:
//         a level must be held longer than one destination period.
// Part 2: 200 pulses of 2 ns; reports how many get through. This is why every crossing in the design is a held level.
// - RTL simulation cannot show metastability; this proves the protocol, not the settling.
`timescale 1ns / 1ps

module tb_cdc_sync;

  localparam real T_SRC = 7.3;
  localparam real T_DST = 20.0;

  reg  src_clk = 1'b0;
  reg  dst_clk = 1'b0;
  reg  reset   = 1'b1;
  reg  d       = 1'b0;
  wire q;

  always #(T_SRC / 2) src_clk = ~src_clk;
  always #(T_DST / 2) dst_clk = ~dst_clk;

  cdc_sync dut (.clk(dst_clk), .reset(reset), .d(d), .q(q));

  integer errors   = 0;
  integer sent     = 0;   // toggles driven
  integer received = 0;   // toggles observed at q
  reg     q_prev;

  // Count every change of q in the destination domain.
  always @(posedge dst_clk) begin
    if (!reset) begin
      if (q !== q_prev) begin
        received = received + 1;
        // d only toggles, so after toggle n q must equal n & 1.
        if (q !== received[0]) begin
          $display("FAIL: q=%b out of order at toggle %0d", q, received);
          errors = errors + 1;
        end
      end
      q_prev = q;
    end
  end

  integer n, hold;
  integer seed = 1;

  initial begin
    $dumpfile("build/tb_cdc_sync.vcd");
    $dumpvars(0, tb_cdc_sync);

    q_prev = 1'b0;
    repeat (3) @(posedge dst_clk);
    reset = 1'b0;

    $display("--- Part 1: 500 level toggles, each held 3..6 source cycles");
    for (n = 0; n < 500; n = n + 1) begin
      hold = 3 + ($random(seed) & 3);        // 3..6 source cycles, > one T_DST
      repeat (hold) @(posedge src_clk);
      d = ~d;
      sent = sent + 1;
    end
    repeat (5) @(posedge dst_clk);            // let the last one through
    $display("    sent %0d, received %0d", sent, received);
    if (sent != received) begin
      $display("FAIL: toggle count mismatch");
      errors = errors + 1;
    end

    $display("--- Part 2: 200 pulses of 2 ns, spaced 33 ns apart (walks the phase)");
    sent = 0; received = 0;
    for (n = 0; n < 200; n = n + 1) begin
      #31 d = 1'b1;
      #2  d = 1'b0;
      sent = sent + 2;                        // a pulse is two toggles
    end
    repeat (5) @(posedge dst_clk);
    $display("    pulses sent %0d, edges received %0d (a pulse that gets through gives 2)",
             sent / 2, received);
    if (received < sent)
      $display("    %0d pulses were LOST. Expected: a 2 ns pulse can fall between %0.0f ns samples.",
               (sent - received) / 2, T_DST);
    else
      $display("    All got through this time -- the phase walk happened to miss the gaps.");
    $display("    Conclusion: never cross a pulse; cross a level and hold it until acknowledged.");

    if (errors == 0) $display("RESULT: PASS");
    else             $display("RESULT: FAIL (%0d errors)", errors);
    $finish;
  end

endmodule
