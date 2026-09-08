// regfile.v -- register file and pin interface (clk domain; every input pin is asynchronous to clk)
// Pins   ui_in[2:0] ADDR   ui_in[3] WE (rising edge = one write)   ui_in[6:4] RSEL   ui_in[7] spare
//        uio_in[7:0] WDATA (all bidirectionals are inputs)          uo_out[7:0] byte selected by RSEL, registered
// Write (ADDR)                                   Read (RSEL)
//   0 TRIM_CODE[7:0]   1 RING_SEL[2:0]             0 STATUS = {4'b0, write_ignored, timeout_error, busy, done}
//   2 TAP_SEL[2:0]     3/4 TARGET_N lo/hi byte     1/2/3/4 RESULT[7:0] / [15:8] / [23:16] / [31:24]
//   5/6 TIMEOUT lo/hi  7 CONTROL bit 0 = START     5 TRIM_CODE   6 {2'b0, TAP_SEL, RING_SEL}   7 ID = 0xA5
// Write: set ADDR/WDATA, WE high >= 4 clk, WE low >= 4 clk before changing them. WE is synchronised and edge-detected
//   2-3 clk after the host raised it, so ADDR/WDATA have been stable that long: the only reason sampling them raw is safe.
// Read: set RSEL, wait >= 3 clk, read uo_out (RSEL is unsynchronised; a byte read while it changes may be wrong).
// Reset: TRIM 0, RING_SEL 0, TAP_SEL 0, TARGET_N 256, TIMEOUT 65535, so a bare START gives a finite measurement.
// - While busy every write, START included, is ignored and sets STATUS.write_ignored until the next accepted START:
//   RING_SEL/TAP_SEL would glitch the clock muxes, TRIM_CODE the ring, TARGET_N crosses to the ring domain unsynchronised.
// - RESULT is a shadow latched when done rises, so a measurement starting between two byte reads cannot mix results.
// - START is a self-clearing one-cycle pulse. Pin reasoning: docs/pinmap.md.
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

  // ---- write strobe: synchronise, then rising edge --------------------------
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
      start     <= 1'b0;                 // self-clearing pulse

      if (write_now) begin
        if (busy) begin
          // all writes blocked while measuring
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
                write_ignored <= 1'b0;   // an accepted START clears the flag
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
