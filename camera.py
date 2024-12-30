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
    def __init__(self, request, client_address, server, output, page):
        self.output = output  # Pass output instance
        self.page = page
        super().__init__(request, client_address, server)

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = self.page.encode('utf-8')
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
                    with self.output.condition:
                        self.output.condition.wait()
                        frame = self.output.frame
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
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass, output, page):
        # Pass output to the handler
        self.output = output
        self.page = page
        self.RequestHandlerClass = lambda *args, **kwargs: RequestHandlerClass(*args, output=self.output, page=self.page, **kwargs)
        super().__init__(server_address, self.RequestHandlerClass)


class PiCameraStreamApp:
    def __init__(self):
        self.width, self.height = 1280, 720
        self.page = f"""\
        <html>
        <head>
        <title>RaspberryTips Pi Cam Stream</title>
        </head>
        <body>
        <h1>Raspberry Tips Pi Camera Live Stream Demo</h1>
        <img src="stream.mjpg" width="{self.width}" height="{self.height}" />
        </body>
        </html>
        """
        self.output = StreamingOutput()
        self.picam2 = Picamera2()
        self.framerate = 24  # Set your desired framerate
        self.picam2.configure(self.picam2.create_video_configuration(main={"size": (self.width, self.height), "format": "RGB888"}, controls={"FrameRate": self.framerate}))
        self.picam2.start_recording(JpegEncoder(), FileOutput(self.output))

    def start(self):
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler, self.output, self.page)
        try:
            server.serve_forever()
        finally:
            self.picam2.stop_recording()


if __name__ == "__main__":
    app = PiCameraStreamApp()
    app.start()

