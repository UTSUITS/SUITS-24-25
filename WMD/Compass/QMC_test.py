import py_qmc5883l # type: ignore
import math as m

sensor = py_qmc5883l.QMC5883L(output_range=py_qmc5883l.RNG_8G)
sensor.calibration = [[1.044690880951639, 0.12114736424952487, -932.8075168601913], [0.12114736424952492, 1.328404442966541, 949.8242267184698], [0.0, 0.0, 1.0]]
def get_bearing():
    heading = sensor.get_bearing()
    return heading

if __name__ == "__main__":
    while True:
        x, y, z = sensor.get_magnet_raw()
        heading1 = sensor.get_bearing()
        heading2 = m.degrees(m.atan2(y, x))
        if heading2 < 0:
            heading2 += 360
        print(f"Magnetometer: X={x}, Y={y}, Z={z} | Heading1: {heading1:.2f}° | Heading2: {heading2:.2f}°")
        # time.sleep(0.5)
    
