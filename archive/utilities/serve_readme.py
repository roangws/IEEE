#!/usr/bin/env python3
"""
Simple server to preview README.md in the browser with beautiful styling
"""

import http.server
import socketserver
import webbrowser
import os
import threading
import time

PORT = 8080

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/README':
            self.path = '/preview_readme.html'
        return super().do_GET()

def start_server():
    """Start the web server"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n🌐 Server started at http://localhost:{PORT}")
        print("📄 Your README is being rendered with beautiful styling")
        print("🔄 Press Ctrl+C to stop the server\n")
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(1)
            webbrowser.open(f'http://localhost:{PORT}')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✅ Server stopped")

if __name__ == "__main__":
    start_server()
