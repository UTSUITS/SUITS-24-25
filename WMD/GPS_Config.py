import sys
import time
import struct
import math
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPolygon, QColor, QPen, QFont
import smbus2

# QMC5883L and I2CWrapper classes as before (copy exactly from previous script)...

class QMC5883L:
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

class CompassWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.heading = 0  # degrees

    def set_heading(self, heading):
        self.heading = heading
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        size = min(self.width(), self.height())
        cx, cy = self.width() // 2, self.height() // 2
        radius = size // 2 - 10

        # Draw outer circle
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.setBrush(QColor(240, 240, 240))
        painter.drawEllipse(cx - radius, cy - radius, 2 * radius, 2 * radius)

        # Draw cardinal points
        painter.setFont(QFont('Arial', 12))
        directions = [('N', 0), ('E', 90), ('S', 180), ('W', 270)]
        for d, angle in directions:
            angle_rad = math.radians(angle)
            tx = cx + math.sin(angle_rad) * (radius - 20)
            ty = cy - math.cos(angle_rad) * (radius - 20)
            painter.drawText(int(tx) - 10, int(ty) + 6, d)

        # Draw heading arrow
        painter.setPen(QPen(Qt.GlobalColor.red, 3))
        painter.setBrush(Qt.GlobalColor.red)
        painter.translate(cx, cy)
        painter.rotate(self.heading)
        arrow = QPolygon([
            QPoint(0, -radius + 20),
            QPoint(-10, 10),
            QPoint(0, 0),
            QPoint(10, 10)
        ])
        painter.drawPolygon(arrow)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QMC5883L Compass")
        self.resize(300, 400)

        self.mag_label = QLabel("Magnetic Field: X=0.00 Y=0.00 Z=0.00")
        self.temp_label = QLabel("Temperature: 0.00 °C")

        self.compass = CompassWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.mag_label)
        layout.addWidget(self.temp_label)
        layout.addWidget(self.compass)

        self.setLayout(layout)

        bus = smbus2.SMBus(1)
        i2c = I2CWrapper(bus)
        self.sensor = QMC5883L(i2c)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_readings)
        self.timer.start(1000)  # 1 second update

    def update_readings(self):
        try:
            x, y, z, temp = self.sensor.read_scaled()
            self.mag_label.setText(f"Magnetic Field: X={x:.3f} Y={y:.3f} Z={z:.3f}")
            self.temp_label.setText(f"Temperature: {temp:.2f} °C")

            # Calculate heading in degrees from X and Y
            heading_rad = math.atan2(y, x)
            heading_deg = math.degrees(heading_rad)
            if heading_deg < 0:
                heading_deg += 360

            self.compass.set_heading(heading_deg)
        except Exception as e:
            self.mag_label.setText(f"Error reading sensor: {e}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
