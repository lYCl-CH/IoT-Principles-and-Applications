from machine import I2C
from time import sleep

I2C_ADDRESS = 0x57

MODE_CONFIG = 0x06
SPO2_CONFIG = 0x07
LED_CONFIG = 0x09
FIFO_DATA = 0x05
FIFO_WR_PTR = 0x02
FIFO_RD_PTR = 0x04

class MAX30100:
    def __init__(self, i2c):
        self.i2c = i2c
        self.buffer_ir = []
        self.buffer_red = []
        self.reset()
        self.set_mode(0x03)  # Heart rate only
        self.set_led_current(0x0F, 0x0F)  # Maximum current
        self.set_spo2_config(0x27)  # Example config

    def reset(self):
        self.i2c.writeto_mem(I2C_ADDRESS, MODE_CONFIG, b'\x40')

    def set_mode(self, mode):
        self.i2c.writeto_mem(I2C_ADDRESS, MODE_CONFIG, bytes([mode]))

    def set_led_current(self, red, ir):
        # Red and IR currents: upper 4 bits (red), lower 4 bits (IR)
        self.i2c.writeto_mem(I2C_ADDRESS, LED_CONFIG, bytes([(red << 4) | ir]))

    def set_spo2_config(self, config):
        self.i2c.writeto_mem(I2C_ADDRESS, SPO2_CONFIG, bytes([config]))

    def read_fifo(self):
        data = self.i2c.readfrom_mem(I2C_ADDRESS, FIFO_DATA, 4)
        ir = (data[0] << 8) | data[1]
        red = (data[2] << 8) | data[3]
        return ir, red
