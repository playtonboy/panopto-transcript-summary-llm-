"""A tiny fake LM Studio server for the integration tests. It answers like the real API, but instantly and always the same."""

import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class FakeLMStudio(BaseHTTPRequestHandler):
    delay_s = 0   # seconds to wait before answering (> 0 imitates a slow model)
    status = 200  # HTTP status to answer with (500 imitates a crashed server)

    def log_message(self, *args):  # keep the test output quiet
        pass

    def _send(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # GET /v1/models, used by llm_client.is_server_running()
        self._send(200, {"data": [{"id": "local-model"}]})

    def do_POST(self):  # POST /v1/chat/completions, used by llm_client.chat()
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        prompt = request["messages"][-1]["content"]
        time.sleep(self.delay_s)
        if self.status != 200:
            return self._send(self.status, {"error": "fake server error"})
        self._send(200, {"choices": [{"message": {"content": fake_answer(prompt)}}]})


def fake_answer(prompt: str) -> str:
    """Pick a fixed answer based on which of our prompts was sent."""
    if prompt.startswith("List the main topics"):
        return "- Software testing\n- Unit and integration tests"
    if prompt.startswith("Find everything"):
        return "- Hand in Task 5 on 6 November"
    count = re.search(r"exactly (\d+) points", prompt)
    if count:
        return "\n".join(f"{i}. Fake point {i}." for i in range(1, int(count.group(1)) + 1))
    return "Fake notes."


def start_fake_server(delay_s=0, status=200):
    """Start the fake server in the background and return it with its base URL."""
    handler = type("Handler", (FakeLMStudio,), {"delay_s": delay_s, "status": status})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)  # port 0 = any free port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}/v1"