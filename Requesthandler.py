from six.moves.BaseHTTPServer import BaseHTTPRequestHandler
from six.moves.urllib_parse import parse_qsl, urlparse


def parse_auth_response_url(url):
    query_s = urlparse(url).query
    form = dict(parse_qsl(query_s))
    return tuple(form.get(param) for param in ["state", "code"])


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.auth_code = self.server.error = None
        try:
            state, auth_code = parse_auth_response_url(self.path)
            self.server.state = state
            self.server.auth_code = auth_code
        except Exception as err:
            self.server.state = err.state
            self.server.error = err.error

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        if self.server.auth_code:
            status = "successful"
        elif self.server.error:
            status = "failed ({})".format(self.server.error)
        else:
            self._write("<html><body><h1>Invalid request</h1></body></html>")
            return

        self._write(f"""<html>
<script>
window.close()
</script>
<body>
<h1>Authentication status: {status}</h1>
This window can be closed.
</body>
</html>""")

    def _write(self, text):
        return self.wfile.write(text.encode("utf-8"))

    def log_message(self, format, *args):
        return
