# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import FallingEdge
from cocotb.triggers import ClockCycles
from cocotb.types import Logic
from cocotb.types import LogicArray

async def await_half_sclk(dut):
    """Wait for the SCLK signal to go high or low."""
    start_time = cocotb.utils.get_sim_time(units="ns")
    while True:
        await ClockCycles(dut.clk, 1)
        # Wait for half of the SCLK period (10 us)
        if (start_time + 100*100*0.5) < cocotb.utils.get_sim_time(units="ns"):
            break
    return

def ui_in_logicarray(ncs, bit, sclk):
    """Setup the ui_in value as a LogicArray."""
    return LogicArray(f"00000{ncs}{bit}{sclk}")


async def send_spi_transaction(dut, r_w, address, data):
    """
    Send an SPI transaction with format:
    - 1 bit for Read/Write
    - 7 bits for address
    - 8 bits for data
    
    Parameters:
    - r_w: boolean, True for write, False for read
    - address: int, 7-bit address (0-127)
    - data: LogicArray or int, 8-bit data
    """
    # Convert data to int if it's a LogicArray
    if isinstance(data, LogicArray):
        data_int = int(data)
    else:
        data_int = data
    # Validate inputs
    if address < 0 or address > 127:
        raise ValueError("Address must be 7-bit (0-127)")
    if data_int < 0 or data_int > 255:
        raise ValueError("Data must be 8-bit (0-255)")
    # Combine RW and address into first byte
    first_byte = (int(r_w) << 7) | address
    # Start transaction - pull CS low
    sclk = 0
    ncs = 0
    bit = 0
    # Set initial state with CS low
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 1)
    # Send first byte (RW + Address)
    for i in range(8):
        bit = (first_byte >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # Send second byte (Data)
    for i in range(8):
        bit = (data_int >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # End transaction - return CS high
    sclk = 0
    ncs = 1
    bit = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 600)
    return ui_in_logicarray(ncs, bit, sclk)

@cocotb.test()
async def test_spi(dut):
    dut._log.info("Start SPI test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    dut._log.info("Test project behavior")
    dut._log.info("Write transaction, address 0x00, data 0xF0")
    ui_in_val = await send_spi_transaction(dut, 1, 0x00, 0xF0)  # Write transaction
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000) 

    dut._log.info("Write transaction, address 0x01, data 0xCC")
    ui_in_val = await send_spi_transaction(dut, 1, 0x01, 0xCC)  # Write transaction
    assert dut.uo_out.value == 0xCC, f"Expected 0xCC, got {dut.uio_out.value}"
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x30 (invalid), data 0xAA")
    ui_in_val = await send_spi_transaction(dut, 1, 0x30, 0xAA)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Read transaction (invalid), address 0x30, data 0xBE")
    ui_in_val = await send_spi_transaction(dut, 0, 0x30, 0xBE)
    assert dut.uo_out.value == 0x00, f"Expected 0x00, got {dut.uo_out.value}"
    #if invalid, expect to read 0.
    await ClockCycles(dut.clk, 100)
    
    dut._log.info("Read transaction (invalid), address 0x41 (invalid), data 0xEF")
    ui_in_val = await send_spi_transaction(dut, 0, 0x41, 0xEF)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x02, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x02, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x04, data 0xCF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xCF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x00")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x00)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x01")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x01)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("SPI test completed successfully")

