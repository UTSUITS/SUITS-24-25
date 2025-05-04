import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

pins = {
    "up": 11,      # A
    "right": 13,   # B
    "down": 15,    # D
    "left": 16,    # C
    "center": 18   # DOWN pin
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
