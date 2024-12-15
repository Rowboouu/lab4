import time
from smbus2 import SMBus
from lcd_api import LcdApi

# PCF8574 pin definitions
MASK_RS = 0x01       # P0
MASK_RW = 0x02       # P1
MASK_E  = 0x04       # P2

SHIFT_BACKLIGHT = 3  # P3
SHIFT_DATA      = 4  # P4-P7

class I2cLcd(LcdApi):

    # Implements a HD44780 character LCD connected via PCF8574 on I2C

    def __init__(self, bus, i2c_addr, num_lines, num_columns):
        self.bus = bus
        self.i2c_addr = i2c_addr
        self.bus.write_byte(self.i2c_addr, 0x00)
        time.sleep(0.02)  # Allow LCD time to power up

        # Send reset 3 times
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        time.sleep(0.005)  # Need to delay at least 4.1ms
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        time.sleep(0.001)
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        time.sleep(0.001)

        # Put LCD into 4-bit mode
        self.hal_write_init_nibble(self.LCD_FUNCTION)
        time.sleep(0.001)

        LcdApi.__init__(self, num_lines, num_columns)
        cmd = self.LCD_FUNCTION
        if num_lines > 1:
            cmd |= self.LCD_FUNCTION_2LINES
        self.hal_write_command(cmd)

    def hal_write_init_nibble(self, nibble):
        # Writes an initialization nibble to the LCD.
        byte = ((nibble >> 4) & 0x0F) << SHIFT_DATA
        self.bus.write_byte(self.i2c_addr, byte | MASK_E)
        self.bus.write_byte(self.i2c_addr, byte)

    def hal_backlight_on(self):
        # Turns the backlight on
        self.bus.write_byte(self.i2c_addr, 1 << SHIFT_BACKLIGHT)

    def hal_backlight_off(self):
        # Turns the backlight off
        self.bus.write_byte(self.i2c_addr, 0x00)

    def hal_write_command(self, cmd):
        # Write a command to the LCD. Data is latched on the falling edge of E.
        byte = ((self.backlight << SHIFT_BACKLIGHT) |
                (((cmd >> 4) & 0x0F) << SHIFT_DATA))
        self.bus.write_byte(self.i2c_addr, byte | MASK_E)
        self.bus.write_byte(self.i2c_addr, byte)

        byte = ((self.backlight << SHIFT_BACKLIGHT) |
                ((cmd & 0x0F) << SHIFT_DATA))
        self.bus.write_byte(self.i2c_addr, byte | MASK_E)
        self.bus.write_byte(self.i2c_addr, byte)

        if cmd <= 3:
            # The home and clear commands require a worst case delay of 4.1ms
            time.sleep(0.005)

    def hal_write_data(self, data):
        # Write data to the LCD. Data is latched on the falling edge of E.
        byte = (MASK_RS |
                (self.backlight << SHIFT_BACKLIGHT) |
                (((data >> 4) & 0x0F) << SHIFT_DATA))
        self.bus.write_byte(self.i2c_addr, byte | MASK_E)
        self.bus.write_byte(self.i2c_addr, byte)

        byte = (MASK_RS |
                (self.backlight << SHIFT_BACKLIGHT) |
                ((data & 0x0F) << SHIFT_DATA))
        self.bus.write_byte(self.i2c_addr, byte | MASK_E)
        self.bus.write_byte(self.i2c_addr, byte)

# Example usage:
# bus = SMBus(1)  # Use I2C bus 1
# lcd = I2cLcd(bus, 0x27, 2, 16)  # Address 0x27, 2 lines, 16 columns
# lcd.putstr("Hello, World!")
