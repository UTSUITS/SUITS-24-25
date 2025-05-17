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

# Comment out PiCamera2 import and usage for laptop testing
# from picamera2 import Picamera2, Preview
# from libcamera import Transform

PAGE = '''
<html>
<head>
    <title>EV1 Camera Feed</title>
    <style>
        body {{
            background-color: #1e1e1e;
            color: #f5f5f5;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: row;
        }}
        .left {{
            flex: 2;
            padding: 20px;
        }}
        .right {{
            flex: 1;
            padding: 20px;
            background-color: #2e2e2e;
        }}
        img {{
            border: 3px solid #444;
            max-width: 100%;
            height: auto;
        }}
        button {{
            margin: 10px;
            padding: 10px;
            font-size: 16px;
            background-color: #444;
            color: white;
            border: none;
            cursor: pointer;
        }}
        input {{
            background-color: #444;
            border: none;
            padding: 8px;
            color: white;
            margin: 5px 0;
        }}
        h2 {{
            border-bottom: 1px solid #555;
        }}
        ul {{
            list-style: none;
            padding-left: 0;
        }}
        li {{
            padding: 5px;
        }}
        .recording-dot {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: red;
            animation: blink 1s infinite;
            vertical-align: middle;
            margin-left: 10px;
        }}
        @keyframes blink {{
            0%, 50%, 100% {{ opacity: 1; }}
            25%, 75% {{ opacity: 0; }}
        }}
    </style>
    <script>
        async function checkRecording() {{
            try {{
                const res = await fetch('/status');
                const data = await res.json();
                const dot = document.getElementById('recording-dot');
                if (dot) {{
                    dot.style.display = data.recording ? 'inline-block' : 'none';
                }}
            }} catch (e) {{
                console.error(e);
            }}
        }}
        setInterval(checkRecording, 1000);
    </script>
</head>
<body>
    <div class="left">
        <h1>EV1 Camera Feed</h1>
        <img src="/stream.mjpg" />
        <br />
        <form action="/photo" method="POST">
            <input type="text" name="filename" placeholder="Photo name (optional)" />
            <button type="submit">Take Photo</button>
        </form>
        <form action="/video" method="POST">
            <input type="text" name="filename" placeholder="Video name (optional)" />
            <button type="submit" name="action" value="start">Start Video</button>
            <button type="submit" name="action" value="stop">Stop Video</button>
            <span id="recording-dot" class="recording-dot" style="display:none;"></span>
        </form>
    </div>
    <div class="right">
        <h2>Saved Files</h2>
        <ul>
            {files}
        </ul>
    </div>
</body>
</html>
'''

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
                    ret, frame = camera.read()
                    if not ret:
                        continue

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
            ret, frame = camera.read()
            if ret:
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

# Commented Pi Camera for laptop testing
# picam2 = Picamera2()
# picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
# picam2.start()
# Use OpenCV camera
camera = cv2.VideoCapture(0)

recording = False
recording_start = None
video_writer = None

def recording_loop():
    global recording
    while True:
        if recording:
            ret, frame = camera.read()
            if ret:
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
    camera.release()
    if video_writer:
        video_writer.release()
