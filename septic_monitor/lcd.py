# 20x4 I2C LCD module for septic tank monitor

import time

from RPLCD.i2c import CharLCD

from septic_monitor import storage


lcd = CharLCD(i2c_expander="PCF8574", address=0x27, port=1, charmap="A00", cols=20, rows=4)  # i2cdetect -y 1

lcd.clear()


class Cursor:
    power = (0, 0)
    pump = (0, 12)
    level_msg = (1, 0)
    current = (1, 12)
    time = (3, 0)
    date = (3, 10)
    level = (2, 0)


lcd.cursor_pos = Cursor.power
lcd.write_string("POWER OK")
lcd.cursor_pos = Cursor.pump
lcd.write_string("PUMP OFF")
lcd.cursor_pos = Cursor.level_msg
lcd.write_string("LEVEL OK")
lcd.cursor_pos = Cursor.current
lcd.write_string("Ip= 0.0A")

while True:
    lcd.cursor_pos = Cursor.time
    lcd.write_string(time.strftime("%H:%M:%S"))

    lcd.cursor_pos = Cursor.date
    lcd.write_string(time.strftime("%Y-%m-%d"))

    lcd.cursor_pos = Cursor.level
    level = storage.get_tank_level()
    lcd.write_string(f"Level: {level.value:.1f} cm")

    time.sleep(1)