@cocotb.test()
async def test_pwm_freq(dut):
    #set registers appropriately
    #measure time delay between posedges to identify freq (1% error)
    #assert
    #note sclk period is 5100 ns and clk is 100 ns (10 MHz)
    
    dut._log.info("Start freq test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    
    desired_period = 333333.33 #ns
    time_elapsed = 0.0 #ns
    
    #begin write transactions
    
    #enable all inputs and outputs for output and PWM
    dut._log.info("Write transaction, address 0x00, data 0xFF - enable uo_out")
    ui_in_val = await send_spi_transaction(dut, 1, 0x00, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 1000) 
    
    dut._log.info("Write transaction, address 0x01, data 0xFF - enable uio_out")
    ui_in_val = await send_spi_transaction(dut, 1, 0x01, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 1000) 
    
    dut._log.info("Write transaction, address 0x02, data 0xFF - enable PWM on uo_out")
    ui_in_val = await send_spi_transaction(dut, 1, 0x02, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 1000) 
    
    dut._log.info("Write transaction, address 0x03, data 0xFF - enable PWM on uio_out")
    ui_in_val = await send_spi_transaction(dut, 1, 0x03, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 1000) 
    
    dut._log.info("Write transaction, address 0x04, data 50% - enable PWM on uio_out")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x7F)  # Write transaction
    await ClockCycles(dut.clk, 1000) 
     
    #all outputs set successfully
    #start sampling
    
    #start loop
    PWM_1ago = 0
    PWM_2ago = 0
    cycles = 0
    
    dut._log.info("beginning freq listen")
    # First while loop
    while True: 
        await ClockCycles(dut.clk, 1)
        PWM_2ago = PWM_1ago
        PWM_1ago = int(dut.uo_out[0].value)
        cycles = cycles + 1
        
        # Log only every 10 cycles
        if cycles % 250 == 0:
            dut._log.info(f"current cycle number: {cycles}")
            
        if cycles >= 10000:
            dut._log.error(f"Timeout reached after {cycles} cycles - no rising edge detected")
            break
    
        if(PWM_1ago == 1 and PWM_2ago == 0):
            #posedge detected
            start_time = cocotb.utils.get_sim_time(units="ns")
            dut._log.info("posedge detected")
            break
    
    cycles = 0
    
    # Second while loop 
    while True: 
        await ClockCycles(dut.clk, 1)
        PWM_2ago = PWM_1ago
        PWM_1ago = int(dut.uo_out[0].value)
        cycles = cycles + 1
        
        # Log only every 10 cycles
        if cycles % 250 == 0:
            dut._log.info(f"second posedge find. cycle num {cycles}")
            
        if cycles >= 100000:
            dut._log.error(f"Timeout reached after {cycles} cycles - no rising edge detected")
            break
        
        if(PWM_1ago == 1 and PWM_2ago == 0):
            #posedge detected
            period = cocotb.utils.get_sim_time(units="ns") - start_time
            break
    
    assert period >= (333333.33*0.99) and period <= (333333.33*1.01), f"Period not within specified range, got {period} ns."
            
    dut._log.info("PWM Frequency test completed successfully")

async def set_pwm(dut, duty_cycle):
    """initialize pwm by setting all registers to enable value.

    Args:
        duty_cycle (float): determine the duty cycle as a percentage.
    """
    assert duty_cycle <= 1 and duty_cycle >= 0, f"Your duty cycle percentage, {duty_cycle} exceeds 100% or is less than or equal to 0."
    duty_on_val = int(duty_cycle * 255)  # Calculate as integer
    dut._log.info(f"I I WILL WRITE {duty_on_val} TO REGISTER 4!!!!!!!!!!")
    
    dut._log.info("Write transaction, address 0x00, data 0xFF - enable uo_out")
    ui_in_val = await send_spi_transaction(dut, 1, 0x00, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 1000) 
    
    dut._log.info("Write transaction, address 0x01, data 0xFF - enable uio_out")
    ui_in_val = await send_spi_transaction(dut, 1, 0x01, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 1000) 
    
    dut._log.info("Write transaction, address 0x02, data 0xFF - enable PWM on uo_out")
    ui_in_val = await send_spi_transaction(dut, 1, 0x02, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 1000) 
    
    dut._log.info("Write transaction, address 0x03, data 0xFF - enable PWM on uio_out")
    ui_in_val = await send_spi_transaction(dut, 1, 0x03, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 1000) 
    
    dut._log.info(f"Write transaction, address 0x04, data {duty_cycle*100}% ({duty_on_val}/255) - enable PWM on uio_out")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, duty_on_val)  # Use integer value
    await ClockCycles(dut.clk, 1000) 
    
