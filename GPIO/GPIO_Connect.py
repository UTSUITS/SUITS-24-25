import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

pins = {
    "up": 17,      # A
    "right": 27,   # B
    "down": 22,    # C
    "left": 23,    # D
    "center": 24   # DOWN pin
}

# Setup GPIOs with pull-ups
for pin in pins.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    print("Press a direction (Ctrl+C to quit):")
    while True:
        for direction, pin in pins.items():
            if GPIO.input(pin) == GPIO.LOW:
                print(f"{direction} pressed")
        time.sleep(0.1)

except KeyboardInterrupt:
    GPIO.cleanup()
