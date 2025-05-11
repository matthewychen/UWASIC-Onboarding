`default_nettype none

module spi_peripheral #(parameter SYNC = 2)(
    //SPI inputs
    input wire nCS, 
    input wire SCLK, 
    input wire COPI,

    //sysclk input
    input wire clk,
    input wire rst_n,        //active LOW

    //outputs
    output reg [7:0] en_reg_out_7_0,
    output reg [7:0] en_reg_out_15_8,
    output reg [7:0] en_reg_pwm_7_0,
    output reg [7:0] en_reg_pwm_15_8,
    output reg [7:0] pwm_duty_cycle
);

//internal regs
reg [4:0] sCLKcnt;
reg [15:0] data;

reg [SYNC-1:0] sync_nCS;
reg [SYNC-1:0] sync_SCLK; 
reg [SYNC-1:0] sync_COPI;

//SPI DATA [15:0] IS [DATA 8 bit][ADDR 7 bit][R/W]
//note the ADDR is by default 0x00-0x04

//take in SPI data, 
always @(posedge clk or negedge rst_n) begin

    if (!rst_n) begin
        sCLKcnt <= 5'b0;
        data <= 16'b0;

        sync_nCS <= {SYNC{1'b0}};
        sync_SCLK <= {SYNC{1'b0}};
        sync_COPI <= {SYNC{1'b0}};

        en_reg_out_7_0 <= 8'b0;
        en_reg_out_15_8 <= 8'b0;
        en_reg_pwm_7_0 <= 8'b0;
        en_reg_pwm_15_8 <= 8'b0;
        pwm_duty_cycle <= 8'b0;
    end else begin
        
        sync_nCS <= {sync_nCS[SYNC-2:0], nCS};            //2'b10 is negedge
        sync_SCLK <= {sync_SCLK[SYNC-2:0], SCLK};         //note, 2'b00 is lo, 2'b01 is posedge, 2'b11 is high, 2'b10 is negedge
        sync_COPI <= {sync_COPI[SYNC-2:0], COPI};

        if (sync_nCS == 2'b10) begin
            sCLKcnt <= 5'b0;
            data <= 16'b0;

        end
        else if (sync_nCS == 2'b00 && sync_SCLK == 2'b01) begin
            if (sCLKcnt != 5'b10000) begin
                data[15 - sCLKcnt] <= sync_COPI[SYNC-1];
                sCLKcnt <= sCLKcnt + 1;
            end
        end

        if(sCLKcnt == 5'b10000 && data[15] == 1'b1)begin
            case (data[14:8]) 
                7'b0000000: en_reg_out_7_0 <= data[7:0];
                7'b0000001: en_reg_out_15_8 <= data[7:0];
                7'b0000010: en_reg_pwm_7_0 <= data[7:0];
                7'b0000011: en_reg_pwm_15_8 <= data[7:0];
                7'b0000100: pwm_duty_cycle <= data[7:0];
                default: ;
                //if address isnt one of them, just dont assign anything
            endcase
        end
    end
end

endmodule