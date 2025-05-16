import time
import struct
import smbus2

# Your provided QMC5883L class here (copy-paste exactly from your code)
class QMC5883L:
    # Constants and register definitions as per your provided code
    ADDR = 0x0D
    X_LSB = 0
    X_MSB = 1
    Y_LSB = 2
    Y_MSB = 3
    Z_LSB = 4
    Z_MSB = 5
    STATUS = 6
    T_LSB = 7
    T_MSB = 8
    CONFIG = 9
    CONFIG2 = 10
    RESET = 11
    STATUS2 = 12
    CHIP_ID = 13

    STATUS_DRDY = 1
    STATUS_OVL = 2
    STATUS_DOR = 4

    CONFIG_OS512 = 0b00000000
    CONFIG_OS256 = 0b01000000
    CONFIG_OS128 = 0b10000000
    CONFIG_OS64 = 0b11000000

    CONFIG_2GAUSS = 0b00000000
    CONFIG_8GAUSS = 0b00010000

    CONFIG_10HZ = 0b00000000
    CONFIG_50HZ = 0b00000100
    CONFIG_100HZ = 0b00001000
    CONFIG_200HZ = 0b00001100

    CONFIG_STANDBY = 0b00000000
    CONFIG_CONT = 0b00000001

    CONFIG2_INT_DISABLE = 0b00000001
    CONFIG2_ROL_PTR = 0b01000000
    CONFIG2_SOFT_RST = 0b10000000

    def __init__(self, i2c, offset=50.0):
        self.i2c = i2c
        self.temp_offset = offset
        self.oversampling = QMC5883L.CONFIG_OS64
        self.range = QMC5883L.CONFIG_2GAUSS
        self.rate = QMC5883L.CONFIG_100HZ
        self.mode = QMC5883L.CONFIG_CONT
        self.register = bytearray(9)
        self.command = bytearray(1)
        self.reset()

    def reset(self):
        self.command[0] = 1
        self.i2c.writeto_mem(QMC5883L.ADDR, QMC5883L.RESET, self.command)
        time.sleep(0.1)
        self.reconfig()

    def reconfig(self):
        self.command[0] = (self.oversampling | self.range | self.rate | self.mode)
        self.i2c.writeto_mem(QMC5883L.ADDR, QMC5883L.CONFIG, self.command)
        time.sleep(0.01)
        self.command[0] = QMC5883L.CONFIG2_INT_DISABLE
        self.i2c.writeto_mem(QMC5883L.ADDR, QMC5883L.CONFIG2, self.command)
        time.sleep(0.01)

    def ready(self):
        status = self.i2c.readfrom_mem(QMC5883L.ADDR, QMC5883L.STATUS, 1)[0]
        if status == QMC5883L.STATUS_DOR:
            print("Incomplete read")
            return QMC5883L.STATUS_DRDY
        return status & QMC5883L.STATUS_DRDY

    def read_raw(self):
        try:
            while not self.ready():
                time.sleep(0.005)
            self.i2c.readfrom_mem_into(QMC5883L.ADDR, QMC5883L.X_LSB, self.register)
        except OSError as error:
            print("OSError", error)
            pass
        x, y, z, _, temp = struct.unpack('<hhhBh', self.register)
        return (x, y, z, temp)

    def read_scaled(self):
        x, y, z, temp = self.read_raw()
        scale = 12000 if self.range == QMC5883L.CONFIG_2GAUSS else 3000
        return (x / scale, y / scale, z / scale, (temp / 100 + self.temp_offset))

# I2C Wrapper for smbus2 to match expected interface
class I2CWrapper:
    def __init__(self, bus):
        self.bus = bus

    def writeto_mem(self, addr, reg, data):
        self.bus.write_i2c_block_data(addr, reg, list(data))

    def readfrom_mem(self, addr, reg, nbytes):
        data = self.bus.read_i2c_block_data(addr, reg, nbytes)
        return bytes(data)

    def readfrom_mem_into(self, addr, reg, buf):
        data = self.bus.read_i2c_block_data(addr, reg, len(buf))
        for i in range(len(buf)):
            buf[i] = data[i]

def main():
    bus = smbus2.SMBus(1)  # Raspberry Pi default I2C bus
    i2c = I2CWrapper(bus)
    compass = QMC5883L(i2c)
    
    while True:
        x, y, z, temp = compass.read_scaled()
        print(f"Magnetic Field (Gauss): X={x:.3f}, Y={y:.3f}, Z={z:.3f}")
        print(f"Temperature (°C): {temp:.2f}")
        print("-" * 30)
        time.sleep(1)

if __name__ == "__main__":
    main()
