// tb_stats.v -- the stats_observer page through the pins of the whole tile (SIM: rings are models)
//   1 after reset: count 0, min all ones, max 0, sum 0, signature, and page 0 still reads the ID
//   2 ten measurements with no configuration write between them: count/min/max/sum match what the host saw
//   3 a configuration write clears; a timed-out measurement is not counted; the next good one is
//   4 the page bit changes nothing else: a write made with ui_in[7] = 1 lands as usual
`timescale 1ns / 1ps

module tb_stats;

  localparam real T_REF = 20.0;                // 50 MHz

  reg        clk   = 1'b0;
  reg        rst_n = 1'b0;
  reg        ena   = 1'b1;
  reg  [7:0] ui_in;
  reg  [7:0] uio_in = 8'd0;
  wire [7:0] uo_out, uio_out, uio_oe;

  always #(T_REF / 2) clk = ~clk;

  tt_um_mgpauly1458_ringmeter dut (
      .ui_in(ui_in), .uo_out(uo_out), .uio_in(uio_in), .uio_out(uio_out),
      .uio_oe(uio_oe), .ena(ena), .clk(clk), .rst_n(rst_n));

  integer errors = 0;
  `include "tb_pins.vh"

  // Little-endian field of n bytes starting at stats index i -> field
  reg [31:0] field;
  integer    fb;
  task stats_field;
    input [4:0] i;
    input integer n;
    begin
      field = 32'd0;
      for (fb = 0; fb < n; fb = fb + 1) begin
        stats_read(i + fb);
        field = field | ({24'd0, rdata} << (8 * fb));
      end
    end
  endtask

  task expect_stats;
    input [15:0] c;
    input [15:0] mn;
    input [15:0] mx;
    input [31:0] sm;
    begin
      stats_field(5'd0, 2); if (field !== {16'd0, c})  begin $display("  FAIL: count %0d, expected %0d", field, c); errors = errors + 1; end
      stats_field(5'd2, 2); if (field !== {16'd0, mn}) begin $display("  FAIL: min %0d, expected %0d", field, mn);  errors = errors + 1; end
      stats_field(5'd4, 2); if (field !== {16'd0, mx}) begin $display("  FAIL: max %0d, expected %0d", field, mx);  errors = errors + 1; end
      stats_field(5'd6, 4); if (field !== sm)          begin $display("  FAIL: sum %0d, expected %0d", field, sm);  errors = errors + 1; end
    end
  endtask

  integer    m;
  reg [31:0] seen_min, seen_max;
  reg [31:0] seen_sum;

  initial begin
    $dumpfile("build/tb_stats.vcd");
    $dumpvars(0, tb_stats);

    repeat (3) @(posedge clk); #1 rst_n = 1'b1;
    repeat (3) @(posedge clk);

    $display("--- 1. after reset");
    expect_stats(16'd0, 16'hFFFF, 16'd0, 32'd0);
    stats_read(5'd11); if (rdata !== 8'h5A) begin $display("  FAIL: signature %02X", rdata); errors = errors + 1; end
    host_read(R_ID);   if (rdata !== 8'hA5) begin $display("  FAIL: ID %02X after a stats read", rdata); errors = errors + 1; end

    $display("--- 2. ten measurements of ring 7, code 200, tap 0, N 37 (START only between them)");
    measure(3'd7, 8'd200, 3'd0, 16'd37, 16'd16000);
    seen_min = result; seen_max = result; seen_sum = result;
    for (m = 1; m < 10; m = m + 1) begin
      repeat (m) @(posedge clk);               // move the start phase so the +/-1 count can show
      host_write(A_CONTROL, 8'h01);
      wait_done;
      read_result;
      if (result < seen_min) seen_min = result;
      if (result > seen_max) seen_max = result;
      seen_sum = seen_sum + result;
    end
    $display("host saw min %0d max %0d sum %0d", seen_min, seen_max, seen_sum);
    expect_stats(16'd10, seen_min[15:0], seen_max[15:0], seen_sum);

    $display("--- 3. clear on a configuration write; a timeout is not a sample");
    host_write(A_TIMEOUT_L, 8'd5);
    host_write(A_TIMEOUT_H, 8'd0);
    expect_stats(16'd0, 16'hFFFF, 16'd0, 32'd0);
    host_write(A_CONTROL, 8'h01);
    wait_done;
    if (!rdata[ST_TIMEOUT]) begin $display("  FAIL: expected a timeout"); errors = errors + 1; end
    expect_stats(16'd0, 16'hFFFF, 16'd0, 32'd0);
    measure(3'd7, 8'd200, 3'd0, 16'd37, 16'd16000);
    expect_stats(16'd1, result[15:0], result[15:0], result);

    $display("--- 4. a write with the page bit high lands as usual (and clears)");
    pin_stats = 1'b1;
    host_write(A_TRIM, 8'h3C);
    pin_stats = 1'b0;
    host_read(R_TRIM); if (rdata !== 8'h3C) begin $display("  FAIL: TRIM %02X", rdata); errors = errors + 1; end
    expect_stats(16'd0, 16'hFFFF, 16'd0, 32'd0);

    if (errors == 0) $display("RESULT: PASS");
    else             $display("RESULT: FAIL (%0d errors)", errors);
    $finish;
  end

endmodule
