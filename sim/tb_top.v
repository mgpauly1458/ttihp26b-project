// ============================================================================
// tb_top.v -- the whole tile through its pins
// ----------------------------------------------------------------------------
// Drives tt_um_mgpauly1458_ringmeter exactly as a host microcontroller would:
// write strobes on the dedicated inputs, data on the bidirectionals, bytes
// read back on the dedicated outputs. Compiled with SIM, so the rings are
// behavioural models with known frequencies.
//
//   1. ID byte reads back after reset (the interface is alive).
//   2. Written registers read back.
//   3. One measurement on the analog model at code 255 (400 MHz) gives the
//      count the formula predicts, within +/-1.
//   4. The same ring at one code, through all eight divider taps, recovers
//      the same frequency each time: the divide ratio really is multiplied
//      back out.
//   5. Writes while busy are ignored and flagged; the flag clears on the
//      next accepted START.
//   6. RESULT is a shadow: reading it during the next measurement returns
//      the previous, complete result.
//   7. A dead code times out cleanly through the pins.
// ============================================================================
`timescale 1ns / 1ps

module tb_top;

  localparam real T_REF   = 20.0;              // 50 MHz
  localparam real F_REF   = 1.0e9 / T_REF;

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

  real f_model, f_meas, c_expect;
  integer k;
  reg [31:0] first_result;

  initial begin
    $dumpfile("build/tb_top.vcd");
    $dumpvars(0, tb_top);

    repeat (3) @(posedge clk); #1 rst_n = 1'b1;
    repeat (3) @(posedge clk);

    $display("--- 1. ID");
    host_read(R_ID);
    $display("ID = 0x%02X", rdata);
    if (rdata !== 8'hA5) begin $display("  FAIL"); errors = errors + 1; end

    $display("--- 2. Register readback");
    host_write(A_TRIM, 8'h5C);
    host_write(A_RING_SEL, 8'd6);
    host_write(A_TAP_SEL, 8'd5);
    host_read(R_TRIM);  if (rdata !== 8'h5C) begin $display("  FAIL: TRIM readback %02X", rdata); errors = errors + 1; end
    host_read(R_SEL);   if (rdata !== 8'b00_101_110) begin $display("  FAIL: SEL readback %b", rdata); errors = errors + 1; end
    $display("TRIM and SEL read back correctly");

    $display("--- 3. One measurement: ring 7, code 255, tap 3, N 200");
    measure(3'd7, 8'd255, 3'd3, 16'd200, 16'd16000);
    f_model  = dut.u_rings.u_ring7.u_model.freq_of_code(8'd255);
    c_expect = 200.0 * 8 * F_REF / f_model;
    f_meas   = 200.0 * 8 * F_REF / result;
    $display("status %b  result %0d  expected %0.2f  f_meas %0.3f MHz  f_model %0.3f MHz",
             status, result, c_expect, f_meas / 1e6, f_model / 1e6);
    if (status[ST_TIMEOUT] || result > c_expect + 1 || result < c_expect - 1) begin
      $display("  FAIL"); errors = errors + 1;
    end

    $display("--- 4. All eight taps, ring 7 code 128");
    f_model = dut.u_rings.u_ring7.u_model.freq_of_code(8'd128);
    for (k = 0; k < 8; k = k + 1) begin
      measure(3'd7, 8'd128, k[2:0], 16'd200, 16'd60000);
      f_meas = 200.0 * (1 << k) * F_REF / result;
      $display("tap %0d : count %6d  f_meas %8.3f MHz  (model %8.3f MHz)  err %+6.3f %%",
               k, result, f_meas / 1e6, f_model / 1e6, 100.0 * (f_meas - f_model) / f_model);
      // +/-1 count on the count, so the frequency error bound is 1/count.
      if (status[ST_TIMEOUT] || (f_meas > f_model * (1.0 + 1.5 / result)) || (f_meas < f_model * (1.0 - 1.5 / result))) begin
        $display("  FAIL"); errors = errors + 1;
      end
    end

    $display("--- 5. Writes while busy are ignored and flagged");
    // A long measurement: N = 60000 on ring 0 at tap 7 takes ages.
    host_write(A_RING_SEL, 8'd0);
    host_write(A_TAP_SEL, 8'd7);
    host_write(A_TARGET_L, 8'd0);  host_write(A_TARGET_H, 8'd4);     // 1024 periods of /128
    host_write(A_TIMEOUT_L, 8'hFF); host_write(A_TIMEOUT_H, 8'hFF);
    host_write(A_CONTROL, 8'h01);
    host_read(R_STATUS);
    if (!rdata[ST_BUSY]) begin $display("  FAIL: not busy"); errors = errors + 1; end
    host_write(A_RING_SEL, 8'd5);            // must be ignored
    host_write(A_CONTROL, 8'h01);            // START while busy: also ignored
    host_read(R_STATUS);
    $display("STATUS during busy after illegal writes = %b", rdata);
    if (!rdata[ST_IGNORED]) begin $display("  FAIL: write_ignored not set"); errors = errors + 1; end
    host_read(R_SEL);
    if (rdata[2:0] !== 3'd0) begin $display("  FAIL: RING_SEL changed while busy"); errors = errors + 1; end
    wait_done;
    read_result;
    first_result = result;
    host_write(A_RING_SEL, 8'd5);            // idle now: accepted
    host_read(R_SEL);
    if (rdata[2:0] !== 3'd5) begin $display("  FAIL: RING_SEL write not accepted when idle"); errors = errors + 1; end
    host_read(R_STATUS);
    if (!rdata[ST_IGNORED]) begin $display("  FAIL: flag should persist until next START"); errors = errors + 1; end

    $display("--- 6. RESULT shadow holds during the next measurement");
    host_write(A_CONTROL, 8'h01);            // start another long one (ring 5, /128, 1024)
    host_read(R_STATUS);
    if (rdata[ST_IGNORED]) begin $display("  FAIL: flag not cleared by accepted START"); errors = errors + 1; end
    if (!rdata[ST_BUSY])   begin $display("  FAIL: not busy"); errors = errors + 1; end
    read_result;
    $display("previous result %0d, read mid-measurement %0d", first_result, result);
    if (result !== first_result) begin $display("  FAIL: shadow changed"); errors = errors + 1; end
    wait_done;

    $display("--- 7. Dead code times out through the pins");
    measure(3'd7, 8'd0, 3'd3, 16'd200, 16'd2000);
    $display("status %b after %0d polls", status, polls);
    if (!status[ST_TIMEOUT] || !status[ST_DONE]) begin $display("  FAIL"); errors = errors + 1; end
    // And the instrument is not stuck afterwards.
    measure(3'd7, 8'd255, 3'd3, 16'd200, 16'd16000);
    if (status[ST_TIMEOUT]) begin $display("  FAIL: stuck after timeout"); errors = errors + 1; end
    else $display("recovered: result %0d", result);

    if (errors == 0) $display("RESULT: PASS");
    else             $display("RESULT: FAIL (%0d errors)", errors);
    $finish;
  end

endmodule
