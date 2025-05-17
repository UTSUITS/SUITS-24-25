# http_server.py

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
from picamera2 import Picamera2
from libcamera import Transform

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()

output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

is_recording = False
recording_thread = None

class CamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global is_recording, recording_thread

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

            html = f"""
            <html>
            <head><title>Rename File</title></head>
            <body style="background:#121212;color:#eee;font-family:Arial;padding:20px;">
                <h1>Rename File: {file_to_rename}</h1>
                <form method="POST" action="/rename">
                    <input type="hidden" name="oldname" value="{file_to_rename}">
                    <label for="newname">New filename:</label><br>
                    <input type="text" id="newname" name="newname" value="{file_to_rename}" style="width:300px;padding:5px;font-size:16px;"><br><br>
                    <input type="submit" value="Rename" style="padding:10px 20px;font-size:16px;">
                </form>
                <br><a href="/">Back to main page</a>
            </body>
            </html>
            """
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

            html = f"""
                <html>
                <head>
                    <title>Pi Camera Live Stream</title>
                    <style>
                        body {{ background-color: #121212; color: #eee; font-family: Arial, sans-serif; margin: 0; padding: 0; }}
                        .container {{ display: flex; height: 100vh; }}
                        .left-panel {{ flex: 2; padding: 20px; }}
                        .right-panel {{ flex: 1; padding: 20px; background-color: #1e1e1e; overflow-y: auto; border-left: 1px solid #333; }}
                        h1, h2 {{ color: #fff; }}
                        a.button {{ display: inline-block; margin: 10px 10px 10px 0; padding: 10px 20px; background-color: #2d89ef; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; user-select: none; }}
                        a.button:hover {{ background-color: #1b5fbd; }}
                        a.button.recording {{ background-color: #e53935; pointer-events: none; cursor: default; }}
                        img {{ border: 3px solid #2d89ef; border-radius: 8px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="left-panel">
                            <h1>Pi Camera Live Stream</h1>
                            <img src="/stream.mjpg" width="640" height="480" />
                            <h2>Controls</h2>
                            <a href="/photo" class="button">Take Photo</a><br>
                            {'<a href="/video?record=false" class="button recording">Stop Recording</a>' if is_recording else f'<a href="/video?record=true" class="button">{recording_text}</a>'}
                        </div>
                        <div class="right-panel">
                            <h2>Saved Files</h2>
                            {file_links if files else "<p>No files saved yet.</p>"}
                        </div>
                    </div>
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
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame_bgr, timestamp, (10, frame_bgr.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
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
                    recording_thread = threading.Thread(target=self.recording_loop)
                    recording_thread.start()
                elif not record and is_recording:
                    is_recording = False
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
                self.wfile.write(b"File not found")

    def do_POST(self):
        if self.path == "/rename":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            post_vars = dict(x.split("=") for x in post_data.split("&"))
            oldname = post_vars.get("oldname", "")
            newname = post_vars.get("newname", "")
            oldpath = os.path.join(output_dir, oldname)
            newpath = os.path.join(output_dir, newname)
            if os.path.exists(oldpath) and newname:
                os.rename(oldpath, newpath)
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

    def recording_loop(self):
        global is_recording
        filename = os.path.join(output_dir, f"video_{int(time.time())}.avi")
        out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*"XVID"), 20.0, (640, 480))
        while is_recording:
            frame = picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)
            time.sleep(0.05)
        out.release()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def start_http_server():
    server = ThreadedHTTPServer(('0.0.0.0', 8000), CamHandler)
    print("HTTP server running at http://0.0.0.0:8000")
    server.serve_forever()
