# References
# https://www.youtube.com/watch?v=cVdSc8VYVBM
# https://github.com/adafruit/Adafruit_CircuitPython_CharLCD
### Current Log Of Last Commands

# 3d Printing references
# https://nerd-corner.com/3d-printed-dupont-connector-for-jumper-cable/ Connector idea for cable
# Bezel / housing for lcd https://www.thingiverse.com/thing:3459425

# Required library sudo pip3 install adafruit-circuitpython-charlcd
import time
import datetime
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd

class Display():
    def __init__(self):
        lcd_columns = 16
        lcd_rows = 2
        lcd_rs = digitalio.DigitalInOut(board.D26)
        lcd_en = digitalio.DigitalInOut(board.D8)
        lcd_en = digitalio.DigitalInOut(board.D19)
        lcd_d7 = digitalio.DigitalInOut(board.D11)
        lcd_d6 = digitalio.DigitalInOut(board.D5)
        lcd_d5 = digitalio.DigitalInOut(board.D6)
        lcd_d4 = digitalio.DigitalInOut(board.D13)

        # initialize display
        lcd = characterlcd.Character_LCD_Mono(
                lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows
        )

    def print_message(humidity, temperature):
        # print text
        now = datetime.datetime.now()
        date = now.strftime("%m/%d/%Y")
        time = now.strftime("%I:%M %p")
        message = f'{temperature} F    {time}\n{humidity}%    {date}'
        # TODO: Remove print
        print(message)
        lcd.message = message
