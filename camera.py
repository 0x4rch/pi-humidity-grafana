import io
import logging
import socketserver
from http import server
from threading import Condition
from picamera2 import picamera2
from picamera2.encoders import jpegencoder
from picamera2.outputs import fileoutput


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Redirect root path to index.html
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            # Serve the HTML page
            content = page.encode('utf-8')
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
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            try:
                while True:
                    with server_instance.output.condition:
                        server_instance.output.condition.wait()
                        frame = server_instance.output.frame
                    self.wfile.write(b'--frame\r\n')
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
            # Handle 404 not found
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class StreamingApp:
    def __init__(self, width, height, framerate=24):
        self.width = width
        self.height = height
        self.framerate = framerate
        self.output = StreamingOutput()
        self.picam2 = picamera2()
        self.page = f"""\
<html>
<head>
<title>raspberrytips pi cam stream</title>
</head>
<body>
<h1>raspberry tips pi camera live stream demo</h1>
<img src="stream.mjpg" width="{self.width}" height="{self.height}" />
</body>
</html>
"""
        self.picam2.configure(self.picam2.create_video_configuration(main={"size": (self.width, self.height), "format": "rgb888"}, controls={"framerate": self.framerate}))
        self.picam2.start_recording(jpegencoder(), fileoutput(self.output))

    def start_server(self):
        try:
            address = ('', 8000)
            server_instance = StreamingServer(address, StreamingHandler)
            server_instance.output = self.output  # Assign the shared output instance
            server_instance.serve_forever()
        finally:
            # Stop recording when the script is interrupted
            self.picam2.stop_recording()


if __name__ == '__main__':
    app = StreamingApp(1280, 720)
    app.start_server()

