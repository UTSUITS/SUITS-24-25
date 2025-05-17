import io
import os
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

import cv2
import numpy as np
from PIL import Image
from picamera2 import Picamera2, Preview
from libcamera import Transform

# Start and configure the PiCamera2
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()

output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

is_recording = False
recording_thread = None

class CamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        if path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            files = os.listdir(output_dir)
            file_links = "<br>".join(
                f'<a href="/{output_dir}/{file}">{file}</a>' for file in files
            )
            html = f"""
                <html>
                <head>
                    <title>Pi Camera Stream</title>
                </head>
                <body>
                    <h1>Pi Camera Live Stream</h1>
                    <img src="/stream.mjpg" width="640" height="480" />
                    <h2>Controls</h2>
                    <a href="/photo">Take Photo</a><br>
                    <a href="/video?record=true">Start Recording</a><br>
                    <a href="/video?record=false">Stop Recording</a><br>
                    <h2>Saved Files</h2>
                    {file_links if files else "..."}
                </body>
                </html>
            """
            self.wfile.write(html.encode("utf-8"))

        elif path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Content-type", "multipart/x-mixed-replace; boundary=--jpgboundary")
            self.end_headers()

            try:
                while True:
                    frame = picam2.capture_array()
                    _, jpeg = cv2.imencode('.jpg', frame)
                    self.wfile.write(b"--jpgboundary\r\n")
                    self.send_header("Content-type", "image/jpeg")
                    self.send_header("Content-length", str(len(jpeg)))
                    self.end_headers()
                    self.wfile.write(jpeg.tobytes())
                    time.sleep(0.1)
            except Exception as e:
                print(f"Streaming stopped: {e}")

        elif path == "/photo":
            frame = picam2.capture_array()
            filename = os.path.join(output_dir, f"photo_{int(time.time())}.jpg")
            cv2.imwrite(filename, frame)
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

        elif path == "/video":
            global is_recording, recording_thread
            if "record" in query:
                record = query["record"][0].lower() == "true"
                if record and not is_recording:
                    is_recording = True
                    recording_thread = threading.Thread(target=self.recording_loop)
                    recording_thread.start()
                elif not record and is_recording:
                    is_recording = False
                    if recording_thread:
                        recording_thread.join()
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

        elif path.startswith(f"/{output_dir}/"):
            filepath = path.lstrip("/")
            if os.path.exists(filepath):
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.end_headers()
                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()

    def recording_loop(self):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        filename = os.path.join(output_dir, f"video_{int(time.time())}.avi")
        out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))

        while is_recording:
            frame = picam2.capture_array()
            out.write(frame)
            time.sleep(0.05)

        out.release()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

def run(server_class=ThreadedHTTPServer, handler_class=CamHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Server started at http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down server.")
        picam2.stop()
        httpd.server_close()

if __name__ == "__main__":
    run()
