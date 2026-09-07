// ============================================================================
// tb_ring_mux.v -- every select routes the right ring and enables only it
// ----------------------------------------------------------------------------
// Eight ring inputs are driven by eight distinguishable clocks (period
// 10 + sel ns). For each sel: the output period must match that ring's, and
// ring_en must be one-hot at that position. Then enable=0 must clear ring_en
// entirely.
// ============================================================================
`timescale 1ns / 1ps

module tb_ring_mux;

  reg  [7:0] ring_in = 8'd0;
  reg  [2:0] sel     = 3'd0;
  reg        enable  = 1'b1;
  wire       ring_out;
  wire [7:0] ring_en;

  ring_mux dut (
      .ring_in  (ring_in),
      .sel      (sel),
      .enable   (enable),
      .ring_out (ring_out),
      .ring_en  (ring_en)
  );

  // Eight clocks with distinct periods: 10, 11, ... 17 ns.
  always #5.0 ring_in[0] = ~ring_in[0];
  always #5.5 ring_in[1] = ~ring_in[1];
  always #6.0 ring_in[2] = ~ring_in[2];
  always #6.5 ring_in[3] = ~ring_in[3];
  always #7.0 ring_in[4] = ~ring_in[4];
  always #7.5 ring_in[5] = ~ring_in[5];
  always #8.0 ring_in[6] = ~ring_in[6];
  always #8.5 ring_in[7] = ~ring_in[7];

  integer errors = 0;
  integer k, i;
  real    t0, t1, period;

  initial begin
    $dumpfile("build/tb_ring_mux.vcd");
    $dumpvars(0, tb_ring_mux);

    for (k = 0; k < 8; k = k + 1) begin
      sel = k[2:0];
      #1;
      @(posedge ring_out); t0 = $realtime;
      for (i = 0; i < 4; i = i + 1) @(posedge ring_out);
      t1 = $realtime;
      period = (t1 - t0) / 4;
      $display("sel %0d : period %5.2f ns (expected %5.2f)  ring_en = %b",
               k, period, 10.0 + k, ring_en);
      // Tolerance: the output buffer's 80 ps stand-in shifts every edge
      // equally, and (t1 - t0) / 4 is a real.
      if (period > 10.0 + k + 0.001 || period < 10.0 + k - 0.001) begin
        $display("  FAIL: wrong ring routed");
        errors = errors + 1;
      end
      if (ring_en != (8'b1 << k)) begin
        $display("  FAIL: ring_en not one-hot at %0d", k);
        errors = errors + 1;
      end
    end

    enable = 1'b0;
    #1;
    $display("enable=0 : ring_en = %b", ring_en);
    if (ring_en != 8'd0) begin
      $display("  FAIL: rings still enabled");
      errors = errors + 1;
    end

    if (errors == 0) $display("RESULT: PASS");
    else             $display("RESULT: FAIL (%0d errors)", errors);
    $finish;
  end

endmodule
