// tb_pins.vh -- host-side helpers for the pin-level testbenches (tb_top, tb_sweep)
// Include inside a module that declares clk, ui_in, uio_in, uo_out and `integer errors`. Provides the
// register-map localparams, host_write / host_read with the waits regfile.v mandates, wait_done,
// read_result, and measure(ring, code, tap, n, tmo), which leaves `result` and `status` set.

  // Write map
  localparam [2:0] A_TRIM     = 3'd0,
                   A_RING_SEL = 3'd1,
                   A_TAP_SEL  = 3'd2,
                   A_TARGET_L = 3'd3,
                   A_TARGET_H = 3'd4,
                   A_TIMEOUT_L= 3'd5,
                   A_TIMEOUT_H= 3'd6,
                   A_CONTROL  = 3'd7;
  // Read map
  localparam [2:0] R_STATUS   = 3'd0,
                   R_RESULT0  = 3'd1,
                   R_RESULT1  = 3'd2,
                   R_RESULT2  = 3'd3,
                   R_RESULT3  = 3'd4,
                   R_TRIM     = 3'd5,
                   R_SEL      = 3'd6,
                   R_ID       = 3'd7;
  // STATUS bits
  localparam ST_DONE = 0, ST_BUSY = 1, ST_TIMEOUT = 2, ST_IGNORED = 3;

  reg [2:0] pin_addr = 3'd0;
  reg       pin_we   = 1'b0;
  reg [2:0] pin_rsel = 3'd0;

  always @(*) ui_in = {1'b0, pin_rsel, pin_we, pin_addr};

  // Host write: ADDR/WDATA, WE high 4 clocks, WE low 4.
  task host_write;
    input [2:0] a;
    input [7:0] d;
    begin
      @(posedge clk); #1;
      pin_addr = a; uio_in = d;
      pin_we = 1'b1;
      repeat (4) @(posedge clk); #1;
      pin_we = 1'b0;
      repeat (4) @(posedge clk); #1;
    end
  endtask

  // Host read: RSEL, wait 3 clocks, sample uo_out.
  reg [7:0] rdata;
  task host_read;
    input [2:0] r;
    begin
      @(posedge clk); #1;
      pin_rsel = r;
      repeat (3) @(posedge clk); #1;
      rdata = uo_out;
    end
  endtask

  // Poll STATUS until done; bounded so a hang fails instead of looping.
  integer polls;
  task wait_done;
    begin
      polls = 0;
      host_read(R_STATUS);
      while (!rdata[ST_DONE] && polls < 100000) begin
        host_read(R_STATUS);
        polls = polls + 1;
      end
      if (!rdata[ST_DONE]) begin
        $display("FAIL: measurement never finished");
        errors = errors + 1;
      end
    end
  endtask

  // RESULT from its four bytes.
  reg [31:0] result;
  task read_result;
    begin
      host_read(R_RESULT0); result[7:0]   = rdata;
      host_read(R_RESULT1); result[15:8]  = rdata;
      host_read(R_RESULT2); result[23:16] = rdata;
      host_read(R_RESULT3); result[31:24] = rdata;
    end
  endtask

  // Configure, start, wait, collect: leaves `result` and `status`.
  reg [7:0] status;
  task measure;
    input [2:0]  ring;
    input [7:0]  code;
    input [2:0]  tap;
    input [15:0] n;
    input [15:0] tmo;
    begin
      host_write(A_RING_SEL,  {5'b0, ring});
      host_write(A_TAP_SEL,   {5'b0, tap});
      host_write(A_TRIM,      code);
      host_write(A_TARGET_L,  n[7:0]);
      host_write(A_TARGET_H,  n[15:8]);
      host_write(A_TIMEOUT_L, tmo[7:0]);
      host_write(A_TIMEOUT_H, tmo[15:8]);
      host_write(A_CONTROL,   8'h01);
      wait_done;
      status = rdata;
      read_result;
    end
  endtask
