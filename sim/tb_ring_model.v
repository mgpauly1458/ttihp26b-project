// tb_ring_model.v -- ring_model matches its own freq_of_code curve
// Per code: period over 10 rising edges against 1/f from dut.freq_of_code, tolerance 2 ps (the model
// rounds each half-period to 1 ps). Also: the dead zone is silent, enable = 0 holds the output low,
// and a mid-run code change is honoured at the next edge.
`timescale 1ns / 1ps

module tb_ring_model;

  reg  [7:0] code   = 8'd0;
  reg        enable = 1'b0;
  wire       clk_out;

  ring_model dut (.code(code), .enable(enable), .clk_out(clk_out));

  integer errors = 0;
  integer i;
  real    t_first, t_last, period_ns, expect_ns;

  // Average period over NCYC rising edges.
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

  // clk_out must stay low: sample every 1 ns for 1 us (20 cycles even at F_MIN), count rising edges.
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

    // enable low at a live code
    enable = 1'b0;
    check_silent(8'd200);

    enable = 1'b1;
    // dead zone and its boundary
    check_silent(8'd0);
    check_silent(8'd19);
    // first live code is F_MIN, not zero
    check_code(8'd20);
    check_code(8'd21);
    // middle of the curve
    check_code(8'd64);
    check_code(8'd128);
    check_code(8'd200);
    // top: F_MAX
    check_code(8'd254);
    check_code(8'd255);

    // A code change mid-run must be honoured at the next edge.
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
