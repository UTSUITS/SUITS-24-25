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
stop_event = threading.Event()

class CamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global is_recording, recording_thread, stop_event

        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        if path == "/rename":
            file_to_rename = query.get("file", [""])[0]
            if not file_to_rename or not os.path.exists(os.path.join(output_dir, file_to_rename)):
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"File not found for renaming")
                return

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = f"""..."""  # [UI unchanged for brevity]
            self.wfile.write(html.encode("utf-8"))
            return

        files = os.listdir(output_dir)
        file_links = "<br>".join(
            f'<a href="/{output_dir}/{file}">{file}</a> <a href="/rename?file={file}" style="color:#2d89ef;">[Rename]</a>'
            for file in files
        )

        recording_text = "Start Recording"
        if is_recording:
            recording_text = "Recording..."

        if path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            html = f"""..."""  # [UI unchanged for brevity]
            self.wfile.write(html.encode("utf-8"))

        elif path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Content-type", "multipart/x-mixed-replace; boundary=--jpgboundary")
            self.end_headers()
            try:
                while True:
                    frame = picam2.capture_array()
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame_bgr, timestamp, (10, frame_bgr.shape[0] - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    _, jpeg = cv2.imencode('.jpg', frame_bgr)
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
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            filename = os.path.join(output_dir, f"photo_{int(time.time())}.jpg")
            cv2.imwrite(filename, frame_bgr)
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

        elif path == "/video":
            if "record" in query:
                record = query["record"][0].lower() == "true"
                if record and not is_recording:
                    is_recording = True
                    stop_event.clear()
                    recording_thread = threading.Thread(target=self.recording_loop)
                    recording_thread.start()
                elif not record and is_recording:
                    is_recording = False
                    stop_event.set()
                    if recording_thread is not None:
                        recording_thread.join()
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

        elif path.startswith(f"/{output_dir}/"):
            filepath = path.lstrip("/")
            if os.path.exists(filepath):
                self.send_response(200)
                if filepath.lower().endswith(".jpg"):
                    self.send_header("Content-type", "image/jpeg")
                elif filepath.lower().endswith(".avi"):
                    self.send_header("Content-type", "video/x-msvideo")
                else:
                    self.send_header("Content-type", "application/octet-stream")
                self.end_headers()
                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()

    def do_POST(self):
        if self.path == "/rename":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)

            oldname = params.get("oldname", [""])[0]
            newname = params.get("newname", [""])[0].strip()

            if not newname or "/" in newname or "\\" in newname or newname.startswith("."):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid filename")
                return

            oldpath = os.path.join(output_dir, oldname)
            newpath = os.path.join(output_dir, newname)

            if not os.path.exists(oldpath):
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Original file not found")
                return

            if os.path.exists(newpath):
                self.send_response(409)
                self.end_headers()
                self.wfile.write(b"File with new name already exists")
                return

            os.rename(oldpath, newpath)
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

    def recording_loop(self):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        filename = os.path.join(output_dir, f"video_{int(time.time())}.avi")
        out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
        print(f"[INFO] Started recording to {filename}")
        while not stop_event.is_set():
            frame = picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)
            time.sleep(0.05)
        out.release()
        print(f"[INFO] Finished recording to {filename}")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

def run(server_class=ThreadedHTTPServer, handler_class=CamHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Server started on http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Server stopped.")

if __name__ == "__main__":
    run()
