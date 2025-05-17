import os
import time
import io
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from picamera2 import Picamera2
import cv2
from PIL import Image

# Initialize PiCamera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()

# Output directory for saved images and videos
output_dir = os.path.join(os.getcwd(), "captures")
os.makedirs(output_dir, exist_ok=True)

# Global state
recording_flag = threading.Event()
recording_thread = None

def recording_loop():
    """Threaded video recording function"""
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    filename = os.path.join(output_dir, f"video_{int(time.time())}.avi")
    out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))

    while recording_flag.is_set():
        frame = picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)
        time.sleep(0.05)

    out.release()

class CamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global recording_thread

        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        if path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(f"""
                <html>
                <head>
                    <title>Pi Camera Feed</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; background-color: #f0f0f0; }}
                        .button {{ padding: 10px 20px; margin: 10px; font-size: 16px; }}
                    </style>
                </head>
                <body>
                    <h1>Pi Camera Live View</h1>
                    <img src="/image" width="640" height="480"><br>
                    <a href="/image?save=true"><button class="button">Capture Image</button></a>
                    <a href="/video?record=true"><button class="button">Start Recording</button></a>
                    <a href="/video?record=false"><button class="button">Stop Recording</button></a>
                </body>
                </html>
            """, "utf-8"))

        elif path == "/image":
            frame = picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            _, jpeg = cv2.imencode(".jpg", frame_bgr)
            image_bytes = jpeg.tobytes()

            if "save" in query and query["save"][0].lower() == "true":
                filename = os.path.join(output_dir, f"image_{int(time.time())}.jpg")
                with open(filename, "wb") as f:
                    f.write(image_bytes)

            self.send_response(200)
            self.send_header("Content-type", "image/jpeg")
            self.end_headers()
            self.wfile.write(image_bytes)

        elif path == "/video":
            if "record" in query:
                record = query["record"][0].lower() == "true"
                if record and not recording_flag.is_set():
                    recording_flag.set()
                    recording_thread = threading.Thread(target=recording_loop)
                    recording_thread.start()
                elif not record and recording_flag.is_set():
                    recording_flag.clear()  # recording_loop will exit on its own

            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

        else:
            self.send_error(404)
            self.end_headers()

# Start server
def run_server():
    server = HTTPServer(("", 8000), CamHandler)
    print("Server started on http://localhost:8000")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
