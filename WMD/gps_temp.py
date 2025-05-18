import sys
import math
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QPen, QFont
from PyQt6.QtCore import Qt, QPointF, QThread, pyqtSignal
from Compass.QMC_test import get_bearing  # Your compass module


class CompassWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.heading = 0
        self.setMinimumSize(250, 250)

    def setHeading(self, heading):
        self.heading = heading % 360
        self.update()

    def paintEvent(self, event):
        size = min(self.width(), self.height())
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = size * 0.45

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(center)

        # Rotate compass rose
        painter.save()
        painter.rotate(-self.heading)

        # Draw compass circle
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawEllipse(QPointF(0, 0), radius, radius)

        # Draw tick marks and directions
        font = QFont('Arial', int(size * 0.05))
        painter.setFont(font)

        directions = ['N', 'E', 'S', 'W']
        for i in range(4):
            angle = i * 90
            rad = math.radians(angle)
            dx = math.cos(rad) * (radius - 20)
            dy = math.sin(rad) * (radius - 20)
            label = directions[i]
            painter.drawText(QPointF(dx - 10, dy + 5), label)

        painter.restore()

        # Draw fixed needle (always pointing up)
        needle_pen = QPen(Qt.GlobalColor.red, 4)
        painter.setPen(needle_pen)
        painter.drawLine(QPointF(0, 0), QPointF(0, -radius + 10))

        painter.end()


class BearingWorker(QThread):
    bearingUpdated = pyqtSignal(float)

    def __init__(self, interval_ms=100):
        super().__init__()
        self.interval_ms = interval_ms
        self.running = True

    def run(self):
        while self.running:
            try:
                heading = get_bearing()
                if heading < 0:
                    heading += 360
                self.bearingUpdated.emit(heading)
            except Exception as e:
                print(f"Error in bearing thread: {e}")
            self.msleep(self.interval_ms)

    def stop(self):
        self.running = False


class MagnetometerCompassApp:
    def __init__(self):
        self.widget = CompassWidget()
        self.worker = BearingWorker(100)  # Update every 100 ms
        self.worker.bearingUpdated.connect(self.widget.setHeading)
        self.worker.start()

    def stop(self):
        self.worker.stop()
        self.worker.wait()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    compass_app = MagnetometerCompassApp()
    compass_app.widget.setWindowTitle("Compass with Rotating Rose")
    compass_app.widget.show()
    exit_code = app.exec()
    compass_app.stop()
    sys.exit(exit_code)
