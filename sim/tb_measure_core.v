// ============================================================================
// tb_measure_core.v -- the counter against a clean clock of known frequency
// ----------------------------------------------------------------------------
// No rings, no divider, no CDC awkwardness beyond what the core itself has:
// a generated clock of exactly known period stands in for the divided ring.
// The expected count is target_n * T_ring / T_ref, and the measured count
// must be within +/-1 of it (the quantisation described in the core's
// header). Several target_n values, several ring periods, including ones
// that are not a nice multiple of the reference.
//
// Then the failure path: no ring clock at all must produce timeout_error,
// not a hang, and a measurement afterwards must still work.
// ============================================================================
`timescale 1ns / 1ps

module tb_measure_core;

  localparam real T_REF = 20.0;               // 50 MHz reference

  reg         ref_clk = 1'b0;
  reg         reset   = 1'b1;
  reg         ring    = 1'b0;
  reg         ring_on = 1'b0;
  reg         start   = 1'b0;
  reg  [15:0] target_n = 16'd0;
  reg  [15:0] timeout  = 16'd0;
  wire [31:0] ref_count;
  wire        done, busy, timeout_error;

  always #(T_REF / 2) ref_clk = ~ref_clk;

  // The stand-in ring: a clock whose period we set.
  real t_ring = 10.0;
  always begin
    if (ring_on) #(t_ring / 2) ring = ~ring;
    else begin ring = 1'b0; @(ring_on); end
  end

  measure_core dut (
      .ref_clk       (ref_clk),
      .reset         (reset),
      .divided_ring  (ring),
      .start         (start),
      .target_n      (target_n),
      .timeout       (timeout),
      .ref_count     (ref_count),
      .done          (done),
      .busy          (busy),
      .timeout_error (timeout_error)
  );

  integer errors = 0;
  real    expect;
  integer cycles;

  task pulse_start;
    begin
      @(posedge ref_clk); #1 start = 1'b1;
      @(posedge ref_clk); #1 start = 1'b0;
    end
  endtask

  // Wait for done, counting reference cycles so a hang is caught.
  task wait_done;
    begin
      cycles = 0;
      while (!done && cycles < 200000) begin
        @(posedge ref_clk); cycles = cycles + 1;
      end
      if (!done) begin
        $display("FAIL: never finished (hang)");
        errors = errors + 1;
      end
    end
  endtask

  task measure;
    input real    period;
    input [15:0]  n;
    begin
      t_ring   = period;
      target_n = n;
      timeout  = 16'd60000;
      pulse_start;
      if (!busy) begin $display("FAIL: busy not raised"); errors = errors + 1; end
      wait_done;
      expect = n * period / T_REF;
      $display("T_ring %8.3f ns  N %5d : count %6d  expected %9.2f  %s",
               period, n, ref_count, expect, timeout_error ? "TIMEOUT" : "");
      if (timeout_error) begin
        $display("  FAIL: unexpected timeout");
        errors = errors + 1;
      end else if (ref_count > expect + 1.0 || ref_count < expect - 1.0) begin
        $display("  FAIL: outside +/-1 count");
        errors = errors + 1;
      end
      if (busy) begin $display("FAIL: still busy after done"); errors = errors + 1; end
    end
  endtask

  initial begin
    $dumpfile("build/tb_measure_core.vcd");
    $dumpvars(0, tb_measure_core);

    repeat (3) @(posedge ref_clk);
    #1 reset = 1'b0;
    ring_on = 1'b1;
    repeat (5) @(posedge ref_clk);

    $display("--- Clean clocks, several target_n and ring periods");
    // Ring slower than the reference: many counts per period.
    measure(100.0, 16'd1);
    measure(100.0, 16'd10);
    measure(100.0, 16'd100);
    // Ring faster than the reference: fractional counts per period, where
    // the quantisation does its worst.
    measure(7.3,   16'd100);
    measure(7.3,   16'd1000);
    measure(2.5,   16'd4000);      // 400 MHz ring, undivided
    // Awkward ratio very close to an integer, both sides of it.
    measure(19.99, 16'd200);
    measure(20.01, 16'd200);
    // Back to back with no idle time between: SETTLE handshake must cope.
    measure(50.0,  16'd50);
    measure(50.0,  16'd50);

    $display("--- Timeout: ring stopped entirely");
    ring_on  = 1'b0;
    target_n = 16'd10;
    timeout  = 16'd500;
    pulse_start;
    wait_done;
    $display("no ring : done=%b timeout_error=%b busy=%b after %0d cycles",
             done, timeout_error, busy, cycles);
    if (!timeout_error) begin $display("  FAIL: no timeout_error"); errors = errors + 1; end
    if (cycles > 520)   begin $display("  FAIL: took too long to time out"); errors = errors + 1; end

    $display("--- Timeout: ring alive but too slow for the limit");
    ring_on  = 1'b1;
    t_ring   = 1000.0;
    target_n = 16'd100;           // would need 5000 reference cycles
    timeout  = 16'd1000;
    pulse_start;
    wait_done;
    $display("slow ring : timeout_error=%b after %0d cycles", timeout_error, cycles);
    if (!timeout_error) begin $display("  FAIL: no timeout_error"); errors = errors + 1; end

    $display("--- Recovery: a normal measurement after the timeouts");
    measure(100.0, 16'd10);

    $display("--- Timeout of 0 gives up immediately, by design");
    timeout = 16'd0;
    pulse_start;
    wait_done;
    if (!timeout_error) begin $display("  FAIL: timeout=0 did not error"); errors = errors + 1; end
    else $display("timeout=0 : timeout_error=%b, as documented", timeout_error);

    if (errors == 0) $display("RESULT: PASS");
    else             $display("RESULT: FAIL (%0d errors)", errors);
    $finish;
  end

endmodule
