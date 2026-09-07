// ============================================================================
// tb_ring_model.v -- checks that the ground truth is what we think it is
// ----------------------------------------------------------------------------
// For a handful of codes: enable the model, measure the period between rising
// edges over several cycles, and compare against the curve the model claims
// (read straight out of the model's own freq_of_code function). Also checks
// the dead zone is silent and that enable=0 holds the output low.
//
// Allowed error: the model rounds each half-period to 1 ps, so the measured
// period can differ from 1/f by up to 2 ps.
// ============================================================================
`timescale 1ns / 1ps

module tb_ring_model;

  reg  [7:0] code   = 8'd0;
  reg        enable = 1'b0;
  wire       clk_out;

  ring_model dut (.code(code), .enable(enable), .clk_out(clk_out));

  integer errors = 0;
  integer i;
  real    t_first, t_last, period_ns, expect_ns;

  // Measure the average period over NCYC rising edges.
  localparam NCYC = 10;
  task measure_period;       // result lands in period_ns
    begin
      @(posedge clk_out); t_first = $realtime;
      for (i = 0; i < NCYC; i = i + 1) @(posedge clk_out);
      t_last = $realtime;
      period_ns = (t_last - t_first) / NCYC;
    end
  endtask

  task check_code;
    input [7:0] c;
    begin
      code = c;
      #50;                                   // let the new code take effect
      measure_period;
      expect_ns = 1.0e9 / dut.freq_of_code(c);
      $display("code %3d : f = %8.3f MHz  period = %7.4f ns  expected %7.4f ns",
               c, 1.0e3 / period_ns, period_ns, expect_ns);
      if (period_ns > expect_ns + 0.002 || period_ns < expect_ns - 0.002) begin
        $display("  FAIL: period off by more than 2 ps");
        errors = errors + 1;
      end
    end
  endtask

  // Check that clk_out stays low for a while: sample it every nanosecond for
  // 1 us (20 cycles even at F_MIN) and count rising transitions.
  task check_silent;
    input [7:0] c;
    integer edges, n;
    reg prev;
    begin
      code = c;
      #50;
      edges = 0;
      prev = clk_out;
      for (n = 0; n < 1000; n = n + 1) begin
        #1;
        if (clk_out === 1'b1 && prev === 1'b0) edges = edges + 1;
        prev = clk_out;
      end
      if (edges != 0 || clk_out !== 1'b0) begin
        $display("code %3d : FAIL, expected silence but saw %0d edges", c, edges);
        errors = errors + 1;
      end else begin
        $display("code %3d : silent, as expected", c);
      end
    end
  endtask

  initial begin
    $dumpfile("build/tb_ring_model.vcd");
    $dumpvars(0, tb_ring_model);

    // Enable low: nothing should happen even at a live code.
    enable = 1'b0;
    check_silent(8'd200);

    enable = 1'b1;
    // Dead zone, and the boundary of it.
    check_silent(8'd0);
    check_silent(8'd19);
    // First live code is F_MIN, not zero: the offset.
    check_code(8'd20);
    check_code(8'd21);
    // Middle of the curve.
    check_code(8'd64);
    check_code(8'd128);
    check_code(8'd200);
    // Top: F_MAX.
    check_code(8'd254);
    check_code(8'd255);

    // A code change mid-run should be honoured at the next edge, not ignored.
    code = 8'd255; #100;
    code = 8'd20;  #50;
    measure_period;
    expect_ns = 1.0e9 / dut.freq_of_code(8'd20);
    if (period_ns > expect_ns + 0.002 || period_ns < expect_ns - 0.002) begin
      $display("FAIL: period after code change is %7.4f ns, expected %7.4f", period_ns, expect_ns);
      errors = errors + 1;
    end else begin
      $display("code change 255->20 honoured: %7.4f ns", period_ns);
    end

    if (errors == 0) $display("RESULT: PASS");
    else             $display("RESULT: FAIL (%0d errors)", errors);
    $finish;
  end

endmodule
