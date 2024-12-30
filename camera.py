# Taken from https://raspberrytips.com/how-to-live-stream-pi-camera/
import io
import logging
import socketserver
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput


FRAME_SIZE = (1280, 720)
WIDTH, HEIGHT = FRAME_SIZE
# HTML page for the MJPEG streaming demo
PAGE = f"""\
<html>
<head>
<title>RaspberryTips Pi Cam Stream</title>
</head>
<body>
<h1>Raspberry Tips Pi Camera Live Stream Demo</h1>
<img src="stream.mjpg" width="{WIDTH}" height="{HEIGHT}" />
</body>
</html>
"""

# Class to handle streaming output
class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

# Class to handle HTTP requests
class StreamingHandler(server.BaseHTTPRequestHandler):
    def __init__(self, *args, output=None, **kwargs):
        self.output = output # Store the additional argument
        super()#.__init__(*args, **kwargs)  # Call the parent class initializer

    def do_GET(self):
        if self.path == '/':
            # Redirect root path to index.html
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            # Serve the HTML page
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            # Set up MJPEG streaming
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            # Handle 404 Not Found
            self.send_error(404)
            self.end_headers()

# Class to handle streaming server
class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

class CameraServer:
    def __init__(self):
        pass

    def start(self):
        # Create Picamera2 instance and configure it
        picam2 = Picamera2()
        FRAMERATE = 24  # Set your desired framerate
        picam2.configure(picam2.create_video_configuration(main={"size": (WIDTH, HEIGHT), "format": "RGB888"}, controls={"FrameRate": FRAMERATE}))
        output = StreamingOutput()
        picam2.start_recording(JpegEncoder(), FileOutput(output))

        try:
            # Set up and start the streaming server
            address = ('', 8000)
            server = StreamingServer(address, StreamingHandler(output=output))
            server.serve_forever()
        finally:
            # Stop recording when the script is interrupted
            picam2.stop_recording()

