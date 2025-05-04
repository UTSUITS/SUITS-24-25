import RPi.GPIO as GPIO
import time
import pyautogui

# Setup
GPIO.setmode(GPIO.BCM)
pyautogui.FAILSAFE = False  # Avoid edge panic

pins = {
    "up": 17,
    "right": 27,
    "down": 22,
    "left": 23,
    "center": 24
}

for pin in pins.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Cursor move delta (pixels per press)
delta = 10

try:
    print("Joystick cursor control active (Ctrl+C to quit):")
    while True:
        if GPIO.input(pins["up"]) == GPIO.LOW:
            pyautogui.moveRel(0, -delta)
        if GPIO.input(pins["down"]) == GPIO.LOW:
            pyautogui.moveRel(0, delta)
        if GPIO.input(pins["left"]) == GPIO.LOW:
            pyautogui.moveRel(-delta, 0)
        if GPIO.input(pins["right"]) == GPIO.LOW:
            pyautogui.moveRel(delta, 0)
        if GPIO.input(pins["center"]) == GPIO.LOW:
            pyautogui.click()
        time.sleep(0.05)

except KeyboardInterrupt:
    GPIO.cleanup()
