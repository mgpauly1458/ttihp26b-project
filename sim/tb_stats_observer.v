// tb_stats_observer.v -- stats_observer alone, fed hand-made done pulses
//   1 reset values                         2 three samples: count, min, max, sum
//   3 a timed-out done, or a value over 16 bits, is not a sample     4 a sum that carries into its top bytes
//   5 clear                                6 count saturates at 65535 and the statistics freeze
//   7 dice: never 0, changes, signature and string bytes
`timescale 1ns / 1ps

module tb_stats_observer;

  reg         clk = 1'b0;
  reg         reset = 1'b1;
  reg         done = 1'b0;
  reg         timeout_error = 1'b0;
  reg  [31:0] ref_count = 32'd0;
  reg         clear = 1'b0;
  reg  [4:0]  index = 5'd0;
  wire [7:0]  stats_byte;

  always #10 clk = ~clk;

  stats_observer dut (
      .clk(clk), .reset(reset), .done(done), .timeout_error(timeout_error),
      .ref_count(ref_count), .clear(clear), .index(index), .stats_byte(stats_byte));

  integer errors = 0;

  // One measurement as measure_core presents it: value and flag settle, done rises, stays, falls at the next start.
  task give;
    input [31:0] v;
    input        tmo;
    begin
      @(posedge clk); #1; ref_count = v; timeout_error = tmo;
      @(posedge clk); #1; done = 1'b1;
      repeat (3) @(posedge clk); #1;
      done = 1'b0; timeout_error = 1'b0;
    end
  endtask

  reg [31:0] got;
  integer    b;
  task read_field;              // little-endian field of n bytes starting at index i -> got
    input [4:0] i;
    input integer n;
    begin
      got = 32'd0;
      for (b = 0; b < n; b = b + 1) begin
        index = i + b; #1;
        got = got | ({24'd0, stats_byte} << (8 * b));
      end
    end
  endtask

  task expect_all;
    input [15:0] c;
    input [15:0] mn;
    input [15:0] mx;
    input [31:0] sm;
    begin
      read_field(5'd0, 2); if (got !== {16'd0, c})  begin $display("  FAIL: count %0d, expected %0d", got, c); errors = errors + 1; end
      read_field(5'd2, 2); if (got !== {16'd0, mn}) begin $display("  FAIL: min %h, expected %h", got, mn);   errors = errors + 1; end
      read_field(5'd4, 2); if (got !== {16'd0, mx}) begin $display("  FAIL: max %h, expected %h", got, mx);   errors = errors + 1; end
      read_field(5'd6, 4); if (got !== sm)          begin $display("  FAIL: sum %h, expected %h", got, sm);   errors = errors + 1; end
    end
  endtask

  integer    n;
  reg [7:0]  dice_a, dice_b;
  reg [8*14:1] text;

  initial begin
    $dumpfile("build/tb_stats_observer.vcd");
    $dumpvars(0, tb_stats_observer);
    repeat (3) @(posedge clk); #1 reset = 1'b0;

    $display("--- 1. reset values");
    expect_all(16'd0, 16'hFFFF, 16'd0, 32'd0);

    $display("--- 2. three samples 229, 231, 228");
    give(32'd229, 1'b0); give(32'd231, 1'b0); give(32'd228, 1'b0);
    expect_all(16'd3, 16'd228, 16'd231, 32'd688);

    $display("--- 3. a timed-out done and a value over 16 bits are ignored");
    give(32'd5, 1'b1);
    give(32'h00010002, 1'b0);
    expect_all(16'd3, 16'd228, 16'd231, 32'd688);

    $display("--- 4. carries: 3 x FFFF, then FFFF + 1");
    @(posedge clk); #1 clear = 1'b1; @(posedge clk); #1 clear = 1'b0;
    give(32'h0000FFFF, 1'b0); give(32'h0000FFFF, 1'b0); give(32'h0000FFFF, 1'b0);
    expect_all(16'd3, 16'hFFFF, 16'hFFFF, 32'h0002_FFFD);
    @(posedge clk); #1 clear = 1'b1; @(posedge clk); #1 clear = 1'b0;
    give(32'h0000FFFF, 1'b0); give(32'h00000001, 1'b0);
    expect_all(16'd2, 16'h0001, 16'hFFFF, 32'h0001_0000);

    $display("--- 5. clear");
    @(posedge clk); #1 clear = 1'b1; @(posedge clk); #1 clear = 1'b0;
    expect_all(16'd0, 16'hFFFF, 16'd0, 32'd0);

    $display("--- 6. saturation: 65540 samples of 0xFFFE (the largest sum there can be, near enough)");
    for (n = 0; n < 65540; n = n + 1) give(32'h0000FFFE, 1'b0);
    expect_all(16'hFFFF, 16'hFFFE, 16'hFFFE, 32'd65535 * 32'h0000FFFE);
    give(32'd1, 1'b0);                                   // would move min if not frozen
    expect_all(16'hFFFF, 16'hFFFE, 16'hFFFE, 32'd65535 * 32'h0000FFFE);

    $display("--- 7. dice, signature, string");
    index = 5'd10; #1 dice_a = stats_byte;
    repeat (5) @(posedge clk); #1 dice_b = stats_byte;
    if (dice_a === dice_b || dice_a === 8'd0 || dice_b === 8'd0) begin $display("  FAIL: dice %h %h", dice_a, dice_b); errors = errors + 1; end
    for (n = 0; n < 600; n = n + 1) begin                // a full LFSR period and more, with samples folded in
      @(posedge clk); #1;
      if (stats_byte === 8'd0 && n > 1 && dice_b === 8'd0) begin $display("  FAIL: dice stuck at 0"); errors = errors + 1; end
      dice_b = stats_byte;
      if (n % 50 == 0) begin done = 1'b1; ref_count = n + 1; end else done = 1'b0;
    end
    done = 1'b0;
    index = 5'd11; #1 if (stats_byte !== 8'h5A) begin $display("  FAIL: signature %h", stats_byte); errors = errors + 1; end
    for (n = 0; n < 14; n = n + 1) begin index = 12 + n; #1 text[8*(14-n) -: 8] = stats_byte; end
    $display("string = \"%s\"", text);
    if (text !== "RING METER 26B") begin $display("  FAIL: string"); errors = errors + 1; end

    if (errors == 0) $display("RESULT: PASS");
    else             $display("RESULT: FAIL (%0d errors)", errors);
    $finish;
  end

endmodule
