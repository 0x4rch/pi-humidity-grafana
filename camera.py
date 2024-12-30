# Taken from https://raspberrytips.com/how-to-live-stream-pi-camera/
import io
import logging
import socketserver
from http import server
from threading import Condition
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class StreamingHandler(server.BaseHTTPRequestHandler):
    PAGE_TEMPLATE = f"""\
<html>
<head>
<title>RaspberryTips Pi Cam Stream</title>
</head>
<body>
<h1>Raspberry Tips Pi Camera Live Stream Demo</h1>
<img src="stream.mjpg" width="{self.server.width}" height="{self.server.height}" />
</body>
</html>
"""

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = self.PAGE_TEMPLATE.format(width=self.server.width, height=self.server.height).encode('utf-8')
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
            try:
                while True:
                    with self.server.output.condition:
                        self.server.output.condition.wait()
                        frame = self.server.output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning('Removed streaming client %s: %s', self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

class CameraServer:
    def __init__(self, host='', port=8000, width=1280, height=720, framerate=24):
        self.host = host
        self.port = port
        self.width = width
        self.height = height
        self.framerate = framerate
        self.picam2 = Picamera2()
        self.output = StreamingOutput()
        self.server = None

    def configure_camera(self):
        video_config = self.picam2.create_video_configuration(
            main={"size": (self.width, self.height), "format": "RGB888"},
            controls={"FrameRate": self.framerate}
        )
        self.picam2.configure(video_config)

    def start(self):
        self.configure_camera()
        self.picam2.start_recording(JpegEncoder(), FileOutput(self.output))

        self.server = StreamingServer((self.host, self.port), StreamingHandler)
        self.server.output = self.output
        self.server.width = self.width
        self.server.height = self.height

        try:
            print(f"Starting server on {self.host}:{self.port}")
            self.server.serve_forever()
        finally:
            self.picam2.stop_recording()

