"""Real Xray client/server transport matrix, inside an isolated Docker container.

Run: python -m scripts.test_xray_26327
All requests target local TCP/UDP echo servers, never the public internet.
"""
import base64
import copy
import json
import os
import socket
import socketserver
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from scripts.init_xray_defaults import initialize

ROOT = Path(tempfile.mkdtemp(prefix="marzban-xray-tests-"))
initialize("xray_config.json", ROOT / "xray.json")
os.environ["XRAY_JSON"] = str(ROOT / "xray.json")
os.environ["SQLALCHEMY_DATABASE_URL"] = f"sqlite:///{ROOT / 'db.sqlite3'}"
os.environ["XRAY_EXECUTABLE_PATH"] = "/usr/local/bin/xray"

# Load library packages without starting the web application and its jobs.
import sys
import types
for name, directory in (("app", "app"), ("app.xray", "app/xray")):
    package = types.ModuleType(name)
    package.__path__ = [str(Path(directory).resolve())]
    sys.modules[name] = package
sys.modules["app"].xray = sys.modules["app.xray"]
from apscheduler.schedulers.background import BackgroundScheduler
sys.modules["app"].scheduler = BackgroundScheduler(timezone="UTC")
from app.utils import system
system.get_public_ip = lambda: "127.0.0.1"
system.get_public_ipv6 = lambda: "::1"

from app.xray.transport import (client_stream, subscription_stream, select_port,
                                supports_vision, validate_client_override)
from app.subscription.v2ray import V2rayJsonConfig, V2rayShareLink
from app.subscription.singbox import SingBoxConfiguration
from app.subscription.clash import ClashMetaConfiguration
from app.models.proxy import ProxyTypes, HysteriaSettings, ProxyHost
from app.xray.config import XRayConfig
from xray_api import XRay
from xray_api.types.account import HysteriaAccount

TEST_ID = "d37af3ab-20d8-466a-a4c4-3d7f9ea6aa11"
ACCOUNTS = {"vmess": {"id": TEST_ID}, "vless": {"id": TEST_ID},
            "trojan": {"password": "local-matrix-password"},
            "shadowsocks": {"password": "local-matrix-password", "method": "chacha20-ietf-poly1305"},
            "hysteria": {"auth": "local-matrix-hysteria"}}


class Echo(socketserver.BaseRequestHandler):
    def handle(self):
        while chunk := self.request.recv(65536):
            self.request.sendall(chunk)


class EchoServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class UDPEcho(socketserver.BaseRequestHandler):
    def handle(self):
        data, sock = self.request
        sock.sendto(data, self.client_address)


def wait_port(port, process=None):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise AssertionError(f"Xray exited with {process.returncode}")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=.2):
                return
        except OSError:
            time.sleep(.05)
    raise AssertionError(f"Port {port} never became ready")


def check_config(config):
    path = ROOT / "check.json"
    path.write_text(json.dumps(config))
    result = subprocess.run(["xray", "run", "-test", "-c", str(path)], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)


def socks_echo(port, username=None, password=None, target="127.0.0.1"):
    import socks
    with socks.socksocket() as conn:
        conn.set_proxy(socks.SOCKS5, "127.0.0.1", port, username=username, password=password)
        conn.settimeout(15)
        conn.connect((target, 18090))
        payload = b"marzban-xray-26327-echo:" + os.urandom(4096)
        conn.sendall(payload)
        received = bytearray()
        while len(received) < len(payload):
            part = conn.recv(len(payload) - len(received))
            if not part:
                break
            received.extend(part)
        assert bytes(received) == payload, "Proxy changed or lost payload bytes"


def socks_udp_echo(port, target="127.0.0.1"):
    import socks
    with socks.socksocket(type=socket.SOCK_DGRAM) as conn:
        conn.set_proxy(socks.SOCKS5, "127.0.0.1", port)
        conn.settimeout(10)
        payload = b"marzban-udp-echo:" + os.urandom(256)
        conn.sendto(payload, (target, 18090))
        data, _ = conn.recvfrom(4096)
        assert data == payload, "UDP payload changed or was lost"


