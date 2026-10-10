import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from discovery import Discovery, apply_config, endpoint, parse_instances, render, resolve_ipv4


def instance(address="127.0.0.1", port=8123, status="passing"):
    return {"Service": {"Service": "auth-service", "Address": address, "Port": port},
            "Node": {"Address": "127.0.0.2"}, "Checks": [{"Status": status}]}


class DiscoveryTests(unittest.TestCase):
    def test_internal_auth_routes_are_blocked_with_and_without_upstreams(self):
        for config in (render({}), render({"auth-service": ["127.0.0.1:8001"]}),
                       Path(__file__).resolve().parents[1].joinpath("nginx.conf").read_text()):
            self.assertIn("location ^~ /auth/internal/ { return 404", config)
            self.assertIn("location = /auth/internal { return 404", config)

    @patch("discovery.subprocess.run")
    def test_ipv4_hostname_resolution_is_bounded_validated_and_deduplicated(self, run):
        run.return_value.stdout = json.dumps({"dualstack.test": ["127.0.0.1", "127.0.0.1", "127.0.0.2"]})
        records = [instance("dualstack.test"), instance("dualstack.test"), instance("::1")]
        servers = parse_instances(records, "auth-service", "ipv4", dns_timeout=0.5)
        self.assertEqual(servers, ["127.0.0.1:8123", "127.0.0.2:8123"])
        self.assertEqual(run.call_count, 1)
        self.assertEqual(json.loads(run.call_args.kwargs["input"]), ["dualstack.test"])
        self.assertEqual(run.call_args.kwargs["timeout"], 0.5)
        config = render({"auth-service": servers})
        self.assertNotIn("dualstack.test", config)
        self.assertNotIn("[::1]", config)

    @patch("discovery.subprocess.run")
    def test_ipv4_literals_skip_dns_and_ipv6_only_instances_fail_closed(self, run):
        self.assertEqual(parse_instances([instance()], "auth-service", "ipv4"), ["127.0.0.1:8123"])
        self.assertEqual(parse_instances([instance("::1")], "auth-service", "ipv4"), [])
        run.assert_not_called()

    @patch("discovery.subprocess.run")
    def test_resolution_timeout_failure_and_invalid_results_are_safe(self, run):
        for failure in [subprocess.TimeoutExpired("resolver", 0.1),
                        subprocess.CalledProcessError(1, "resolver"), OSError("DNS unavailable")]:
            run.side_effect = failure
            with self.subTest(failure=failure), self.assertRaises(OSError):
                resolve_ipv4({"dualstack.test"}, 0.1)
        run.side_effect = None
        for data in ["not json", "[]", "{}", '{"dualstack.test":[]}',
                     '{"dualstack.test":["::1"]}', '{"dualstack.test":["x; return 200"]}',
                     '{"dualstack.test":[123]}', " " * 262145]:
            run.return_value.stdout = data
            with self.subTest(data=data[:80]), self.assertRaises(OSError):
                resolve_ipv4({"dualstack.test"}, 0.1)

    @patch("discovery.urlopen")
    @patch("discovery.subprocess.run")
    def test_dns_failure_uses_only_bounded_last_good_ipv4_cache(self, run, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = json.dumps([instance("dualstack.test")]).encode()
        run.return_value.stdout = '{"dualstack.test":["127.0.0.1"]}'
        clock = [10]
        discovery = Discovery("http://registry", stale_ttl=5, clock=lambda: clock[0], ip_family="ipv4")
        self.assertEqual(discovery.refresh_one("auth-service"), ["127.0.0.1:8123"])
        run.side_effect = subprocess.TimeoutExpired("resolver", 0.1)
        clock[0] = 14
        self.assertEqual(discovery.refresh_one("auth-service"), ["127.0.0.1:8123"])
        clock[0] = 15
        self.assertEqual(discovery.refresh_one("auth-service"), [])
        run.side_effect = None
        run.return_value.stdout = '{"dualstack.test":["127.0.0.2"]}'
        self.assertEqual(discovery.refresh_one("auth-service"), ["127.0.0.2:8123"])

    def test_invalid_family_and_dns_timeout_are_rejected(self):
        for family in ["IPv4", "ipv6", "", "unexpected"]:
            with self.subTest(family=family), self.assertRaises(ValueError):
                Discovery("http://registry", ip_family=family)
        for timeout in [0, -1, float("nan"), float("inf"), 11]:
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                Discovery("http://registry", dns_timeout=timeout)

    @patch("discovery.IPV4_LOOKUP", "import time; time.sleep(60)")
    def test_stalled_resolver_process_is_terminated_at_deadline(self):
        with self.assertRaises(OSError) as caught:
            resolve_ipv4({"dualstack.test"}, 0.1)
        self.assertIsInstance(caught.exception.__cause__, subprocess.TimeoutExpired)

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
