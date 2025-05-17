import io
import os
import glob
import time
import threading
from http import server
from datetime import datetime
from urllib.parse import parse_qs
from http.server import SimpleHTTPRequestHandler, HTTPServer
import socketserver
import cv2
from PIL import Image

# For PiCamera2
from picamera2 import Picamera2, Preview
from libcamera import Transform

PAGE = '''...'''  # [Omitted here for brevity; use your full PAGE HTML from before]

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            files = glob.glob('media/*')
            file_list = '\n'.join([f'<li>{os.path.basename(f)}</li>' for f in sorted(files, key=os.path.getctime, reverse=True)])
            content = PAGE.format(files=file_list).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            stream_start = time.time()
            try:
                while True:
                    frame = picam2.capture_array()

                    # Add timestamp and blinking dot to stream
                    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    elapsed = time.time() - stream_start
                    elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed))
                    blink_on = int(time.time() * 2) % 2 == 0
                    if blink_on:
                        cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
                    cv2.putText(frame, f"Time: {now_str}", (50, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame, f"Live: {elapsed_str}", (50, 55),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                    _, jpeg = cv2.imencode('.jpg', frame)
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(jpeg)))
                    self.end_headers()
                    self.wfile.write(jpeg.tobytes())
                    self.wfile.write(b'\r\n')
                    time.sleep(1/24)
            except Exception as e:
                print('Removed streaming client:', self.client_address, str(e))
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(('{"recording": ' + ('true' if recording else 'false') + '}').encode())
        else:
            self.send_error(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        fields = parse_qs(post_data)
        if self.path == '/photo':
            filename = fields.get('filename', [''])[0].strip()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'media/{filename or "photo_" + timestamp}.jpg'
            frame = picam2.capture_array()
            cv2.imwrite(filename, frame)
        elif self.path == '/video':
            action = fields.get('action', [''])[0]
            name = fields.get('filename', [''])[0].strip()
            global recording, video_writer, recording_start
            if action == 'start' and not recording:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                video_name = f'media/{name or "video_" + timestamp}.avi'
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                video_writer = cv2.VideoWriter(video_name, fourcc, 24.0, (640, 480))
                recording_start = time.time()
                recording = True
            elif action == 'stop' and recording:
                recording = False
                video_writer.release()
        self.send_response(303)
        self.send_header('Location', '/')
        self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# Setup folder
os.makedirs('media', exist_ok=True)

# Initialize PiCamera2
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()

# Commented out for Pi version
# camera = cv2.VideoCapture(0)

recording = False
recording_start = None
video_writer = None

def recording_loop():
    global recording
    while True:
        if recording:
            frame = picam2.capture_array()
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elapsed = time.time() - recording_start
            elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed))
            blink_on = int(time.time() * 2) % 2 == 0
            if blink_on:
                cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
            cv2.putText(frame, f"Time: {now_str}", (50, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"Recording: {elapsed_str}", (50, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            video_writer.write(frame)
        time.sleep(1/24)

record_thread = threading.Thread(target=recording_loop, daemon=True)
record_thread.start()

try:
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    print("Starting EV1 camera server on port 8000...")
    server.serve_forever()
finally:
    # camera.release()  # Commented out, not using OpenCV camera
    if video_writer:
        video_writer.release()