class TransportProjectionTests(unittest.TestCase):
    def test_aliases(self):
        for old, new, settings in (("tcp", "raw", "tcpSettings"), ("splithttp", "xhttp", "splithttpSettings"), ("mkcp", "kcp", "kcpSettings"), ("websocket", "ws", "wsSettings")):
            with self.subTest(network=old):
                options = {"header": {"type": "none"}} if new == "raw" else {"mtu": 1280} if new == "kcp" else {"path": "/a"}
                projected = client_stream({"network": old, settings: options})
                self.assertEqual(projected["network"], new)
                self.assertEqual(projected[f"{new}Settings"], options)

    def test_server_secrets_never_exported(self):
        projected = client_stream({"network": "raw", "security": "reality", "sockopt": {"mark": 123},
                                   "realitySettings": {"privateKey": "SECRET", "mldsa65Seed": "SECRET",
                                                       "target": "secret:443", "publicKey": "public", "mldsa65Verify": "verify"}})
        self.assertNotIn("SECRET", json.dumps(projected))
        self.assertNotIn("sockopt", projected)
        projected = client_stream({"security": "tls", "tlsSettings": {"certificates": [{"key": ["SECRET"]}], "echServerKeys": "SECRET", "echConfigList": "public", "pinnedPeerCertSha256": "pin"}})
        self.assertNotIn("SECRET", json.dumps(projected))
        self.assertEqual(projected["tlsSettings"]["echConfigList"], "public")

    def test_invalid_removed_transports(self):
        for network in ("http", "h2", "h3", "quic", "invalid"):
            with self.subTest(network=network), self.assertRaises(ValueError):
                client_stream({"network": network})
        with self.assertRaises(ValueError):
            client_stream({"network": "ws", "security": "reality"})

    def test_xhttp_extra_overrides_and_nested_secrets(self):
        value = {"network": "xhttp", "xhttpSettings": {"host": "host", "path": "/path", "mode": "packet-up", "noGRPCHeader": False,
                 "extra": {"noGRPCHeader": True, "sessionKey": "custom", "downloadSettings": {"address": "down.example", "port": 443, "network": "raw", "security": "tls", "tlsSettings": {"echServerKeys": "SECRET"}}}}}
        original = copy.deepcopy(value)
        result = client_stream(value)
        self.assertTrue(result["xhttpSettings"]["noGRPCHeader"])
        self.assertEqual(result["xhttpSettings"]["downloadSettings"]["address"], "down.example")
        self.assertNotIn("SECRET", json.dumps(result))
        self.assertEqual(original, value)

    def test_override_rejects_private_keys_and_unknown_fields(self):
        for value in ({"grpcSettings": {"headers": {"User-Agent": "ignored"}}}, {"xhttpSettings": {"extra": {"scMaxConcurrentPosts": 3}}}, {"realitySettings": {"privateKey": "secret"}}, {"tlsSettings": {"certificates": []}}, {"xhttpSettings": {"downloadSettings": {"realitySettings": {"mldsa65Seed": "secret"}}}}):
            with self.assertRaises(ValueError):
                validate_client_override(value)

    def test_port_ranges_and_vision(self):
        for _ in range(50):
            self.assertIn(select_port("443,1000-1002"), {443, 1000, 1001, 1002})
        for value in ("0", "65536", "20-10"):
            with self.assertRaises(ValueError):
                select_port(value)
        self.assertTrue(supports_vision({"network": "raw", "tls": "reality"}))
        self.assertFalse(supports_vision({"network": "kcp", "tls": "tls"}))

    def test_hysteria_model_and_protobuf(self):
        self.assertEqual(ProxyTypes.Hysteria.settings_model, HysteriaSettings)
        settings = HysteriaSettings()
        previous = settings.auth
        settings.revoke()
        self.assertNotEqual(previous, settings.auth)
        message = HysteriaAccount(email="test", auth="abc").message
        self.assertEqual(message.type, "xray.proxy.hysteria.account.Account")
        self.assertEqual(message.value, b"\x0a\x03abc")


class LiveMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.echo = EchoServer(("127.0.0.1", 18090), Echo)
        threading.Thread(target=cls.echo.serve_forever, daemon=True).start()
        cls.udp_echo = socketserver.ThreadingUDPServer(("127.0.0.1", 18090), UDPEcho)
        threading.Thread(target=cls.udp_echo.serve_forever, daemon=True).start()
        config = json.loads((ROOT / "xray.json").read_text())
        config["routing"]["rules"] = [{"type": "field", "inboundTag": ["LOCAL WIREGUARD", "LOCAL TUN"], "outboundTag": "LOCAL_ECHO"}]
        config["outbounds"].append({"tag": "LOCAL_ECHO", "protocol": "freedom", "settings": {"redirect": "127.0.0.1:18090"}})
        for inbound in config["inbounds"]:
            if inbound["protocol"] in ACCOUNTS:
                inbound["settings"]["clients"] = [{"email": "matrix-user", **ACCOUNTS[inbound["protocol"]]}]
        cls.config = XRayConfig(config, api_port=19808)
        sys.modules["app.xray"].config = cls.config
        (ROOT / "server.json").write_text(cls.config.to_json())
        cls.log = open(ROOT / "server.log", "w+")
        cls.server = subprocess.Popen(["xray", "run", "-c", str(ROOT / "server.json")], stdout=cls.log, stderr=cls.log)
        try:
            wait_port(19808, cls.server)
            api = XRay("127.0.0.1", 19808)
            deadline = time.monotonic() + 10
            while True:
                try:
                    api.get_sys_stats(timeout=1)
                    break
                except Exception:
                    if time.monotonic() > deadline:
                        raise
                    time.sleep(.1)
        except Exception:
            cls.log.seek(0)
            raise AssertionError(cls.log.read())
        cls.credentials = json.loads((ROOT / "local-credentials.json").read_text())
        cls.results = []

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.server.wait(timeout=10)
        cls.echo.shutdown()
        cls.echo.server_close()
        cls.udp_echo.shutdown()
        cls.udp_echo.server_close()
        Path("/tmp/xray-26327-results.json").write_text(json.dumps(cls.results, indent=2))

    def client_outbound(self, inbound):
        inbound = copy.deepcopy(inbound)
        inbound.update(sni="localhost", host="localhost" if inbound["network"] in {"ws", "xhttp", "httpupgrade", "grpc"} else "",
                       fragment_setting="", noise_setting="", mux_enable=False, ais=False)
        if inbound["network"] == "grpc":
            inbound["path"] = "marzban"
        if inbound.get("sids"):
            inbound["sid"] = inbound["sids"][0]
        builder = V2rayJsonConfig()
        builder.add("matrix", "127.0.0.1", inbound, ACCOUNTS[inbound["protocol"]])
        outbound = json.loads(builder.render())[0]["outbounds"][0]
        # Local test cert is pinned, so TLS validation remains enabled.
        return inbound, outbound

    def run_client(self, tag, outbound, target="127.0.0.1", udp=False):
        config = {"log": {"loglevel": "info"}, "inbounds": [{"listen": "127.0.0.1", "port": 19090, "protocol": "socks", "settings": {"auth": "noauth", "udp": True}}], "outbounds": [outbound]}
        check_config(config)
        path = ROOT / "client.json"
        path.write_text(json.dumps(config))
        with open(ROOT / "client.log", "w+") as log:
            process = subprocess.Popen(["xray", "run", "-c", str(path)], stdout=log, stderr=log)
            try:
                wait_port(19090, process)
                socks_echo(19090, target=target)
                if udp:
                    socks_udp_echo(19090, target=target)
            except Exception as exc:
                log.seek(0)
                self.results.append({"tag": tag, "status": "failed", "reason": str(exc), "log": log.read()})
                raise
            finally:
                process.terminate()
                process.wait(timeout=10)
        self.results.append({"tag": tag, "status": "passed", "tcp": True, "udp": udp})

    def test_managed_protocol_transport_matrix(self):
        for inbound in self.config.inbounds:
            if inbound["protocol"] == "wireguard":
                continue  # Tested below with a WireGuard peer and TCP/UDP.
            with self.subTest(tag=inbound["tag"]):
                projected, outbound = self.client_outbound(inbound)
                encoded = json.dumps(outbound)
                for secret in (self.credentials["REALITY_PRIVATE_KEY"], "certificateFile", "keyFile"):
                    self.assertNotIn(secret, encoded)
                self.run_client(inbound["tag"], outbound, udp=inbound["protocol"] != "shadowsocks" or inbound["network"] == "raw")
                links = V2rayShareLink()
                links.add("matrix", "127.0.0.1", projected, ACCOUNTS[inbound["protocol"]])
                self.assertEqual(len(links.links), 0 if (inbound["protocol"] == "shadowsocks" and (inbound["network"] != "raw" or inbound["tls"] != "none" or inbound["header_type"] != "none")) or (inbound["network"] == "hysteria" and inbound["protocol"] != "hysteria") else 1)
                if inbound["network"] == "kcp" and inbound["protocol"] in {"vmess", "vless", "trojan"}:
                    query = parse_qs(urlsplit(links.links[0]).query)
                    self.assertEqual(query["mtu"], ["1350"])
                    self.assertEqual(query["tti"], ["50"])
                    self.assertNotIn("mkcp-legacy", query["fm"][0])

    def test_hysteria_api_add_remove(self):
        api = XRay("127.0.0.1", 19808)
        api.add_inbound_user("HYSTERIA 2", HysteriaAccount(email="api-user", auth="api-auth"))
        inbound = self.config.inbounds_by_tag["HYSTERIA 2"]
        _, outbound = self.client_outbound(inbound)
        outbound["streamSettings"]["hysteriaSettings"]["auth"] = "api-auth"
        self.run_client("HYSTERIA API add", outbound)
        api.remove_inbound_user("HYSTERIA 2", "api-user")
        # A fresh connection must reject the removed identity.
        with self.assertRaises(Exception):
            self.run_client("HYSTERIA API removed (expected rejection)", outbound)
        self.assertIn("auth failed", self.results[-1]["log"])
        self.results[-1] = {"tag": "HYSTERIA API removed", "status": "passed", "expected": "authentication rejected"}

    def test_static_protocols(self):
        password = self.credentials["LOCAL_PROXY_PASSWORD"]
        for port in (12082, 12083):
            with self.subTest(port=port):
                socks_echo(port, "local", password)
                self.results.append({"tag": "LOCAL SOCKS" if port == 12082 else "LOCAL MIXED", "status": "passed", "tcp": True})
        for port in (12084, 12085):
            with socket.create_connection(("127.0.0.1", port), timeout=5) as conn:
                conn.sendall(b"tunnel-echo")
                self.assertEqual(conn.recv(100), b"tunnel-echo")
                self.results.append({"tag": "LOCAL TUNNEL" if port == 12084 else "LOCAL DOKODEMO", "status": "passed", "tcp": True})
        for port, security in ((12081, "none"), (12080, "tls")):
            outbound = {"protocol": "http", "settings": {"servers": [{"address": "127.0.0.1", "port": port, "users": [{"user": "local", "pass": password}]}]},
                        "streamSettings": {"network": "raw", "security": security}}
            if security == "tls":
                source = self.config.get_inbound("LOCAL HTTPS")["streamSettings"]
                outbound["streamSettings"] = client_stream(source)
            self.run_client(f"LOCAL HTTP {security}", outbound)
        outbound = {"protocol": "wireguard", "settings": {"secretKey": self.credentials["WIREGUARD_CLIENT_PRIVATE_KEY"], "address": ["10.77.0.2/32"], "noKernelTun": True,
                    "peers": [{"publicKey": self.credentials["WIREGUARD_PUBLIC_KEY"], "endpoint": "127.0.0.1:12086", "allowedIPs": ["0.0.0.0/0"]}]}}
        self.run_client("LOCAL WIREGUARD", outbound, target="10.77.0.1", udp=True)
        self.assertTrue(Path("/sys/class/net/marzban0").exists(), "TUN interface must be created")
        subprocess.run(["ip", "address", "add", "198.18.0.1/32", "dev", "marzban0"], check=True)
        subprocess.run(["ip", "link", "set", "marzban0", "up"], check=True)
        subprocess.run(["ip", "route", "add", "198.18.0.2/32", "dev", "marzban0"], check=True)
        with socket.create_connection(("198.18.0.2", 18090), timeout=10) as conn:
            conn.sendall(b"tun-tcp-echo")
            self.assertEqual(conn.recv(100), b"tun-tcp-echo")
        with socket.socket(type=socket.SOCK_DGRAM) as conn:
            conn.settimeout(10)
            conn.sendto(b"tun-udp-echo", ("198.18.0.2", 18090))
            self.assertEqual(conn.recv(100), b"tun-udp-echo")
        self.results.append({"tag": "LOCAL TUN", "status": "passed", "tcp": True, "udp": True})


if __name__ == "__main__":
    unittest.main(verbosity=2)
