#!/usr/bin/env python3
import os
import sys

# Auto-promote to sudo if not already root
if os.geteuid() != 0:
    print("Re-running with sudo...")
    os.execvp("sudo", ["sudo", "python3"] + sys.argv)

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

delta = 50  # Pixels moved per press

try:
    print("Joystick cursor control active (Ctrl+C to quit):")
    while True:
        if GPIO.input(pins["up"]) == GPIO.LOW:
            pyautogui.moveRel(0, -delta)
            time.sleep(0.2)
        elif GPIO.input(pins["down"]) == GPIO.LOW:
            pyautogui.moveRel(0, delta)
            time.sleep(0.2)
        elif GPIO.input(pins["left"]) == GPIO.LOW:
            pyautogui.moveRel(-delta, 0)
            time.sleep(0.2)
        elif GPIO.input(pins["right"]) == GPIO.LOW:
            pyautogui.moveRel(delta, 0)
            time.sleep(0.2)
        elif GPIO.input(pins["center"]) == GPIO.LOW:
            pyautogui.click()
            time.sleep(0.2)
except KeyboardInterrupt:
    print("\nExiting. Cleaning up GPIO.")
    GPIO.cleanup()
