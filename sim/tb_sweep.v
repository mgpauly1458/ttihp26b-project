// ============================================================================
// tb_sweep.v -- the exit criterion: every code on every ring, through the pins
// ----------------------------------------------------------------------------
// For each of the 8 rings and each of the 256 trim codes: select the ring,
// set the code, pick a tap, measure, recover the frequency, and compare it
// with what the behavioural model behind that slot actually generates. Every
// row goes to build/sweep.csv; scripts/plot_sweep.py draws it.
//
// Pass conditions (from the brief, section 7)
//   * recovered frequency matches the model within the quantisation error
//     over the whole live range, including the nonlinear region;
//   * dead-zone codes return timeout_error, not a number, not a hang;
//   * no dropped or duplicated counts: the count is within +/-1 of the exact
//     ratio (plus the model's own 1 ps period rounding);
//   * no cross-contamination: ring 3 after ring 5 reads the same as ring 3
//     after ring 3.
//
// Tap policy
//   One tap per ring, from the table below. The sweep script on silicon
//   will do the same: it knows roughly how fast each ring is. tb_top
//   separately proves that every tap recovers the same frequency.
// ============================================================================
`timescale 1ns / 1ps

module tb_sweep;

  localparam real T_REF = 20.0;                 // 50 MHz reference
  localparam real F_REF = 1.0e9 / T_REF;
  localparam [15:0] N_PERIODS = 16'd200;        // divided-ring periods per measurement
  localparam [15:0] TIMEOUT   = 16'd16000;      // reference cycles; 320 us

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

  // Divider tap used for each ring. Rings 0-4 and 6-7 sit at or below
  // ~450 MHz; ring 5 (11 stages) is the fast one.
  function [2:0] tap_for_ring;
    input [2:0] ring;
    case (ring)
      3'd5:    tap_for_ring = 3'd4;
      default: tap_for_ring = 3'd3;
    endcase
  endfunction

  // What the model behind slot `ring` is generating right now. Reads the
  // code the model actually sees (after the ring wrapper's interpretation),
  // so the testbench does not have to know how each ring uses the code.
  function real model_freq;
    input [2:0] ring;
    case (ring)
      3'd0: model_freq = dut.u_rings.u_ring0.u_model.freq_of_code(dut.u_rings.u_ring0.u_model.code);
      3'd1: model_freq = dut.u_rings.u_ring1.u_model.freq_of_code(dut.u_rings.u_ring1.u_model.code);
      3'd2: model_freq = dut.u_rings.u_ring2.u_model.freq_of_code(dut.u_rings.u_ring2.u_model.code);
      3'd3: model_freq = dut.u_rings.u_ring3.u_model.freq_of_code(dut.u_rings.u_ring3.u_model.code);
      3'd4: model_freq = dut.u_rings.u_ring4.u_model.freq_of_code(dut.u_rings.u_ring4.u_model.code);
      3'd5: model_freq = dut.u_rings.u_ring5.u_model.freq_of_code(dut.u_rings.u_ring5.u_model.code);
      3'd6: model_freq = dut.u_rings.u_ring6.u_model.freq_of_code(dut.u_rings.u_ring6.u_model.code);
      default: model_freq = dut.u_rings.u_ring7.u_model.freq_of_code(dut.u_rings.u_ring7.u_model.code);
    endcase
  endfunction

  integer csv;
  integer ring, code;
  integer n_meas = 0, n_timeouts = 0, n_bad = 0;
  real    f_model, f_meas, c_expect, worst_err_pct, err_pct;
  reg [2:0]  tap;
  reg [31:0] r3a, r3b;

  initial begin
    // No waveform dump: 2048 measurements would make a multi-GB file.
    csv = $fopen("build/sweep.csv", "w");
    $fwrite(csv, "ring,code,tap,target_n,count,timeout_error,f_model_hz,f_meas_hz\n");

    repeat (3) @(posedge clk); #1 rst_n = 1'b1;
    repeat (3) @(posedge clk);

    worst_err_pct = 0.0;
    for (ring = 0; ring < 8; ring = ring + 1) begin
      tap = tap_for_ring(ring[2:0]);
      for (code = 0; code < 256; code = code + 1) begin
        measure(ring[2:0], code[7:0], tap, N_PERIODS, TIMEOUT);
        n_meas  = n_meas + 1;
        f_model = model_freq(ring[2:0]);

        if (status[ST_TIMEOUT]) begin
          n_timeouts = n_timeouts + 1;
          f_meas = 0.0;
          if (f_model != 0.0) begin
            $display("FAIL ring %0d code %0d: timeout but model runs at %0.3f MHz", ring, code, f_model / 1e6);
            n_bad = n_bad + 1;
          end
        end else begin
          f_meas   = N_PERIODS * (1 << tap) * F_REF / result;
          if (f_model == 0.0) begin
            $display("FAIL ring %0d code %0d: model is dead but got count %0d", ring, code, result);
            n_bad = n_bad + 1;
          end else begin
            c_expect = N_PERIODS * (1 << tap) * F_REF / f_model;
            // +/-1 count quantisation, plus the model's 1 ps period rounding
            // (well under 0.1 %).
            if (result > c_expect + 1.0 + 0.001 * c_expect ||
                result < c_expect - 1.0 - 0.001 * c_expect) begin
              $display("FAIL ring %0d code %0d: count %0d, expected %0.2f", ring, code, result, c_expect);
              n_bad = n_bad + 1;
            end
            err_pct = 100.0 * (f_meas - f_model) / f_model;
            if (err_pct < 0) err_pct = -err_pct;
            if (err_pct > worst_err_pct) worst_err_pct = err_pct;
          end
        end

        $fwrite(csv, "%0d,%0d,%0d,%0d,%0d,%0d,%0.1f,%0.1f\n",
                ring, code, tap, N_PERIODS, result, status[ST_TIMEOUT], f_model, f_meas);
      end
      $display("ring %0d done: %0d measurements so far, %0d timeouts, %0d bad", ring, n_meas, n_timeouts, n_bad);
    end
    $fclose(csv);

    $display("--- Cross-contamination: ring 3, then ring 5, then ring 3 again");
    measure(3'd3, 8'd100, 3'd3, N_PERIODS, TIMEOUT); r3a = result;
    measure(3'd5, 8'd100, 3'd4, N_PERIODS, TIMEOUT);
    measure(3'd3, 8'd100, 3'd3, N_PERIODS, TIMEOUT); r3b = result;
    $display("ring 3: %0d then %0d", r3a, r3b);
    if (r3a > r3b + 1 || r3b > r3a + 1) begin
      $display("FAIL: ring 3 reads differently after ring 5");
      n_bad = n_bad + 1;
    end

    $display("--- Summary: %0d measurements, %0d timeouts, %0d failures, worst live error %0.4f %%",
             n_meas, n_timeouts, n_bad, worst_err_pct);
    $display("    CSV written to build/sweep.csv");
    if (n_bad == 0 && errors == 0) $display("RESULT: PASS");
    else                           $display("RESULT: FAIL (%0d bad)", n_bad + errors);
    $finish;
  end

endmodule
