import serial
import pynmea2
from qmc5883l import QMC5883L
import smbus2
import time

def read_gps(port):
    try:
        line = port.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith('$GNGGA') or line.startswith('$GPGGA'):
            msg = pynmea2.parse(line)
            if msg.latitude and msg.longitude:
                return (msg.latitude, msg.longitude)
    except pynmea2.ParseError:
        pass
    return (None, None)

def read_compass(sensor):
    try:
        heading = sensor.get_bearing()
        return heading
    except Exception as e:
        print(f"Compass error: {e}")
        return None

def main():
    print("Initializing...")
    try:
        gps = serial.Serial('/dev/serial0', baudrate=38400, timeout=1)

        i2c_bus = smbus2.SMBus(1)  # Raspberry Pi I2C bus 1
        compass = QMC5883L(i2c_bus)  # pass just i2c_bus

        print("GPS + Compass active. Press Ctrl+C to exit.")
        while True:
            lat, lon = read_gps(gps)
            heading = read_compass(compass)

            if lat and lon:
                print(f"📡 GPS: Latitude={lat:.6f}, Longitude={lon:.6f}")
            else:
                print("📡 GPS: Waiting for fix...")

            if heading is not None:
                print(f"🧭 Compass Heading: {heading:.2f}°")
            else:
                print("🧭 Compass: No data")

            print("-" * 40)
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if 'gps' in locals() and gps.is_open:
            gps.close()

if __name__ == '__main__':
    main()
