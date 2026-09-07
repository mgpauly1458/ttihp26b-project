// ============================================================================
// tb_ring_divider.v -- all eight taps, then the tap-change runt experiment
// ----------------------------------------------------------------------------
// Part 1: a clean 10 ns clock in, every tap out. The period at tap k must be
//         exactly 10 ns * 2^k, measured over several cycles.
// Part 2: switch tap_sel while running, at eight different phases of the
//         input clock, and record the shortest high or low pulse that appears
//         on divided_clk. Reported, not judged: the question was "does a
//         runt appear", and the answer is printed.
// ============================================================================
`timescale 1ns / 1ps

module tb_ring_divider;

  localparam real T_IN = 10.0;         // input period, ns

  reg        ring_clk = 1'b0;
  reg        reset    = 1'b1;
  reg  [2:0] tap_sel  = 3'd0;
  wire       divided_clk;

  ring_divider dut (
      .ring_clk    (ring_clk),
      .reset       (reset),
      .tap_sel     (tap_sel),
      .divided_clk (divided_clk)
  );

  always #(T_IN / 2) ring_clk = ~ring_clk;

  integer errors = 0;
  integer i, k;
  real    t0, t1, period, expect;

  // ---- Part 1 -------------------------------------------------------------
  task check_tap;
    input [2:0] tap;
    begin
      tap_sel = tap;
      // A tap change is glitchy by nature; wait for it to settle before
      // measuring, and ignore whatever the first edge looks like.
      @(posedge divided_clk);
      @(posedge divided_clk); t0 = $realtime;
      for (i = 0; i < 4; i = i + 1) @(posedge divided_clk);
      t1 = $realtime;
      period = (t1 - t0) / 4;
      expect = T_IN * (1 << tap);
      $display("tap %0d : period %9.3f ns  expected %9.3f ns  (divide by %0d)",
               tap, period, expect, 1 << tap);
      // The output buffer's 80 ps delay stand-in shifts every edge by the same
      // amount, so the period is unchanged; compare with a tolerance rather
      // than exactly, since (t1 - t0) / 4 is a real.
      if (period > expect + 0.001 || period < expect - 0.001) begin
        $display("  FAIL");
        errors = errors + 1;
      end
    end
  endtask

  // ---- Part 2 -------------------------------------------------------------
  // Watch divided_clk for a while and record the shortest pulse (high or low)
  // seen. Polled at 10 ps, which is fine enough for a 10 ns input.
  real min_pulse, t_edge;
  reg  prev;
  task watch_min_pulse;
    input real duration;
    integer n;
    begin
      min_pulse = 1.0e9;
      prev = divided_clk;
      t_edge = $realtime;
      for (n = 0; n < duration / 0.01; n = n + 1) begin
        #0.01;
        if (divided_clk !== prev) begin
          if ($realtime - t_edge < min_pulse) min_pulse = $realtime - t_edge;
          t_edge = $realtime;
          prev = divided_clk;
        end
      end
    end
  endtask

  real phase, worst_runt;

  initial begin
    $dumpfile("build/tb_ring_divider.vcd");
    $dumpvars(0, tb_ring_divider);

    #25 reset = 1'b0;

    $display("--- Part 1: every tap against a %0.1f ns input", T_IN);
    for (k = 0; k < 8; k = k + 1) check_tap(k[2:0]);

    $display("--- Part 2: switching tap_sel 0 -> 1 while running, at 8 phases");
    worst_runt = 1.0e9;
    for (k = 0; k < 8; k = k + 1) begin
      tap_sel = 3'd0;
      @(posedge ring_clk);
      phase = k * T_IN / 8;
      #(phase);
      tap_sel = 3'd1;
      watch_min_pulse(T_IN * 4);
      // 0.01 ns means two transitions inside one 10 ps sample step: the mux
      // output moved at the switch instant and again at the very next edge.
      $display("  switch at phase %5.2f ns : shortest pulse afterwards %6.2f ns", phase, min_pulse);
      if (min_pulse < worst_runt) worst_runt = min_pulse;
    end
    $display("--- Part 2 result: shortest pulse after a live tap change is %0.2f ns", worst_runt);
    if (worst_runt < T_IN / 2)
      $display("    A runt DOES appear (shorter than the /1 half period of %0.1f ns).", T_IN / 2);
    else
      $display("    No runt seen in this sweep.");
    $display("    Conclusion: only change tap_sel while idle. The register file blocks it while busy.");

    if (errors == 0) $display("RESULT: PASS");
    else             $display("RESULT: FAIL (%0d errors)", errors);
    $finish;
  end

endmodule
