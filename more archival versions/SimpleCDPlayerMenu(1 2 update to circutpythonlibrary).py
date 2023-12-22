import subprocess
import time #control time
import RPi.GPIO as GPIO
import signal
import board
from digitalio import DigitalInOut
from adafruit_character_lcd.character_lcd import Character_LCD_Mono

# Modify this if you have a different sized character LCD
lcd_columns = 16
lcd_rows = 2

lcd_rs = DigitalInOut(board.D26)
lcd_en = DigitalInOut(board.D25)
lcd_d4 = DigitalInOut(board.D10)
lcd_d5 = DigitalInOut(board.D9)
lcd_d6 = DigitalInOut(board.D11)
lcd_d7 = DigitalInOut(board.D0)
# Initialise the LCD class
lcd = Character_LCD_Mono(
    lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows
)

GPIO.setmode(GPIO.BCM)
button_pin = 12
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
lcd.clear()
lcd.cursor = False
lcd.blink = False
lcd.message ="  Welcome to my \n    cd player"
time.sleep(2)

'''
def run_script():
    process = subprocess.run(['python', '/home/mtryb/pytest/SimpleCDPlayerv1.py'], check=True)
    lcd.clear()
    lcd.message("Ejected")
    return process.returncode

while True:
    lcd.clear()
    lcd.message("Click for\nloading")
    GPIO.wait_for_edge(button_pin, GPIO.FALLING)
    time.sleep(1)
    return_code = run_script()
    print(f"The script returned: {return_code}")
    time.sleep(1)
'''   
GPIO.setmode(GPIO.BCM)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
process = None

while True:
    GPIO.wait_for_edge(button_pin, GPIO.FALLING)
    input_state = GPIO.input(button_pin)
    time.sleep(0.5)
    if input_state == False:
        if process is None or process.poll() is not None:
            process = subprocess.Popen(['python', '/home/mtryb/pytest/SimpleCDPlayerv1.py'])
        else:
            process.send_signal(signal.SIGINT)
            lcd.clear()
            lcd.cursor = True
            lcd.blink = True
            lcd.message('Eject/Input')
