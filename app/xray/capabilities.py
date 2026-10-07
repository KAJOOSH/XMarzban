"""Version-specific source inventory and explicit subscription capabilities."""
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def capabilities():
    schema = json.loads(Path(__file__).with_name("schema_v26_3_27.json").read_text())
    return {**schema,
            "managed_protocols": ["vmess", "vless", "trojan", "shadowsocks", "hysteria", "wireguard"],
            "static_protocols": ["http", "socks", "mixed", "tunnel", "dokodemo-door", "tun"],
            "transports": ["raw", "xhttp", "kcp", "ws", "httpupgrade", "grpc", "hysteria"],
            "removed_transports": ["http", "h2", "h3", "quic"],
            "reality_transports": ["raw", "xhttp", "grpc"],
            "wireguard_management": {"per_user_keys": True, "peer_changes": "core restart", "per_peer_traffic_accounting": False},
            "subscription_formats": {
                "v2ray-json": "Complete client streamSettings; server-only fields excluded",
                "v2ray": "Share-link parameters supported by the importing client; prefer JSON for advanced settings",
                "clash": "RAW, WS, gRPC; VMess, Trojan, Shadowsocks; no REALITY",
                "clash-meta": "RAW, WS, gRPC and native Hysteria 2; unrepresentable advanced settings omitted",
                "sing-box": "RAW, WS, gRPC, HTTPUpgrade and native Hysteria 2; unrepresentable advanced settings omitted",
                "outline": "Plain RAW Shadowsocks only",
            }}
