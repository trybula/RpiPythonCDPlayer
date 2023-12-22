import subprocess
from Adafruit_CharLCD import Adafruit_CharLCD #LCD
import time #control time
import RPi.GPIO as GPIO
import signal

lcd = Adafruit_CharLCD(rs=26, en=25,
                       d4=10, d5=9, d6=11, d7=0,
                       cols=16, lines=2)
GPIO.setmode(GPIO.BCM)
button_pin = 12
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
lcd.clear()
lcd.message("  Welcome to my \n    cd player")
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
            lcd.message('Eject/Input')
