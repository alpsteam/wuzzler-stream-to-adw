import http.server
import socketserver

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/stream-to-adw.log'
            self.send_header('Content-type', 'text/html')
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

# Create an object of the above class
handler_object = MyHttpRequestHandler

PORT = 8081
my_server = socketserver.TCPServer(("", PORT), handler_object)

print("Starting webserver to host logs...")
# Start the server
my_server.serve_forever()
