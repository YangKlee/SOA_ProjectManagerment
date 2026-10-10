import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from discovery import DEFAULT_CORS_ORIGINS, Discovery, apply_config, endpoint, parse_allowed_origins, parse_instances, render


def instance(address="127.0.0.1", port=8123, status="passing"):
    return {"Service": {"Service": "auth-service", "Address": address, "Port": port},
            "Node": {"Address": "127.0.0.2"}, "Checks": [{"Status": status}]}


class DiscoveryTests(unittest.TestCase):
    def test_cors_origin_parser_accepts_exact_origins_and_explicit_empty_allowlist(self):
        self.assertEqual(parse_allowed_origins(""), ())
        self.assertEqual(parse_allowed_origins("  "), ())
        self.assertEqual(parse_allowed_origins("https://portal.example.com, http://[::1]:5173,https://portal.example.com"),
                         ("http://[::1]:5173", "https://portal.example.com"))

    def test_cors_origin_parser_rejects_wildcards_paths_and_nginx_injection(self):
        invalid = ["*", "null", "https://*.example.com", "ftp://example.com", "http://example.com/",
                   "http://example.com/path", "http://user@example.com", "http://example.com?x=1",
                   "http://example.com#fragment", "http://example.com:0", "http://example.com:65536",
                   "http://example.com;return 200", 'http://example.com"', "http://$host",
                   "http://example.com\nreturn 200", "http://-bad.example", "http://example..com",
                   "http://[invalid]", "http://localhost:5173,", ",http://localhost:5173",
                   ",".join(f"https://site{i}.example" for i in range(65))]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_allowed_origins(value)

    def test_cors_policy_survives_bootstrap_and_dynamic_route_changes(self):
        for instances in [{}, {"auth-service": ["127.0.0.1:8123"]}, {"auth-service": ["127.0.0.1:9123"]}]:
            config = render(instances, ("https://portal.example.com",))
            self.assertIn('"https://portal.example.com" "https://portal.example.com";', config)
            self.assertNotIn("localhost:5173", config)
            self.assertIn('add_header Access-Control-Allow-Origin $cors_origin always;', config)
            self.assertIn('add_header Vary "Origin" always;', config)
            self.assertEqual(config.count('if ($cors_preflight = 1) { return 204; }'), 4)
            self.assertIn("proxy_hide_header Access-Control-Allow-Origin;", config)
            self.assertNotIn("add_header Access-Control-Allow-Credentials", config)

    def test_cors_default_and_disabled_policy_and_bootstrap_file(self):
        config = render({})
        for origin in DEFAULT_CORS_ORIGINS:
            self.assertIn(f'"{origin}" "{origin}";', config)
            self.assertNotIn(origin, render({}, ()))
        bootstrap = Path(__file__).resolve().parents[1] / "nginx.conf"
        self.assertEqual(bootstrap.read_text(), config)

    def test_only_healthy_instances_deduplicated_and_node_fallback(self):
        self.assertEqual(parse_instances([instance(), instance(), instance(status="critical"),
                                         instance(address="")], "auth-service"),
                         ["127.0.0.1:8123", "127.0.0.2:8123"])

    def test_addresses_and_ports_cannot_inject_nginx_directives(self):
        for address, port in [("a; return 200", 80), ("x\nserver y", 80),
                              ("/tmp/socket", 80), ("x:123", 80), ("a", True),
                              ("a", "80"), ("a", 0), ("a", 65536), ("", 80)]:
            with self.subTest(address=address, port=port), self.assertRaises(ValueError):
                endpoint(address, port)
        self.assertEqual(endpoint("::1", 80), "[::1]:80")
        self.assertEqual(endpoint("host.docker.internal", 8001), "host.docker.internal:8001")

    def test_malformed_and_wrong_service_responses_rejected(self):
        for payload in [{}, [None], [{"Service": {"Service": "other"}}]]:
            with self.subTest(payload=payload), self.assertRaises((ValueError, TypeError)):
                parse_instances(payload, "auth-service")

    @patch("discovery.urlopen")
    def test_http_contract_uses_passing_token_and_timeout(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = json.dumps([instance()]).encode()
        discovery = Discovery("http://registry:8500", timeout=0.5, token="test-only-token")
        self.assertEqual(discovery.fetch("auth-service"), ["127.0.0.1:8123"])
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://registry:8500/v1/health/service/auth-service?passing=true")
        self.assertEqual(request.get_header("X-consul-token"), "test-only-token")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 0.5)

    def test_outage_cache_expires_and_empty_success_clears_it_immediately(self):
        clock = [10]
        discovery = Discovery("http://registry", stale_ttl=5, clock=lambda: clock[0])
        with patch.object(discovery, "fetch", return_value=["127.0.0.1:8123"]):
            self.assertEqual(discovery.refresh_one("auth-service"), ["127.0.0.1:8123"])
        with patch.object(discovery, "fetch", side_effect=URLError("offline")):
            clock[0] = 14
            self.assertTrue(discovery.refresh_one("auth-service"))
            clock[0] = 15
            self.assertEqual(discovery.refresh_one("auth-service"), [])
        with patch.object(discovery, "fetch", return_value=[]):
            self.assertEqual(discovery.refresh_one("auth-service"), [])

    def test_registry_unavailable_at_start_fails_closed(self):
        discovery = Discovery("http://registry")
        with patch.object(discovery, "fetch", side_effect=TimeoutError):
            self.assertEqual(set(tuple(v) for v in discovery.refresh().values()), {()})

    def test_instance_change_updates_config_without_static_fallback(self):
        old = render({"auth-service": ["127.0.0.1:8123"]})
        new = render({"auth-service": ["127.0.0.1:9123"]})
        self.assertNotEqual(old, new)
        self.assertNotIn("host.docker.internal", new)
        self.assertIn("proxy_next_upstream off;", new)
        self.assertIn("proxy_set_header Authorization $http_authorization;", new)

    @patch("discovery.subprocess.run")
    def test_failed_validation_or_reload_preserves_previous_config(self, run):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "nginx.conf"
            path.write_text("previous")
            run.side_effect = subprocess.CalledProcessError(1, "nginx")
            with self.assertRaises(subprocess.CalledProcessError):
                apply_config("new", path)
            self.assertEqual(path.read_text(), "previous")
            run.side_effect = [None, subprocess.CalledProcessError(1, "nginx")]
            with self.assertRaises(subprocess.CalledProcessError):
                apply_config("new", path)
            self.assertEqual(path.read_text(), "previous")

    @patch("discovery.subprocess.run")
    def test_unchanged_configuration_does_not_reload(self, run):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "nginx.conf"
            path.write_text("same")
            self.assertFalse(apply_config("same", path))
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
