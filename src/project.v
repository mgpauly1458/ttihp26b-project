// project.v -- Tiny Tapeout top: on-chip ring oscillator frequency meter
//   ring_bank (8 rings) -> ring_mux -> ring_divider (/1../128) -> measure_core -> regfile -> pins
//   f_ring = TARGET_N * 2^TAP_SEL * f_ref / RESULT    f_ref = the clk pin, the only thing that must be accurate
// Pins  ui_in  = {spare, RSEL[2:0], WE, ADDR[2:0]}   uo_out = read byte      (docs/pinmap.md)
//       uio_in = write data                          uio_out = uio_oe = 0
// Clock domains: clk (regfile, measure_core FSM and counters); the selected ring and the divider taps
//   (ring_divider, measure_core window logic). Crossings are single bits through cdc_sync (docs/constraints.md).
// - rst_n is used synchronously by the clk domain and asynchronously by the divider, whose clock may be stopped.
// - ena is the master ring enable: 1 only while this design is selected, so the rings are off for neighbours.
`default_nettype none

module tt_um_mgpauly1458_ringmeter (
    input  wire [7:0] ui_in,    // dedicated inputs
    output wire [7:0] uo_out,   // dedicated outputs
    input  wire [7:0] uio_in,   // IOs: input path
    output wire [7:0] uio_out,  // IOs: output path
    output wire [7:0] uio_oe,   // IOs: enable path (active high: 0=input, 1=output)
    input  wire       ena,      // 1 while this design is selected; master ring enable here
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // Synchronous in the clk domain, asynchronous in the divider (its clock may be stopped): intended.
  /* verilator lint_off SYNCASYNCNET */
  wire reset = ~rst_n;
  /* verilator lint_on SYNCASYNCNET */

  // ---- register file --------------------------------------------------------
  wire [7:0]  trim_code;
  wire [2:0]  ring_sel;
  wire [2:0]  tap_sel;
  wire [15:0] target_n;
  wire [15:0] timeout;
  wire        start;
  wire [31:0] ref_count;
  wire        done, busy, timeout_error;

  regfile u_regs (
      .clk           (clk),
      .reset         (reset),
      .ui_in         (ui_in),
      .uio_in        (uio_in),
      .uo_out        (uo_out),
      .trim_code     (trim_code),
      .ring_sel      (ring_sel),
      .tap_sel       (tap_sel),
      .target_n      (target_n),
      .timeout       (timeout),
      .start         (start),
      .ref_count     (ref_count),
      .done          (done),
      .busy          (busy),
      .timeout_error (timeout_error)
  );

  // ---- the rings ------------------------------------------------------------
  wire [7:0] ring_en;
  wire [7:0] ring_clk;

  ring_bank u_rings (
      .trim_code (trim_code),
      .ring_en   (ring_en),
      .ring_clk  (ring_clk)
  );

  // ---- select one, divide it, measure it -------------------------------------
  wire ring_sel_clk;
  wire divided_ring;

  ring_mux u_mux (
      .ring_in  (ring_clk),
      .sel      (ring_sel),
      .enable   (ena),
      .ring_out (ring_sel_clk),
      .ring_en  (ring_en)
  );

  ring_divider u_div (
      .ring_clk    (ring_sel_clk),
      .reset       (reset),
      .tap_sel     (tap_sel),
      .divided_clk (divided_ring)
  );

  measure_core u_core (
      .ref_clk       (clk),
      .reset         (reset),
      .divided_ring  (divided_ring),
      .start         (start),
      .target_n      (target_n),
      .timeout       (timeout),
      .ref_count     (ref_count),
      .done          (done),
      .busy          (busy),
      .timeout_error (timeout_error)
  );

  // Bidirectionals are all inputs (write data).
  assign uio_out = 8'b0;
  assign uio_oe  = 8'b0;

endmodule

`default_nettype wire
