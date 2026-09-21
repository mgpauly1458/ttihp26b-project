// stats_observer.v -- running statistics of RESULT, plus a dice byte (clk domain; drives nothing in the instrument)
//   clk, reset        tile clk and its synchronous active-high reset
//   done, timeout_error, ref_count   straight from measure_core; sampled the cycle done rises (as regfile's shadow)
//   clear             one-cycle pulse from regfile: an accepted write to a configuration register (ADDR 0..6)
//   index [4:0]       which byte to show; raw pins, the same "set, wait >= 3 clk, read" rule as RSEL
//   stats_byte [7:0]  combinational; regfile registers it onto uo_out while ui_in[7] = 1
// Index  0/1 COUNT   2/3 MIN   4/5 MAX   6..9 SUM   10 DICE   11 0x5A   12..25 "RING METER 26B"   26..31 zero
//   All little-endian. Everything covers "every good measurement since the last configuration write".
//   average RESULT = SUM / COUNT (the +/-1 count error averages down ~sqrt(COUNT)); MAX - MIN = peak-to-peak spread.
// - 16 bits are enough: measure_core's 16-bit timeout counter runs through the whole measurement, so a RESULT
//   that did not time out is below 65536. One that is not (it cannot happen) is skipped rather than truncated.
// - A timed-out measurement is not a sample: its ref_count is not a result.
// - COUNT saturates at 65535 and every statistic freezes with it, so SUM / COUNT stays true. 65535 * 65535 < 2^32.
// - A sample and a clear cannot coincide: regfile ignores writes while busy, and done rises while busy.
// - DICE: free-running 8-bit LFSR (x^8+x^6+x^5+x^4+1); each sample's RESULT bit 0 (ring jitter) is folded in.
//   A plain LFSR locks up at 0 and a folded-in bit can put it there, hence the reload.
`default_nettype none

module stats_observer (
    input  wire        clk,
    input  wire        reset,
    input  wire        done,
    input  wire        timeout_error,
    input  wire [31:0] ref_count,
    input  wire        clear,
    input  wire [4:0]  index,
    output reg  [7:0]  stats_byte
);

  // ---- when is there a new sample ---------------------------------------------
  reg [15:0] count;
  reg        done_q;
  wire       fits   = (ref_count[31:16] == 16'd0);
  wire       sample = done & ~done_q & ~timeout_error & fits & (count != 16'hFFFF);

  wire [15:0] value = ref_count[15:0];

  // ---- statistics -------------------------------------------------------------
  reg [15:0] min;
  reg [15:0] max;
  reg [31:0] sum;

  always @(posedge clk) begin
    if (reset) begin
      done_q <= 1'b0;
      count  <= 16'd0;
      min    <= 16'hFFFF;
      max    <= 16'd0;
      sum    <= 32'd0;
    end else begin
      done_q <= done;

      if (clear) begin
        count <= 16'd0;
        min   <= 16'hFFFF;
        max   <= 16'd0;
        sum   <= 32'd0;
      end else if (sample) begin
        count <= count + 16'd1;
        if (value < min) min <= value;
        if (value > max) max <= value;
        sum   <= sum + {16'd0, value};
      end
    end
  end

  // ---- dice ---------------------------------------------------------------------
  reg  [7:0] lfsr;
  wire       feedback = lfsr[7] ^ lfsr[5] ^ lfsr[4] ^ lfsr[3] ^ (sample & value[0]);

  always @(posedge clk) begin
    if (reset)
      lfsr <= 8'h01;
    else if (lfsr == 8'h00)
      lfsr <= 8'h01;
    else
      lfsr <= {lfsr[6:0], feedback};
  end

  // ---- byte select --------------------------------------------------------------
  always @(*) begin
    case (index)
      5'd0:    stats_byte = count[7:0];
      5'd1:    stats_byte = count[15:8];
      5'd2:    stats_byte = min[7:0];
      5'd3:    stats_byte = min[15:8];
      5'd4:    stats_byte = max[7:0];
      5'd5:    stats_byte = max[15:8];
      5'd6:    stats_byte = sum[7:0];
      5'd7:    stats_byte = sum[15:8];
      5'd8:    stats_byte = sum[23:16];
      5'd9:    stats_byte = sum[31:24];
      5'd10:   stats_byte = lfsr;
      5'd11:   stats_byte = 8'h5A;
      5'd12:   stats_byte = "R";
      5'd13:   stats_byte = "I";
      5'd14:   stats_byte = "N";
      5'd15:   stats_byte = "G";
      5'd16:   stats_byte = " ";
      5'd17:   stats_byte = "M";
      5'd18:   stats_byte = "E";
      5'd19:   stats_byte = "T";
      5'd20:   stats_byte = "E";
      5'd21:   stats_byte = "R";
      5'd22:   stats_byte = " ";
      5'd23:   stats_byte = "2";
      5'd24:   stats_byte = "6";
      5'd25:   stats_byte = "B";
      default: stats_byte = 8'h00;
    endcase
  end

endmodule

`default_nettype wire
