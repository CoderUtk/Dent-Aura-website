#!/usr/bin/env python3
"""Local dev server that mimics how Netlify serves this site.

`python -m http.server` is not enough: the site links internally without file
extensions (/fees, /services/root-canal-treatment), which Netlify resolves to
the matching .html file. This server does the same, and applies the headers
declared in netlify.toml so caching behaviour matches production.

    python scripts/serve.py [--port 8000] [--host 127.0.0.1]
"""
import argparse
import mimetypes
import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Not in the Windows mimetype registry, but Netlify serves these correctly.
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/avif", ".avif")
mimetypes.add_type("image/svg+xml", ".svg")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}
ASSET_CACHE = "public, max-age=31536000, immutable"


class NetlifyLikeHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        local = super().translate_path(path)
        if os.path.isdir(local):
            index = os.path.join(local, "index.html")
            if os.path.exists(index):
                return index
        elif not os.path.exists(local):
            # Pretty URL: /fees -> fees.html, /services/x -> services/x.html
            candidate = local + ".html"
            if os.path.exists(candidate):
                return candidate
        return local

    def end_headers(self):
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        if self.path.startswith("/assets/"):
            self.send_header("Cache-Control", ASSET_CACHE)
        else:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def send_error(self, code, message=None, explain=None):
        # Netlify serves 404.html when present; fall back to the default page.
        page = os.path.join(ROOT, "404.html")
        if code == 404 and os.path.exists(page):
            with open(page, "rb") as fh:
                body = fh.read()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
            return
        super().send_error(code, message, explain)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    handler = partial(NetlifyLikeHandler, directory=ROOT)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print("Serving %s at http://%s:%d/  (Ctrl+C to stop)" % (ROOT, args.host, args.port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
        server.server_close()


if __name__ == "__main__":
    main()
