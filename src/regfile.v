// ============================================================================
// regfile.v -- register file and pin interface
// ----------------------------------------------------------------------------
// What it does
//   Turns the Tiny Tapeout pins into a handful of registers the host writes
//   and reads: the trim code, which ring, which divider tap, how long to
//   measure, when to give up, a start bit, a status byte and the 32-bit
//   result. Statistically this is where the bugs live, so it is kept dull.
//
// Clock domain
//   Reference domain (clk). Every input pin is asynchronous to it -- the
//   host is a microcontroller -- and is treated accordingly (see Protocol).
//
// Pins (see docs/pinmap.md for the reasoning)
//   ui_in[2:0]   ADDR   write address
//   ui_in[3]     WE     write strobe, rising edge = one write
//   ui_in[6:4]   RSEL   which byte appears on uo_out
//   ui_in[7]     -      spare
//   uio_in[7:0]  WDATA  write data (all bidirectionals are inputs)
//   uo_out[7:0]  RDATA  the byte selected by RSEL, registered
//
// Write map (ADDR)                      Read map (RSEL)
//   0  TRIM_CODE  [7:0]                   0  STATUS  {4'b0, write_ignored,
//   1  RING_SEL   [2:0]                                timeout_error, busy, done}
//   2  TAP_SEL    [2:0]                   1  RESULT[7:0]
//   3  TARGET_N   [7:0]  low byte         2  RESULT[15:8]
//   4  TARGET_N   [15:8] high byte        3  RESULT[23:16]
//   5  TIMEOUT    [7:0]  low byte         4  RESULT[31:24]
//   6  TIMEOUT    [15:8] high byte        5  TRIM_CODE readback
//   7  CONTROL    bit 0 = START           6  {2'b0, TAP_SEL, RING_SEL} readback
//                                         7  ID = 0xA5, constant
//
// Protocol
//   Write: put ADDR and WDATA on the pins, then raise WE, hold everything
//   for at least 4 clk periods, then lower WE. Do not change ADDR or WDATA
//   until WE has been low for at least 4 clk periods. WE is passed through
//   a two-flop synchroniser and its rising edge is detected; ADDR and WDATA
//   are sampled on that detected edge, two to three clocks after the host
//   raised WE, by which time they have been stable for at least that long.
//   That is the only reason plain sampling of ADDR and WDATA is safe.
//   Read: put RSEL on the pins, wait at least 3 clk periods, read uo_out.
//   RSEL is sampled straight into the output register with no synchroniser;
//   a read taken while RSEL is changing may return one wrong byte, and the
//   wait is what avoids that. uo_out is registered so it never glitches.
//
// Rules enforced here
//   * While busy, writes to TRIM_CODE, RING_SEL, TAP_SEL, TARGET_N and
//     TIMEOUT are IGNORED, and so is START. Each of those would corrupt the
//     measurement in progress: RING_SEL and TAP_SEL glitch the clock muxes,
//     TRIM_CODE changes the ring mid-count, TARGET_N crosses into the ring
//     domain unsynchronised and is only safe because it is static.
//   * An ignored write sets STATUS.write_ignored, which stays set until the
//     next START is accepted. The flag costs one flop and turns "my sweep
//     script has a race" from a mystery into a status bit. Adopted.
//   * RESULT is latched into a shadow register the moment done rises and
//     the host reads the shadow. Without it, a new measurement starting
//     between two byte reads would hand back a mix of two results -- a bug
//     that appears rarely and looks like noise.
//   * START is self-clearing: it is a one-cycle pulse to the core, not a
//     stored bit.
//
// Reset values
//   TRIM_CODE 0, RING_SEL 0, TAP_SEL 0, TARGET_N 256, TIMEOUT 65535. The
//   host is expected to write all of them; the defaults just make a bare
//   START after reset produce a finite, sane measurement.
// ============================================================================
`default_nettype none

module regfile (
    input  wire        clk,
    input  wire        reset,

    // pins
    input  wire [7:0]  ui_in,
    input  wire [7:0]  uio_in,
    output reg  [7:0]  uo_out,

    // to the instrument
    output reg  [7:0]  trim_code,
    output reg  [2:0]  ring_sel,
    output reg  [2:0]  tap_sel,
    output reg  [15:0] target_n,
    output reg  [15:0] timeout,
    output reg         start,

    // from the instrument
    input  wire [31:0] ref_count,
    input  wire        done,
    input  wire        busy,
    input  wire        timeout_error
);

  localparam [7:0] ID = 8'hA5;

  // ---- pin decode -----------------------------------------------------------
  wire [2:0] addr  = ui_in[2:0];
  wire       we    = ui_in[3];
  wire [2:0] rsel  = ui_in[6:4];
  wire [7:0] wdata = uio_in;

  // ---- write strobe: synchronise, then detect the rising edge ---------------
  wire we_sync;
  reg  we_sync_q;

  cdc_sync u_sync_we (
      .clk   (clk),
      .reset (reset),
      .d     (we),
      .q     (we_sync)
  );

  wire write_now = we_sync & ~we_sync_q;

  // ---- registers --------------------------------------------------------------
  reg write_ignored;

  always @(posedge clk) begin
    if (reset) begin
      we_sync_q     <= 1'b0;
      trim_code     <= 8'd0;
      ring_sel      <= 3'd0;
      tap_sel       <= 3'd0;
      target_n      <= 16'd256;
      timeout       <= 16'hFFFF;
      start         <= 1'b0;
      write_ignored <= 1'b0;
    end else begin
      we_sync_q <= we_sync;
      start     <= 1'b0;                 // self-clearing: a pulse, not a bit

      if (write_now) begin
        if (busy) begin
          // Every register is off limits while measuring. See header.
          write_ignored <= 1'b1;
        end else begin
          case (addr)
            3'd0: trim_code       <= wdata;
            3'd1: ring_sel        <= wdata[2:0];
            3'd2: tap_sel         <= wdata[2:0];
            3'd3: target_n[7:0]   <= wdata;
            3'd4: target_n[15:8]  <= wdata;
            3'd5: timeout[7:0]    <= wdata;
            3'd6: timeout[15:8]   <= wdata;
            default: begin                 // 7: CONTROL
              if (wdata[0]) begin
                start         <= 1'b1;
                write_ignored <= 1'b0;   // a fresh measurement clears the flag
              end
            end
          endcase
        end
      end
    end
  end

  // ---- result shadow ----------------------------------------------------------
  reg [31:0] result;
  reg        done_q;

  always @(posedge clk) begin
    if (reset) begin
      result <= 32'd0;
      done_q <= 1'b0;
    end else begin
      done_q <= done;
      if (done & ~done_q)                // the cycle done rises
        result <= ref_count;
    end
  end

  // ---- read mux, registered onto the output pins ------------------------------
  always @(posedge clk) begin
    if (reset) begin
      uo_out <= 8'd0;
    end else begin
      case (rsel)
        3'd0:    uo_out <= {4'b0000, write_ignored, timeout_error, busy, done};
        3'd1:    uo_out <= result[7:0];
        3'd2:    uo_out <= result[15:8];
        3'd3:    uo_out <= result[23:16];
        3'd4:    uo_out <= result[31:24];
        3'd5:    uo_out <= trim_code;
        3'd6:    uo_out <= {2'b00, tap_sel, ring_sel};
        default: uo_out <= ID;
      endcase
    end
  end

  wire _unused = &{ui_in[7]};

endmodule

`default_nettype wire
