/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_uwasic_onboarding_matthew_chen(

    input  wire [7:0] ui_in,    // Dedicated inputs
    output reg [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n    // reset_n - low to reset
    //input  wire [1:0] test_mode // debugger. unsupported by make. moved to ui_in[4:3]
);

  assign uio_oe = 8'hFF;

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

  wire [7:0] pwm_uo_out;
  
  always@(posedge clk) begin
    case(ui_in[4:3]) 
      2'd1: begin
        case(addr_out)
          0: uo_out = en_reg_out_7_0;
          1: uo_out = en_reg_out_15_8;
          2: uo_out = en_reg_pwm_7_0;
          3: uo_out = en_reg_pwm_15_8;
          4: uo_out = pwm_duty_cycle;
          default: uo_out = 8'b0;
        endcase
      end
      2'd2: uo_out = pwm_uo_out;
      2'd3: uo_out = pwm_uo_out;
      default: uo_out = 8'b0;
    endcase
  end

    // Create wires to refer to the values of the registers
  wire [7:0] en_reg_out_7_0;
  wire [7:0] en_reg_out_15_8;
  wire [7:0] en_reg_pwm_7_0;
  wire [7:0] en_reg_pwm_15_8;
  wire [7:0] pwm_duty_cycle;
  reg [2:0] addr_out;

  pwm_peripheral pwm_peripheral_inst (
      .clk(clk),
      .rst_n(rst_n),
      .en_reg_out_7_0(en_reg_out_7_0),
      .en_reg_out_15_8(en_reg_out_15_8),
      .en_reg_pwm_7_0(en_reg_pwm_7_0),
      .en_reg_pwm_15_8(en_reg_pwm_15_8),
      .pwm_duty_cycle(pwm_duty_cycle),
      //.out()
      .out({uio_out, pwm_uo_out}) //[15:8] to uio, [7:0] to uo
    );
    // Add uio_in and ui_in[7:5] to the list of unused signals:
    wire _unused = &{ena, ui_in[7:5], uio_in, 1'b0};

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
      .pwm_duty_cycle(pwm_duty_cycle),
      .addr_out(addr_out)
    );

endmodule
