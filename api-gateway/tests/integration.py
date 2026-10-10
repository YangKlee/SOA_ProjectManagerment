"""Run inside the gateway image; isolated mock registry/backends, no real Consul."""
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import unittest

STATE = {"healthy": True, "registry_error": False, "port": None, "writes": []}


class Backend(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def handle_request(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        if self.command == "POST":
            STATE["writes"].append(self.server.server_port)
        payload = json.dumps({"path": self.path, "body": body,
                              "authorization": self.headers.get("Authorization"),
                              "request_id": self.headers.get("X-Request-ID"),
                              "port": self.server.server_port}).encode()
        self.send_response(502 if self.path == "/fail-write" else 200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = handle_request
    do_POST = handle_request


class Registry(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.send_response(503 if STATE["registry_error"] else 200)
        self.end_headers()
        name = self.path.split("/")[-1].split("?")[0]
        ports = STATE["port"] if isinstance(STATE["port"], list) else [STATE["port"]]
        result = [{"Service": {"Service": name, "Address": "127.0.0.1", "Port": port},
                   "Node": {"Address": "127.0.0.1"}, "Checks": [{"Status": "passing"}]}
                  for port in ports] if STATE["healthy"] else []
        self.wfile.write(json.dumps(result).encode())


def server(handler):
    result = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=result.serve_forever, daemon=True).start()
    return result


def request(path, method="GET", body=None, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", 80, timeout=2)
    try:
        connection.request(method, path, body, headers or {})
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()


def eventually(check, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if check():
                return
        except (OSError, ValueError):
            pass
        time.sleep(0.1)
    raise AssertionError("Expected routing state did not arrive")


class GatewayIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = server(Backend)
        cls.b = server(Backend)
        cls.registry = server(Registry)
        STATE["port"] = cls.a.server_port
        STATE["registry_error"] = True
        environment = dict(os.environ, CONSUL_URL=f"http://127.0.0.1:{cls.registry.server_port}",
                           CONSUL_REFRESH_SECONDS="0.2", CONSUL_TIMEOUT_SECONDS="0.2",
                           CONSUL_STALE_TTL_SECONDS="1")
        cls.worker = subprocess.Popen(["/opt/gateway/entrypoint.sh"], env=environment,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        eventually(lambda: request("/health/")[0] == 200)
        if request("/auth/health/")[0] != 503:
            raise AssertionError("Bootstrap must fail closed when registry is unavailable")
        STATE["registry_error"] = False
        eventually(lambda: request("/auth/health/")[0] == 200)

    @classmethod
    def tearDownClass(cls):
        cls.worker.terminate()
        cls.worker.wait(timeout=15)
        for item in [cls.a, cls.b, cls.registry]:
            item.shutdown()
            item.server_close()

    def setUp(self):
        STATE.update(healthy=True, registry_error=False, port=self.a.server_port, writes=[])
        eventually(lambda: request("/auth/probe")[1].get("port") == self.a.server_port)

    def test_all_prefixes_preserve_query_and_authorization(self):
        for prefix in ["auth", "academic", "registrations", "topics"]:
            status, payload = request(f"/{prefix}/api/items/?page=2", headers={"Authorization": "Bearer fake-test-token"})
            self.assertEqual(status, 200)
            self.assertEqual(payload["path"], "/api/items/?page=2")
            self.assertEqual(payload["authorization"], "Bearer fake-test-token")
            self.assertTrue(payload["request_id"])

    def test_instance_port_changes_without_restart(self):
        STATE["port"] = self.b.server_port
        eventually(lambda: request("/academic/api/items/")[1].get("port") == self.b.server_port)

    def test_multiple_instances_and_no_write_replay(self):
        STATE["port"] = [self.a.server_port, self.b.server_port]
        seen = set()
        def both():
            seen.add(request("/auth/probe")[1].get("port"))
            return seen == {self.a.server_port, self.b.server_port}
        eventually(both)
        status, _ = request("/auth/fail-write", "POST", "payload")
        self.assertEqual(status, 503)
        self.assertEqual(len(STATE["writes"]), 1)

    def test_no_healthy_instance_returns_json_503(self):
        STATE["healthy"] = False
        eventually(lambda: request("/auth/login/")[0] == 503)
        self.assertEqual(request("/health/")[0], 200)

    def test_registry_outage_expires_cache_then_recovers(self):
        STATE["registry_error"] = True
        eventually(lambda: request("/academic/api/items/")[0] == 503)
        STATE["registry_error"] = False
        eventually(lambda: request("/academic/api/items/")[0] == 200)

    def test_unknown_route_is_safe_404(self):
        self.assertEqual(request("/not-a-service/"), (404, {"detail": "Not found."}))


if __name__ == "__main__":
    unittest.main()
