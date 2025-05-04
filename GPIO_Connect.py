import RPi.GPIO as GPIO
import time

# Use BCM numbering
GPIO.setmode(GPIO.BCM)

# Define GPIO pins for each direction
pins = {
    "up": 17,      # GPIO17 = physical pin 11
    "right": 27,   # GPIO27 = physical pin 13
    "down": 22,    # GPIO22 = physical pin 15
    "left": 23,    # GPIO23 = physical pin 16
    "center": 24   # GPIO24 = physical pin 18
}

# Setup each pin as input with pull-up resistor
for pin in pins.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Press a direction (Ctrl+C to quit):")

try:
    while True:
        for direction, pin in pins.items():
            if GPIO.input(pin) == GPIO.LOW:
                print(f"{direction} pressed")
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")
    GPIO.cleanup()
