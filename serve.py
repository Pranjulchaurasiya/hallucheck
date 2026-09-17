"""Lightweight HTTP server for the Hallucheck Stitch UI Dashboard.

Run:
    python serve.py
Then open http://localhost:8080 in your browser.
"""

import os
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json

from urllib.parse import urlparse

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class CustomHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Strip query string and fragments for routing
        clean_path = urlparse(path).path
        if clean_path in ["", "/", "/index.html"]:
            return os.path.join(DIRECTORY, "ui", "index.html")
        elif clean_path.startswith("/ui/"):
            return os.path.join(DIRECTORY, clean_path.lstrip("/"))
        elif clean_path in ["/style.css", "/app.js"]:
            return os.path.join(DIRECTORY, "ui", clean_path.lstrip("/"))
        elif clean_path == "/findings.json":
            return os.path.join(DIRECTORY, "findings.json")
        elif clean_path == "/report.md":
            return os.path.join(DIRECTORY, "report.md")
        return super().translate_path(clean_path)


def run_server():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, CustomHandler)
    url = f"http://localhost:{PORT}"
    print(f"\n=======================================================")
    print(f"  [Hallucheck] Stitch UI Dashboard running at:")
    print(f"     {url}")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
