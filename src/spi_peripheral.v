module spi_peripheral#(
    parameter MAX_ADDR = 4
)
(
    input wire       SCLK,// clock
    input wire       COPI,//in from controller
    input wire       nCS,//start transaction on negedge
    input wire       clk,//
    input wire       rst_n,//

    output wire en_reg_out_7_0,
    output wire en_reg_out_15_8, 
    output wire en_reg_pwm_7_0,
    output wire en_reg_pwm_15_8,
    output wire pwm_duty_cycle 
);

reg SCLK_FF1out;
reg SCLK_FF2out;
reg SCLK_postFF;

reg COPI_FF1out;
reg COPI_postFF;

reg nCS_FF1out;
reg nCS_postFF;

reg [7:0] SPI_regs [0:MAX_ADDR]; // Array of 8-bit registers indexed from 0 to MAX_ADDR
reg [15:0] transaction_dat;
reg [3:0] transaction_curr_bit; //from the serial in: what is the current bit?

reg transaction_posedge;

//Flags
reg transaction_ready; //nCS deasserted
reg transaction_processed; //correct data already written to registers, can discard current transaction

//DFF syncs
always@(posedge clk) begin //SCLK FF sync and edge detection
    //double ff sync the lower freq sig to the higher freq sig
    SCLK_FF1out <= SCLK;
    SCLK_FF2out <= SCLK_FF1out;
    if(SCLK_FF2out == 1 && SCLK_FF1out == 0) begin //posedge det
        SCLK_postFF <= 1;
    end
    else if(SCLK_FF2out == 0 && SCLK_FF1out == 1) begin //negedge det
        SCLK_postFF <= 0;
    end
end

always@(posedge clk) begin //COPI/nCS sync with simple doubleflop
    COPI_FF1out <= COPI;
    COPI_postFF <= COPI_FF1out;

    nCS_FF1out <= nCS;
    nCS_postFF <= nCS_FF1out;
end

always@(negedge nCS_postFF) begin
    transaction_curr_bit <= 4'd0; //start writing from 0
end

always@(posedge nCS_postFF) begin
    transaction_posedge <= 1;
end

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin //not ready
        transaction_ready <= 1'b0;
    end
    else if (nCS_postFF == 1'b0) begin //transaction start. write to transaction one by one
        transaction_dat[transaction_curr_bit] = COPI_postFF;
        transaction_curr_bit = transaction_curr_bit + 1;
    end
    else begin 
        if(transaction_posedge) begin
            transaction_ready <= 1'b1;
        end
        //if transaction processed then the current data is not needed and can await the next transaction
        else if(transaction_processed) begin
            transaction_ready <= 1'b0;
        end
    end
    if(transaction_posedge == 1) begin //reset. The posedge detection should be a pulse only.
        transaction_posedge <= 0;
    end
end

// Update registers only after the complete transaction has finished and been validated
always @(posedge clk or negedge rst_n) begin
   
    reg [6:0] addr;
    
    if (!rst_n) begin
        transaction_processed <= 1'b0;
    end else if (transaction_ready && !transaction_processed) begin
        // Transaction is ready and not yet processed
        if(transaction_dat[15] == 0) begin
            //ignore read command
        end
        else begin
            addr = transaction_dat[14:8];
            if(addr > MAX_ADDR) begin
                //no action as address is out of range
            end
            else begin
                SPI_regs[addr][7:0] <= transaction_dat[7:0];
            end
        end
        // Set the processed flag
        transaction_processed <= 1'b1;
    end else if (!transaction_ready && transaction_processed) begin
        // Reset processed flag when ready flag is cleared
        transaction_processed <= 1'b0;
    end
end

//drive outputs on register update
assign en_reg_out_7_0 = SPI_regs[0][7:0];
assign en_reg_out_15_8 = SPI_regs[1][7:0];
assign en_reg_pwm_7_0 = SPI_regs[2][7:0];
assign en_reg_pwm_15_8 = SPI_regs[3][7:0];
assign pwm_duty_cycle = SPI_regs[4][7:0];

endmodule