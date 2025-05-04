#!/usr/bin/env python3
import os
import sys
import time
import RPi.GPIO as GPIO
import uinput

# GPIO setup
GPIO.setmode(GPIO.BCM)

pins = {
    "up": 17,
    "right": 27,
    "down": 22,
    "left": 23,
    "center": 24
}

for pin in pins.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Define virtual device with mouse events
device = uinput.Device([
    uinput.REL_X,
    uinput.REL_Y,
    uinput.BTN_LEFT
])

# Pixel delta per move
delta = 20

try:
    print("Joystick uinput mouse control running (Ctrl+C to exit)")
    while True:
        if GPIO.input(pins["up"]) == GPIO.LOW:
            device.emit(uinput.REL_Y, -delta)
            time.sleep(0.02)
        elif GPIO.input(pins["down"]) == GPIO.LOW:
            device.emit(uinput.REL_Y, delta)
            time.sleep(0.02)
        elif GPIO.input(pins["left"]) == GPIO.LOW:
            device.emit(uinput.REL_X, -delta)
            time.sleep(0.02)
        elif GPIO.input(pins["right"]) == GPIO.LOW:
            device.emit(uinput.REL_X, delta)
            time.sleep(0.02)
            
        # Handle click with continuous press
        elif GPIO.input(pins["center"]) == GPIO.LOW:
            device.emit(uinput.BTN_LEFT, 1)  # Press
            while GPIO.input(pins["center"]) == GPIO.LOW:  # While button is held down
                device.emit(uinput.BTN_LEFT, 1)  # Keep pressing
                time.sleep(0.01)  # Short delay to avoid overwhelming system
            device.emit(uinput.BTN_LEFT, 0)  # Release
            time.sleep(0.05)  # Debounce for the release of the button


except KeyboardInterrupt:
    print("Cleaning up GPIO.")
    GPIO.cleanup()
