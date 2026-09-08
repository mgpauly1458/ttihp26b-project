// ring_model.v -- behavioural ring oscillator, the simulation ground truth (not synthesisable, lives in sim/)
//   F_MIN_HZ    frequency at the first live code       F_MAX_HZ   frequency at code 255
//   DEAD_CODE   codes below this do not oscillate
//   code [7:0]  trim code     enable  1 = oscillate, 0 = output held low     clk_out  the clock
// Curve: f = F_MIN + (F_MAX - F_MIN) * x^2, x = (code - DEAD_CODE) / (255 - DEAD_CODE); 0 below DEAD_CODE.
//   Dead zone, offset and nonlinearity are deliberate: a straight line would let a broken chain pass.
// - Testbenches call freq_of_code through the hierarchy for the exact expected answer.
// - A code change takes effect at the end of the half-period in progress; dropping enable finishes the
//   half-period, then holds low.
// - Each half-period rounds to 1 ps: 0.08 % of the period at 400 MHz, which the testbenches allow for.
`timescale 1ns / 1ps

module ring_model #(
    parameter real    F_MIN_HZ  = 20.0e6,   // frequency at the first live code
    parameter real    F_MAX_HZ  = 400.0e6,  // frequency at code 255
    parameter integer DEAD_CODE = 20        // codes below this do not oscillate
) (
    input  wire [7:0] code,
    input  wire       enable,
    output reg        clk_out
);

  // Frequency for a code; 0.0 in the dead zone.
  function real freq_of_code;
    input [7:0] c;
    real x;
    begin
      if (c < DEAD_CODE) begin
        freq_of_code = 0.0;
      end else begin
        // x: 0.0 at the first live code, 1.0 at code 255
        x = (c - DEAD_CODE) / (255.0 - DEAD_CODE);
        freq_of_code = F_MIN_HZ + (F_MAX_HZ - F_MIN_HZ) * x * x;
      end
    end
  endfunction

  // Waveform-viewer aid.
  real freq_hz;
  always @(code) freq_hz = freq_of_code(code);

  // Half-period looked up afresh every edge, so a code change needs no special handling.
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
