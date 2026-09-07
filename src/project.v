// ============================================================================
// project.v -- Tiny Tapeout top level: on-chip ring oscillator frequency meter
// ----------------------------------------------------------------------------
// What it is
//   A small all-digital instrument that measures how fast a ring oscillator
//   runs and reports the result as a number over a handful of pins. Eight
//   ring slots share one measurement chain, so any difference between two
//   rings is a real difference and not an instrument difference.
//
//        ring_bank (8 rings) --> ring_mux --> ring_divider --> measure_core
//             ^ TRIM_CODE broadcast        (/1../128)      (reciprocal counter)
//                                                                 |
//        pins <------------------------ regfile <-----------------+
//
//   Reciprocal method: count reference-clock cycles over exactly TARGET_N
//   periods of the divided ring. Then
//
//       f_ring = TARGET_N * 2^TAP_SEL * f_ref / RESULT
//
//   f_ref is the clk pin -- the only thing that has to be accurate, and it
//   comes from the bench. No voltage reference or analog rail anywhere.
//
// Clock domains
//   Reference (clk): regfile, measure_core's FSM and counters.
//   Ring (whichever ring is selected, and the divider taps): ring_divider
//   and the window logic in measure_core. Crossings are single bits through
//   cdc_sync. See docs/constraints.md for what STA will need to be told.
//
// Reset
//   rst_n is the tile's reset. Reference-domain logic uses it synchronously
//   (as active-high `reset`); the divider uses it asynchronously because
//   its clock may not be running. Both are explained in their files.
//
// ena
//   Used as the master ring enable. It is 1 whenever this design is the one
//   selected on the shuttle, so the rings are off while some other project
//   is running -- which is what a neighbour would want from us.
//
// Pin summary (docs/pinmap.md has the full story)
//   ui_in  = {spare, RSEL[2:0], WE, ADDR[2:0]}    uo_out = read data
//   uio_in = write data (all inputs)              uio_out/uio_oe = 0
// ============================================================================
`default_nettype none

module tt_um_mgpauly1458_ringmeter (
    input  wire [7:0] ui_in,    // dedicated inputs
    output wire [7:0] uo_out,   // dedicated outputs
    input  wire [7:0] uio_in,   // IOs: input path
    output wire [7:0] uio_out,  // IOs: output path
    output wire [7:0] uio_oe,   // IOs: enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // Used synchronously by the reference domain and asynchronously by the
  // divider, whose clock may not be running: intended, see the header.
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
