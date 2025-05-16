from machine import I2C, Pin
from QMC5883L import QMC5883L

# Initialize I2C (adjust pins as needed for your board)
i2c = I2C(0, scl=Pin(10), sda=Pin(9))

# Create sensor object
compass = QMC5883L(i2c)

# Reset sensor to ensure it's ready
compass.reset()

# Simple read loop (or just once)
x, y, z, temp = compass.read_scaled()

print(f"Magnetic field (Gauss): X={x:.3f}, Y={y:.3f}, Z={z:.3f}")
print(f"Temperature (°C): {temp:.2f}")
