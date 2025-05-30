/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_uwasic_onboarding_matthew_chen(

    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n    // reset_n - low to reset
    //input  wire [1:0] test_mode // debugger. unsupported by make. moved to ui_in[4:3]
);

// always@(*) begin
//   case(addr_out)
//     7'd0: uo_out <= en_reg_out_7_0;
//     7'd1: uo_out <= en_reg_out_15_8;
//     7'd2: uo_out <= en_reg_pwm_7_0;
//     7'd3: uo_out <= en_reg_pwm_15_8;
//     7'd4: uo_out <= pwm_duty_cycle;
//     default: uo_out <= 8'b0;
//   endcase
// end

  wire [15:0] out;
  
  assign uo_out  = out[7:0];
  assign uio_out = out[15:8];
  assign uio_oe  = 0;

    // Create wires to connect to the values of the registers
  wire [7:0] en_reg_out_7_0;
  wire [7:0] en_reg_out_15_8;
  wire [7:0] en_reg_pwm_7_0;
  wire [7:0] en_reg_pwm_15_8;
  wire [7:0] pwm_duty_cycle;

  pwm_peripheral pwm_peripheral_inst (
      .clk(clk),
      .rst_n(rst_n),
      .en_reg_out_7_0(en_reg_out_7_0),
      .en_reg_out_15_8(en_reg_out_15_8),
      .en_reg_pwm_7_0(en_reg_pwm_7_0),
      .en_reg_pwm_15_8(en_reg_pwm_15_8),
      .pwm_duty_cycle(pwm_duty_cycle),
      //.out()
      .out(out) //[15:8] to uio, [7:0] to uo
    );
    // Add uio_in and ui_in[7:5] to the list of unused signals:
    wire _unused = &{ena, ui_in[7:3], uio_oe, uio_in, 1'b0};

   spi_peripheral spi_peripheral_inst (
      .SCLK(ui_in[0]),
      .COPI(ui_in[1]),
      .nCS(ui_in[2]),
      .clk(clk),
      .rst_n(rst_n),

      .en_reg_out_7_0(en_reg_out_7_0),
      .en_reg_out_15_8(en_reg_out_15_8),
      .en_reg_pwm_7_0(en_reg_pwm_7_0),
      .en_reg_pwm_15_8(en_reg_pwm_15_8),
      .pwm_duty_cycle(pwm_duty_cycle)
    );

endmodule