async def test_pwm(dut, duty_cycle):
    #start loop
    PWM_1ago = int(dut.uo_out[0].value)
    PWM_2ago = int(dut.uo_out[0].value)
    cycles = 0
    
    if duty_cycle == 0:
        dut._log.info("0 duty cycle. ignoring.")
        return
    
    assert duty_cycle <= 1 and duty_cycle > 0, f"Your duty cycle percentage, {duty_cycle} exceeds 100% or is less than or equal to 0%, which are invalid"
    
    if duty_cycle == 1:
        dut._log.info("Your desired duty cycle is 1. Listening to confirm there is no posedge within 100k cycles.")
        posedge_found = False
        while True: 
            await ClockCycles(dut.clk, 1)
            PWM_2ago = PWM_1ago
            PWM_1ago = int(dut.uo_out[0].value)
            cycles = cycles + 1
            
            # Log only every 10 cycles
            if cycles % 250 == 0:
                dut._log.info(f"first posedge find. current cycle number: {cycles}.  PWM2ago: {PWM_2ago}, PWM1ago: {PWM_1ago}")
                
            if cycles >= 100000:
                dut._log.error(f"Timeout reached after {cycles} cycles - no posedge detected")
                break
        
            if(PWM_1ago == 1 and PWM_2ago == 0):
                #posedge detected
                high_start_time = cocotb.utils.get_sim_time(units="ns")
                dut._log.info(f"posedge detected at time {high_start_time}. pwm of 100% failed.")
                posedge_found = True
                break
            
        assert posedge_found == False, "failed"
        
    else:
        dut._log.info("beginning freq listen for posedge")

        while True: 
            await ClockCycles(dut.clk, 1)
            PWM_2ago = PWM_1ago
            PWM_1ago = int(dut.uo_out[0].value)
            cycles = cycles + 1
            
            # Log only every 10 cycles
            if cycles % 250 == 0:
                dut._log.info(f"first posedge find. current cycle number: {cycles}.  PWM2ago: {PWM_2ago}, PWM1ago: {PWM_1ago}")
                
            if cycles >= 10000:
                dut._log.error(f"Timeout reached after {cycles} cycles - no posedge detected.")
                break
        
            if(PWM_1ago == 1 and PWM_2ago == 0):
                #posedge detected
                high_start_time = cocotb.utils.get_sim_time(units="ns")
                dut._log.info("posedge detected")
                break
        
        cycles = 0
        
        while True: 
            await ClockCycles(dut.clk, 1)
            PWM_2ago = PWM_1ago
            PWM_1ago = int(dut.uo_out[0].value)
            cycles = cycles + 1
            
            # Log only every 10 cycles
            if cycles % 250 == 0:
                dut._log.info(f"negedge find. cycle num {cycles}")
                
            if cycles >= 100000:
                dut._log.error(f"Timeout reached after {cycles} cycles - no negedge detected")
                break
            
            if(PWM_1ago == 0 and PWM_2ago == 1):
                #posedge detected
                dut._log.info("negedge detected")
                high_end_time = cocotb.utils.get_sim_time(units="ns")
                break
            
        cycles = 0
        
        while True: 
            await ClockCycles(dut.clk, 1)
            PWM_2ago = PWM_1ago
            PWM_1ago = int(dut.uo_out[0].value)
            cycles = cycles + 1
            
            # Log only every 10 cycles
            if cycles % 250 == 0:
                dut._log.info(f"second posedge find. current cycle number: {cycles}")
                
            if cycles >= 10000:
                dut._log.error(f"Timeout reached after {cycles} cycles - no posedge detected")
                break
        
            if(PWM_1ago == 1 and PWM_2ago == 0):
                #posedge detected
                low_end_time = cocotb.utils.get_sim_time(units="ns")
                dut._log.info("posedge detected")
                break
            
        measured_duty_cycle = (high_end_time - high_start_time)/(low_end_time - high_start_time )
            
        assert measured_duty_cycle >= (duty_cycle*0.99) and measured_duty_cycle <= (duty_cycle*1.01), f"Duty cycle not within specified range, got {measured_duty_cycle} duty cycle when expected {duty_cycle}."
    

@cocotb.test()
async def test_pwm_duty(dut):
    #set registers appropriately
    #measure time delay between posedge/negedge to determine positive time
    #measure time delay between posedges to identify duty cycle (1% error)
    #assert
    
    dut._log.info("Start duty test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    
    #begin write transactions
    
    #enable all inputs and outputs for output and PWM

    duty_cycle = 0.5
    await set_pwm(dut, duty_cycle)
    await test_pwm(dut, duty_cycle)
    
    duty_cycle = 0.9
    await set_pwm(dut, duty_cycle)
    await test_pwm(dut, duty_cycle)
    
    duty_cycle = 1.0
    await set_pwm(dut, duty_cycle)
    await test_pwm(dut, duty_cycle)
    
    duty_cycle = 0 #should fail
    await set_pwm(dut, duty_cycle)
    await test_pwm(dut, duty_cycle)
    
    #all outputs set successfully
    #start sampling
           
    dut._log.info("PWM Duty Cycle test completed successfully")
