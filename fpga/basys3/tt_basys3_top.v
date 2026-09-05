/*
 * Basys3 prototype wrapper for a Tiny Tapeout project.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Board mapping
 * -------------
 *   sw[7:0]    -> ui_in[7:0]        dedicated inputs
 *   sw[15:8]   -> uio_in[7:0]       bidir pins, used only where uio_oe == 0
 *   led[7:0]   <- uo_out[7:0]       dedicated outputs
 *   led[15:8]  <- uio_out & uio_oe  bidir pins, driven bits only
 *   btnC       -> reset (rst_n = ~btnC)
 *   btnU       -> manual clock step, active while btnD is held
 *   btnD       -> hold for single-step mode, release for free-running
 *   7-seg      <- {uo_out, uio_out} as four hex digits
 *
 * The design under test runs on clk_user, a 2**CLK_DIV_LOG2 division of the
 * board's 100 MHz oscillator. build.tcl emits a matching create_generated_clock,
 * so keep the two in sync by changing CLK_DIV_LOG2 in build.tcl only.
 */

`default_nettype none

module tt_basys3_top #(
    // 100 MHz >> CLK_DIV_LOG2. 24 gives ~6 Hz, slow enough to watch on the LEDs.
    // Set to 0 to run the design at the full 100 MHz.
    parameter integer CLK_DIV_LOG2 = 24
) (
    input  wire        clk,
    input  wire [15:0] sw,
    output wire [15:0] led,
    input  wire        btnC,
    input  wire        btnU,
    input  wire        btnD,
    input  wire        btnL,
    input  wire        btnR,
    output wire [6:0]  seg,
    output wire        dp,
    output wire [3:0]  an
);

  // ---------------------------------------------------------------- reset
  // btnC is active high on the board; the design wants an active-low reset.
  // Synchronise the release so the design leaves reset cleanly.
  reg [2:0] rst_sync = 3'b000;
  always @(posedge clk) rst_sync <= {rst_sync[1:0], ~btnC};
  wire rst_n = rst_sync[2];

  // ------------------------------------------------------- clock generation
  wire clk_slow;

  generate
    if (CLK_DIV_LOG2 == 0) begin : g_no_div
      assign clk_slow = clk;
    end else begin : g_div
      reg [CLK_DIV_LOG2-1:0] div = {CLK_DIV_LOG2{1'b0}};
      always @(posedge clk) div <= div + 1'b1;
      assign clk_slow = div[CLK_DIV_LOG2-1];
    end
  endgenerate

  // Debounce btnU into a level that toggles once per press, for single-stepping.
  // 100 MHz / 2**20 ~= 95 Hz sampling, well past contact bounce.
  reg [19:0] db_cnt   = 20'd0;
  reg        btnU_s   = 1'b0;
  reg        step_clk = 1'b0;
  always @(posedge clk) begin
    db_cnt <= db_cnt + 1'b1;
    if (&db_cnt) begin
      btnU_s <= btnU;
      // Rising edge of the debounced button toggles the manual clock.
      if (btnU && !btnU_s) step_clk <= ~step_clk;
    end
  end

  // Hold btnD to take the design off the free-running clock and step it by hand.
  // Switching sources can clip a cycle; assert reset (btnC) after changing mode.
  wire clk_raw = btnD ? step_clk : clk_slow;

  wire clk_user;
  BUFG bufg_user (.I(clk_raw), .O(clk_user));

  // ------------------------------------------------------- design under test
  wire [7:0] uo_out, uio_out, uio_oe;
  wire [7:0] ui_in  = sw[7:0];
  wire [7:0] uio_in = sw[15:8];

  tt_um_example dut (
      .ui_in   (ui_in),
      .uo_out  (uo_out),
      .uio_in  (uio_in),
      .uio_out (uio_out),
      .uio_oe  (uio_oe),
      .ena     (1'b1),
      .clk     (clk_user),
      .rst_n   (rst_n)
  );

  // Show a bidir pin only when the design is actually driving it.
  assign led = {uio_out & uio_oe, uo_out};

  // ------------------------------------------------------------- 7-segment
  // Four hex digits: uio_out[7:4] uio_out[3:0] uo_out[7:4] uo_out[3:0]
  seven_seg_hex display (
      .clk    (clk),
      .value  ({uio_out, uo_out}),
      .seg    (seg),
      .dp     (dp),
      .an     (an)
  );

  // btnL and btnR are constrained but unused; tie them off to silence warnings.
  wire _unused = &{btnL, btnR, 1'b0};

endmodule


/* Time-multiplexed 4-digit hex readout for the Basys3 display.
 * Segments and anodes are active low on this board. */
module seven_seg_hex (
    input  wire        clk,          // 100 MHz
    input  wire [15:0] value,
    output reg  [6:0]  seg,
    output wire        dp,
    output reg  [3:0]  an
);

  assign dp = 1'b1;  // decimal point off

  // ~1.5 kHz per digit refresh, above the flicker threshold.
  reg [15:0] refresh = 16'd0;
  always @(posedge clk) refresh <= refresh + 1'b1;
  wire [1:0] digit = refresh[15:14];

  reg [3:0] nibble;
  always @(*) begin
    case (digit)
      2'd0: begin an = 4'b1110; nibble = value[3:0];   end
      2'd1: begin an = 4'b1101; nibble = value[7:4];   end
      2'd2: begin an = 4'b1011; nibble = value[11:8];  end
      default: begin an = 4'b0111; nibble = value[15:12]; end
    endcase
  end

  // seg[6:0] = {g,f,e,d,c,b,a}, active low.
  always @(*) begin
    case (nibble)
      4'h0: seg = 7'b1000000;  4'h1: seg = 7'b1111001;
      4'h2: seg = 7'b0100100;  4'h3: seg = 7'b0110000;
      4'h4: seg = 7'b0011001;  4'h5: seg = 7'b0010010;
      4'h6: seg = 7'b0000010;  4'h7: seg = 7'b1111000;
      4'h8: seg = 7'b0000000;  4'h9: seg = 7'b0010000;
      4'ha: seg = 7'b0001000;  4'hb: seg = 7'b0000011;
      4'hc: seg = 7'b1000110;  4'hd: seg = 7'b0100001;
      4'he: seg = 7'b0000110;  default: seg = 7'b0001110;
    endcase
  end

endmodule
