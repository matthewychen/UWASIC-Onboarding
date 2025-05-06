module spi_peripheral(
    input wire       SCLK,// clock
    input wire       COPI,//in from controller
    input wire       nCS,//start transaction on negedge
    input wire       clk,//
    input wire       rst_n//

);

reg SCLK_FF1out;
reg SCLK_FF2out;
reg SCLK_postFF;

reg COPI_FF1out;
reg COPI_postFF;

reg nCS_FF1out;
reg nCS_postFF;

reg [3:0] [7:0] SPI_regs; //4 addr/8 bit per addr
reg [16:0] transaction_dat;
reg [3:0] transaction_curr_bit; //from the serial in: what is the current bit?

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

always @(posedge clk or negedge nCS_postFF) begin
    if (!nCS_postFF) begin //not ready
        transaction_ready <= 1'b0;
    end
    else if (nCS_postFF == 1'b0) begin //transaction start
    end
    else begin 
     //need posedge detection for ncs, if posedge found then transaction has ended
     //
    end
end

// Update registers only after the complete transaction has finished and been validated
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        transaction_processed <= 1'b0;
    end else if (transaction_ready && !transaction_processed) begin
        // Transaction is ready and not yet processed
        // omitted code
        // Set the processed flag
        transaction_processed <= 1'b1;
    end else if (!transaction_ready && transaction_processed) begin
        // Reset processed flag when ready flag is cleared
        transaction_processed <= 1'b0;
    end
end
endmodule