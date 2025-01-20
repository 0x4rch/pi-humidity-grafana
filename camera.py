# Inspired By: https://raspberrytips.com/how-to-live-stream-pi-camera/
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
    def __init__(self, request, client_address, server, output, camera_stream_instance):
        self.output = output  # Pass output instance
        self.camera_stream_instance = camera_stream_instance
        self.page = camera_stream_instance.page
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

    def __init__(self, server_address, RequestHandlerClass, output, camera_stream_instance):
        # Pass output to the handler
        self.output = output
        self.camera_stream_instance = camera_stream_instance
        self.RequestHandlerClass = lambda *args, **kwargs: RequestHandlerClass(*args, output=self.output, camera_stream_instance=self.camera_stream_instance, **kwargs)

        super().__init__(server_address, self.RequestHandlerClass)


class CameraStream:
    def __init__(self, width, height, temperature, humidity):
        self.width, self.height = width, height
        self.temperature, self.humidity = temperature, humidity
        self.page = self.generate_page(self.temperature, self.humidity)
        self.output = StreamingOutput()
        self.picam2 = Picamera2()
        self.framerate = 24  # Set your desired framerate
        self.picam2.configure(self.picam2.create_video_configuration(main={"size": (self.width, self.height), "format": "RGB888"}, controls={"FrameRate": self.framerate}))
        self.picam2.start_recording(JpegEncoder(), FileOutput(self.output))

    def start(self):
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler, self.output, self)
        try:
            server.serve_forever()
        finally:
            self.picam2.stop_recording()

    def update_temperature_and_humidity(self, temperature, humidity):
        print('****VALID READING**** Updating temperature and humidity ****VALID READING****')
        self.temperature = temperature
        self.humidity = humidity
        self.page = self.generate_page(self.temperature, self.humidity)

    def generate_page(self, temperature, humidity):
        return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tent Camera</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-gray-100 font-sans">
    <header class="p-4 bg-gray-800 border-b border-gray-700">
        <div class="max-w-7xl mx-auto flex justify-between items-center">
            <h1 class="text-3xl font-bold flex items-center gap-2">
                <span class="bg-red-600 text-white px-3 py-1 rounded-lg text-lg font-semibold">
                    LIVE
                </span>
                Tent Camera
            </h1>
        </div>
    </header>
    <main class="mx-auto p-6">
        <div class="flex flex-col md:flex-row gap-6">
            <!-- Video Stream -->
            <div class="flex-1 rounded-lg overflow-hidden border border-gray-700">
                <img src="stream.mjpg" alt="Live Stream" class="w-full h-auto">
            </div>
            <!-- Temperature and Humidity -->
            <div class="flex flex-col gap-4 w-full md:w-1/6">
                <div class="bg-gray-800 p-6 rounded-lg text-center">
                    <h2 class="text-xl font-medium">Temperature</h2>
                    <p class="text-3xl font-bold text-green-400">{temperature}°F</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg text-center">
                    <h2 class="text-xl font-medium">Humidity</h2>
                    <p class="text-3xl font-bold text-blue-400">{humidity}</p>
                </div>
            </div>
        </div>
    </main>
    <footer class="p-4 bg-gray-800 border-t border-gray-700 text-center text-sm">
        <p>&copy; 2024 Tent Camera. All rights reserved.</p>
    </footer>
</body>
</html>
"""

