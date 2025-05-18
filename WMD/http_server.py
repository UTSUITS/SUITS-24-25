# http_server.py

import os
import time
import threading
import cv2
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

from PIL import Image

# Global camera placeholder
picam2 = None

output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

is_recording = False
recording_thread = None

class CamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global is_recording, recording_thread, picam2

        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        if path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Content-type", "multipart/x-mixed-replace; boundary=--jpgboundary")
            self.end_headers()
            try:
                while True:
                    # frame = picam2.capture_array()
                    frame = picam2.capture_array()

                    # REMOVE this line:
                    # frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                    # Instead, just use the frame directly
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, timestamp, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    _, jpeg = cv2.imencode('.jpg', frame)

                    # timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    # cv2.putText(frame_bgr, timestamp, (10, frame_bgr.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    # _, jpeg = cv2.imencode('.jpg', frame_bgr)
                    self.wfile.write(b"--jpgboundary\r\n")
                    self.send_header("Content-type", "image/jpeg")
                    self.send_header("Content-length", str(len(jpeg)))
                    self.end_headers()
                    self.wfile.write(jpeg.tobytes())
                    time.sleep(0.1)
            except Exception as e:
                print(f"Streaming stopped: {e}")
        # [Keep rest of the handlers the same, replacing picam2 with global variable]

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True

def start_http_server(shared_cam, port=8000):
    global picam2
    picam2 = shared_cam
    server = ThreadedHTTPServer(('', port), CamHandler)
    print(f"HTTP server running on port {port}")
    server.serve_forever()
