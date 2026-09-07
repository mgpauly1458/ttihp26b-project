// ============================================================================
// tb_rings.v -- every STRUCTURAL ring oscillates at the frequency its
//               netlist predicts, and stops when told to
// ----------------------------------------------------------------------------
// Compiled WITHOUT SIM, so the ring modules use their cell-level netlists,
// with the delay stand-ins from sim/sg13g2_cells_sim.v. What this proves is
// that each netlist is wired into a loop with an odd number of inversions,
// that the enable works, that the tap ring's eight codes give eight
// distinct, monotonic, correctly ordered periods, and that the analog macro
// is silent. The numbers are checked against the closed-form period from
// the stand-in delays, to the picosecond, because that is what a wiring
// error would break.
// ============================================================================
`timescale 1ns / 1ps

module tb_rings;

  // Stand-in cell delays, ns. Must match sim/sg13g2_cells_sim.v.
  localparam real T_INV1  = 0.055;
  localparam real T_INV8  = 0.060;
  localparam real T_NAND1 = 0.065;
  localparam real T_NAND2 = 0.060;
  localparam real T_MUX4  = 0.180;
  localparam real T_MUX2  = 0.110;

  reg  [7:0] code    = 8'd0;
  reg  [7:0] ring_en = 8'd0;
  wire [7:0] ring_clk;

  ring_bank dut (.trim_code(code), .ring_en(ring_en), .ring_clk(ring_clk));

  integer errors = 0;
  integer i;
  real    t0, t1, period;

  // Period of ring k, averaged over 20 cycles.
  task measure;
    input integer k;
    begin
      @(posedge ring_clk[k]);
      @(posedge ring_clk[k]); t0 = $realtime;
      for (i = 0; i < 20; i = i + 1) @(posedge ring_clk[k]);
      t1 = $realtime;
      period = (t1 - t0) / 20;
    end
  endtask

  task check_ring;
    input integer k;
    input real    expect;
    input [63:0]  name;           // 8 characters
    begin
      ring_en = 8'b1 << k;
      #5;
      measure(k);
      $display("slot %0d %s : period %6.3f ns  (%6.1f MHz)  expected %6.3f ns",
               k, name, period, 1.0e3 / period, expect);
      if (period > expect + 0.001 || period < expect - 0.001) begin
        $display("  FAIL");
        errors = errors + 1;
      end
    end
  endtask

  // With enable low the output must sit still.
  task check_stopped;
    input integer k;
    integer n, edges;
    reg prev;
    begin
      ring_en = 8'd0;
      #5;
      edges = 0; prev = ring_clk[k];
      for (n = 0; n < 200; n = n + 1) begin
        #0.05;
        if (ring_clk[k] !== prev) edges = edges + 1;
        prev = ring_clk[k];
      end
      if (edges != 0) begin
        $display("  FAIL: slot %0d still toggling with enable low", k);
        errors = errors + 1;
      end
    end
  endtask

  real    prev_period;
  integer c;                    // tap-ring code; measure() uses i itself

  initial begin
    $dumpfile("build/tb_rings.vcd");
    $dumpvars(0, tb_rings);

    // Let every chain flush its power-up X with enable low before anything
    // is enabled. Enabling at time zero lets an X pulse into the loop, and
    // a circulating X never dies in simulation. Silicon has no X.
    #10;

    check_ring(0, 2 * (T_NAND1 + 20 * T_INV1), "21_min  "); check_stopped(0);
    check_ring(1, 2 * (T_NAND1 + 20 * T_INV1), "21_min  "); check_stopped(1);
    check_ring(2, 2 * (T_NAND1 + 20 * T_INV1), "21_min  "); check_stopped(2);
    check_ring(3, 2 * (T_NAND1 + 20 * T_INV1), "21_min  "); check_stopped(3);
    check_ring(4, 2 * (T_NAND2 + 20 * T_INV8), "21_hd   "); check_stopped(4);
    check_ring(5, 2 * (T_NAND1 + 10 * T_INV1), "11_min  "); check_stopped(5);

    $display("--- slot 6, tap ring, all eight codes");
    prev_period = 1.0e9;
    for (c = 0; c < 8; c = c + 1) begin
      code = c[7:0];
      check_ring(6, 2 * (T_NAND1 + (18 - 2 * c) * T_INV1 + T_MUX4 + T_MUX2), "tap     ");
      if (period >= prev_period) begin
        $display("  FAIL: not monotonic (code %0d not faster than code %0d)", c, c - 1);
        errors = errors + 1;
      end
      prev_period = period;
    end
    check_stopped(6);

    // Slot 7 is the hard macro: without SIM it is a blackbox with no body,
    // so its output floats. What matters is that nothing here drives it.
    $display("--- slot 7, analog macro: blackbox, must be silent without SIM");
    ring_en = 8'b1000_0000; code = 8'd255;
    #20;
    if (ring_clk[7] !== 1'bz && ring_clk[7] !== 1'b0) begin
      $display("  FAIL: macro output is %b, expected z (blackbox) or 0", ring_clk[7]);
      errors = errors + 1;
    end else $display("slot 7 macro   : output %b (blackbox), as expected", ring_clk[7]);

    if (errors == 0) $display("RESULT: PASS");
    else             $display("RESULT: FAIL (%0d errors)", errors);
    $finish;
  end

endmodule
