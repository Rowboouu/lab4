import time
from smbus2 import SMBus

class LcdApi:
    # Implements the API for talking with HD44780 compatible character LCDs.
    # This class only knows what commands to send to the LCD, and not how to get
    # them to the LCD. A derived class must implement the hal_xxx functions.

    # HD44780 LCD controller command set
    LCD_CLR = 0x01  # Clear display
    LCD_HOME = 0x02  # Return to home position

    LCD_ENTRY_MODE = 0x04  # Set entry mode
    LCD_ENTRY_INC = 0x02  # Increment cursor
    LCD_ENTRY_SHIFT = 0x01  # Shift display

    LCD_ON_CTRL = 0x08  # Display on/off control
    LCD_ON_DISPLAY = 0x04  # Turn display on
    LCD_ON_CURSOR = 0x02  # Turn cursor on
    LCD_ON_BLINK = 0x01  # Blinking cursor

    LCD_MOVE = 0x10  # Cursor or display shift
    LCD_MOVE_DISP = 0x08  # Display shift
    LCD_MOVE_RIGHT = 0x04  # Move right

    LCD_FUNCTION = 0x20  # Function set
    LCD_FUNCTION_8BIT = 0x10  # 8-bit mode
    LCD_FUNCTION_2LINES = 0x08  # Two lines
    LCD_FUNCTION_10DOTS = 0x04  # 5x10 font

    LCD_CGRAM = 0x40  # Set CG RAM address
    LCD_DDRAM = 0x80  # Set DD RAM address

    LCD_RS_CMD = 0
    LCD_RS_DATA = 1

    LCD_RW_WRITE = 0
    LCD_RW_READ = 1

    def __init__(self, bus, address, num_lines, num_columns):
        self.bus = bus
        self.address = address
        self.num_lines = min(num_lines, 4)
        self.num_columns = min(num_columns, 40)
        self.cursor_x = 0
        self.cursor_y = 0
        self.implied_newline = False
        self.backlight = True

        self.display_off()
        self.backlight_on()
        self.clear()
        self.hal_write_command(self.LCD_ENTRY_MODE | self.LCD_ENTRY_INC)
        self.hide_cursor()
        self.display_on()

    def clear(self):
        self.hal_write_command(self.LCD_CLR)
        time.sleep(0.002)  # Clearing the display takes 1.52ms
        self.cursor_x = 0
        self.cursor_y = 0

    def show_cursor(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY | self.LCD_ON_CURSOR)

    def hide_cursor(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def blink_cursor_on(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY | self.LCD_ON_CURSOR | self.LCD_ON_BLINK)

    def blink_cursor_off(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY | self.LCD_ON_CURSOR)

    def display_on(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def display_off(self):
        self.hal_write_command(self.LCD_ON_CTRL)

    def backlight_on(self):
        self.backlight = True
        self.hal_backlight_on()

    def backlight_off(self):
        self.backlight = False
        self.hal_backlight_off()

    def move_to(self, cursor_x, cursor_y):
        self.cursor_x = cursor_x
        self.cursor_y = cursor_y
        addr = cursor_x & 0x3F
        if cursor_y & 1:
            addr += 0x40
        if cursor_y & 2:
            addr += self.num_columns
        self.hal_write_command(self.LCD_DDRAM | addr)

    def putchar(self, char):
        if char == '\n':
            if not self.implied_newline:
                self.cursor_x = self.num_columns
        else:
            self.hal_write_data(ord(char))
            self.cursor_x += 1

        if self.cursor_x >= self.num_columns:
            self.cursor_x = 0
            self.cursor_y += 1
            self.implied_newline = (char != '\n')
        if self.cursor_y >= self.num_lines:
            self.cursor_y = 0
        self.move_to(self.cursor_x, self.cursor_y)

    def putstr(self, string):
        for char in string:
            self.putchar(char)

    def custom_char(self, location, charmap):
        location &= 0x7
        self.hal_write_command(self.LCD_CGRAM | (location << 3))
        time.sleep(0.00004)
        for i in range(8):
            self.hal_write_data(charmap[i])
            time.sleep(0.00004)
        self.move_to(self.cursor_x, self.cursor_y)

    def hal_backlight_on(self):
        # This function can be customized for modules with a backlight control pin
        pass

    def hal_backlight_off(self):
        # This function can be customized for modules with a backlight control pin
        pass

    def hal_write_command(self, cmd):
        self.hal_write_byte(self.LCD_RS_CMD, cmd)

    def hal_write_data(self, data):
        self.hal_write_byte(self.LCD_RS_DATA, data)

    def hal_write_byte(self, rs, data):
        byte = (data & 0xF0) | (rs << 0) | (self.backlight << 3)
        self.bus.write_byte(self.address, byte)
        self.hal_pulse_enable(byte)

        byte = ((data << 4) & 0xF0) | (rs << 0) | (self.backlight << 3)
        self.bus.write_byte(self.address, byte)
        self.hal_pulse_enable(byte)

    def hal_pulse_enable(self, data):
        enable_bit = 0x04
        self.bus.write_byte(self.address, data | enable_bit)
        time.sleep(0.000001)
        self.bus.write_byte(self.address, data & ~enable_bit)
        time.sleep(0.00005)

# Example usage:
# bus = SMBus(1)  # Use I2C bus 1
# lcd = LcdApi(bus, 0x27, 2, 16)  # Address 0x27, 2 lines, 16 columns
# lcd.putstr("Hello, World!")
