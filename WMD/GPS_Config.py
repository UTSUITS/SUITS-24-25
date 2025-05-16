from qmc5883l import QMC5883L
import smbus

def test_qmc5883l_init():
    try:
        compass = QMC5883L()  # try no arguments
        print("Compass initialized with no arguments")
    except TypeError as e:
        print(f"No-arg initialization failed: {e}")

    try:
        compass = QMC5883L(1)  # try bus number
        print("Compass initialized with bus number (1)")
    except TypeError as e:
        print(f"Bus number initialization failed: {e}")

    try:
        bus = smbus.SMBus(1)
        compass = QMC5883L(bus)  # try bus object
        print("Compass initialized with bus object (smbus.SMBus(1))")
    except TypeError as e:
        print(f"Bus object initialization failed: {e}")

if __name__ == "__main__":
    test_qmc5883l_init()
