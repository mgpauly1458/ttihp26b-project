// ============================================================================
// ring_model.v -- behavioural ring oscillator, the simulation ground truth
// ----------------------------------------------------------------------------
// What it does
//   Produces a clock whose frequency is a known function of an 8-bit code. We
//   choose the curve, so during simulation we always know the right answer and
//   can check the measurement chain against it.
//
// Clock domain
//   None. It IS a clock source. Non-synthesisable (uses real arithmetic and
//   delay control) and lives in sim/ so it can never reach a synthesis run.
//
// Interface (identical to every real ring in src/rings/)
//   code    [7:0]  trim code, interpreted through the curve below
//   enable         1 = oscillate, 0 = output held low
//   clk_out        the oscillator output
//
// The curve is deliberately unpleasant, because a straight line would let a
// broken measurement chain pass:
//   * dead zone   -- codes below DEAD_CODE do not oscillate at all
//   * offset      -- the first live code is F_MIN_HZ, not zero
//   * nonlinear   -- frequency rises with the SQUARE of the distance above the
//                    dead zone, so a one-code step near the top is far larger
//                    than a one-code step near the bottom
//
// Per-instance parameters let a population of rings with different
// characters be simulated from this one module.
//
// Assumptions
//   * A code change takes effect at the end of the half-period in progress.
//   * Dropping enable finishes the half-period in progress and then holds the
//     output low. Nothing downstream cares about that last edge.
//   * The half-period is rounded to the simulation precision (1 ps). At
//     400 MHz that is a 0.08 % error in the period; the testbenches allow
//     for it.
// ============================================================================
`timescale 1ns / 1ps

module ring_model #(
    // ----------------------- curve parameters: edit these and re-run --------
    parameter real    F_MIN_HZ  = 20.0e6,   // frequency at the first live code
    parameter real    F_MAX_HZ  = 400.0e6,  // frequency at code 255
    parameter integer DEAD_CODE = 20        // codes below this do not oscillate
    // ------------------------------------------------------------------------
) (
    input  wire [7:0] code,
    input  wire       enable,
    output reg        clk_out
);

  // Frequency for a given code. Returns 0.0 in the dead zone. The testbenches
  // call this through the hierarchy to get the exact expected answer.
  function real freq_of_code;
    input [7:0] c;
    real x;
    begin
      if (c < DEAD_CODE) begin
        freq_of_code = 0.0;
      end else begin
        // x runs 0.0 at the first live code to 1.0 at code 255
        x = (c - DEAD_CODE) / (255.0 - DEAD_CODE);
        freq_of_code = F_MIN_HZ + (F_MAX_HZ - F_MIN_HZ) * x * x;
      end
    end
  endfunction

  // Visible in the waveform viewer. Updated on every code change.
  real freq_hz;
  always @(code) freq_hz = freq_of_code(code);

  // The oscillator. Each half-period is looked up afresh, so a code change is
  // honoured at the next edge without any special handling.
  real half_period_ns;
  initial clk_out = 1'b0;
  always begin
    if (enable === 1'b1 && code >= DEAD_CODE) begin
      half_period_ns = 0.5e9 / freq_of_code(code);
      #(half_period_ns) clk_out = ~clk_out;
    end else begin
      clk_out = 1'b0;
      @(enable or code);
    end
  end

endmodule
