"""Xray v26.3.27 transport projection from server to subscription clients.

Keep transport objects intact, but never project server TLS/REALITY secrets or
server socket options. Explicit host overrides are client-side configuration.
"""
from copy import deepcopy
import json
from pathlib import Path
from random import choice, randint


ALIASES = {"tcp": "raw", "splithttp": "xhttp", "mkcp": "kcp", "websocket": "ws"}
NETWORKS = {"raw", "xhttp", "kcp", "ws", "httpupgrade", "grpc", "hysteria"}
REMOVED = {"http", "h2", "h3", "quic"}
SETTINGS_KEYS = {"raw": ("rawSettings", "tcpSettings"),
                 "xhttp": ("xhttpSettings", "splithttpSettings"),
                 "kcp": ("kcpSettings",), "ws": ("wsSettings",),
                 "httpupgrade": ("httpupgradeSettings",),
                 "grpc": ("grpcSettings",), "hysteria": ("hysteriaSettings",)}
TLS_CLIENT_FIELDS = {"serverName", "alpn", "fingerprint",
                     "enableSessionResumption", "disableSystemRoot", "minVersion",
                     "maxVersion", "cipherSuites", "curvePreferences",
                     "pinnedPeerCertSha256", "verifyPeerCertByName",
                     "echConfigList", "echForceQuery", "echSockopt"}
REALITY_CLIENT_FIELDS = {"fingerprint", "serverName", "password", "publicKey",
                         "shortId", "spiderX", "mldsa65Verify"}
TRANSPORT_OBJECTS = {"raw": "TCPConfig", "ws": "WebSocketConfig", "httpupgrade": "HttpUpgradeConfig",
                     "grpc": "GRPCConfig", "xhttp": "SplitHTTPConfig", "kcp": "KCPConfig", "hysteria": "HysteriaConfig"}
_SOURCE_OBJECTS = json.loads(Path(__file__).with_name("schema_v26_3_27.json").read_text())["objects"]
TRANSPORT_FIELDS = {network: {f["json"] for f in _SOURCE_OBJECTS[name]["fields"]}
                    for network, name in TRANSPORT_OBJECTS.items()}


CLIENT_PROTOCOL_FIELDS = {
    "vmess": {"security", "experiments", "level", "email"},
    "vless": {"encryption", "reverse", "seed", "testpre", "testseed", "level", "email"},
    "trojan": {"level", "email"}, "shadowsocks": {"level", "email", "uot"},
    "wireguard": {"mtu", "workers", "reserved", "noKernelTun", "domainStrategy"},
    "hysteria": set(),
}


def canonical_network(network):
    return ALIASES.get(network, network)


def transport_settings(stream):
    network = canonical_network(stream.get("network", "raw"))
    for key in SETTINGS_KEYS.get(network, (f"{network}Settings",)):
        if key in stream:
            return deepcopy(stream[key])
    return {}


def merge_settings(base, override):
    result = deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_settings(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def client_stream(stream):
    network = canonical_network(stream.get("network", "raw"))
    if network in REMOVED:
        raise ValueError(f"Xray v26.3.27 removed transport {network}; use XHTTP instead")
    if network not in NETWORKS:
        raise ValueError(f"Unknown Xray transport: {network}")
    security = stream.get("security", "none")
    if security not in {"none", "tls", "reality"}:
        raise ValueError(f"Unknown or removed Xray security: {security}")
    if security == "reality" and network not in {"raw", "xhttp", "grpc"}:
        raise ValueError("REALITY only supports RAW, XHTTP and gRPC in v26.3.27")
    result = {"network": network, "security": security}
    transport = transport_settings(stream)
    transport = {key:value for key,value in transport.items() if key in TRANSPORT_FIELDS[network]}
    if network == "kcp" and (transport.get("header") is not None or transport.get("seed") is not None):
        raise ValueError("mKCP header and seed were removed; configure finalmask.udp instead")
    transport.pop("acceptProxyProtocol", None)
    if network == "raw":
        transport.get("header", {}).pop("response", None)
    if network == "hysteria":
        for field in ("masquerade", "udpIdleTimeout"):
            transport.pop(field, None)
        transport.setdefault("version", 2)
    if network == "xhttp":
        # Xray's extra replaces the top-level advanced fields, not vice versa.
        extra = transport.pop("extra", None)
        if extra is not None:
            transport = {key: transport[key] for key in ("host", "path", "mode") if key in transport} | deepcopy(extra)
            transport = {key:value for key,value in transport.items() if key in TRANSPORT_FIELDS[network]}
        if "downloadSettings" in transport:
            transport["downloadSettings"] = project_explicit_stream(transport["downloadSettings"])
        for field in ("scMaxBufferedPosts", "serverMaxHeaderBytes"):
            transport.pop(field, None)
    result[f"{network}Settings"] = transport
    if security in {"tls", "reality"}:
        fields = TLS_CLIENT_FIELDS if security == "tls" else REALITY_CLIENT_FIELDS
        result[f"{security}Settings"] = {key: deepcopy(value) for key, value in
                                          (stream.get(f"{security}Settings") or {}).items() if key in fields}
    if "finalmask" in stream:
        result["finalmask"] = deepcopy(stream["finalmask"])
    return result


def project_explicit_stream(stream):
    """Sanitize an explicitly configured client stream, retaining dial options."""
    result = client_stream(stream)
    for key in ("address", "port", "sockopt"):
        if key in stream:
            result[key] = deepcopy(stream[key])
    return result


def subscription_stream(inbound, generated):
    source = deepcopy(inbound.get("client_stream", {}))
    network = canonical_network(inbound["network"])
    # Existing scalar host fields override inherited path/host/security.
    result = merge_settings(generated, source)
    result["network"] = network
    result["security"] = inbound["tls"]
    options = result.setdefault(f"{network}Settings", {})
    if network in {"ws", "httpupgrade", "xhttp"}:
        options.update(path=inbound["path"], host=inbound["host"])
        options.get("headers", {}).pop("Host", None)
    elif network == "grpc":
        options.update(serviceName=inbound["path"], authority=inbound["host"])
    elif network == "kcp":
        options.pop("seed", None)
        options.pop("header", None)
    elif network == "raw" and inbound["header_type"] == "http":
        request = options.setdefault("header", {}).setdefault("request", {})
        request["path"] = [inbound["path"] or "/"]
        request.setdefault("headers", {})["Host"] = [inbound["host"]]
    security = inbound["tls"]
    if security in {"tls", "reality"}:
        tls = result.setdefault(f"{security}Settings", {})
        for key, value in (("serverName", inbound.get("sni")), ("fingerprint", inbound.get("fp"))):
            if value:
                tls[key] = value
        if inbound.get("alpn") and security == "tls":
            tls["alpn"] = inbound["alpn"].split(",")
        if security == "reality":
            tls.update(publicKey=inbound.get("pbk", ""), shortId=inbound.get("sid", ""))
            if inbound.get("spx"):
                tls["spiderX"] = inbound["spx"]
    for key in ("tlsSettings", "realitySettings"):
        if key != f"{security}Settings":
            result.pop(key, None)
    result = merge_settings(result, inbound.get("xray_stream_settings"))
    return project_explicit_stream(result)


def select_port(port):
    if isinstance(port, int):
        if not 1 <= port <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return port
    ranges = []
    for item in str(port).split(","):
        values = item.strip().split("-")
        low, high = (int(values[0]), int(values[-1]))
        if len(values) > 2 or not 1 <= low <= high <= 65535:
            raise ValueError(f"Invalid port range: {item}")
        ranges.append((low, high))
    low, high = choice(ranges)
    return randint(low, high)


def supports_vision(inbound):
    return (canonical_network(inbound.get("network", "raw")) == "raw"
            and inbound.get("tls") in {"tls", "reality"}
            and inbound.get("header_type") != "http")


def validate_client_override(value):
    allowed = {"network", "security", "address", "port", "sockopt", "finalmask",
               "tlsSettings", "realitySettings"} | {key for keys in SETTINGS_KEYS.values() for key in keys}
    if set(value) - allowed:
        raise ValueError("Unknown client streamSettings fields")
    if "network" in value and canonical_network(value["network"]) not in NETWORKS:
        raise ValueError("Unsupported client transport for Xray v26.3.27")
    for key, fields in (("tlsSettings", TLS_CLIENT_FIELDS), ("realitySettings", REALITY_CLIENT_FIELDS)):
        if key in value and (not isinstance(value[key], dict) or set(value[key]) - fields):
            raise ValueError(f"{key} contains unknown or server-only fields")
    for network, keys in SETTINGS_KEYS.items():
        for key in keys:
            if key in value and isinstance(value[key], dict) and set(value[key]) - TRANSPORT_FIELDS[network]:
                raise ValueError(f"{key} contains fields unsupported by Xray v26.3.27")
    for key in allowed - {"network", "security", "address", "port"}:
        if key in value and not isinstance(value[key], dict):
            raise ValueError(f"{key} must be an object")
    for key in ("xhttpSettings", "splithttpSettings"):
        options = value.get(key, {})
        if isinstance(options.get("extra"), dict):
            options = options["extra"]
        if set(options) - TRANSPORT_FIELDS["xhttp"]:
            raise ValueError("XHTTP extra contains fields unsupported by Xray v26.3.27")
        if "downloadSettings" in options:
            validate_client_override(options["downloadSettings"])


def portable_hysteria(inbound):
    """Return Hysteria 2 settings representable in other client cores."""
    stream = subscription_stream(inbound, {})
    masks = stream.get("finalmask", {})
    # Foreign cores only support Salamander, not Xray's other final masks.
    if masks.get("tcp") or masks.get("quicParams") or len(masks.get("udp", [])) > 1:
        return None
    obfs = None
    for mask in masks.get("udp", []):
        if mask.get("type") != "salamander":
            return None
        obfs = mask.get("settings", {}).get("password")
        if not obfs:
            return None
    tls = stream.get("tlsSettings", {})
    if any(tls.get(key) for key in ("echConfigList", "echSockopt", "pinnedPeerCertSha256", "verifyPeerCertByName")):
        return None
    return stream, obfs


def portable_legacy_stream(inbound):
    """Do not silently drop Xray-only verification or transport options."""
    stream = subscription_stream(inbound, {})
    tls = stream.get("tlsSettings", {})
    if any(value for key, value in tls.items() if key not in {"serverName", "alpn", "fingerprint", "allowInsecure"}):
        return False
    reality = stream.get("realitySettings", {})
    if any(reality.get(key) for key in ("mldsa65Verify", "spiderX")):
        return False
    options = stream.get(f"{stream['network']}Settings", {})
    allowed = {"raw": {"header"}, "ws": {"path", "host", "headers"},
               "httpupgrade": {"path", "host", "headers"}, "grpc": {"serviceName", "authority", "multiMode"}}
    if any(value for key, value in options.items() if key not in allowed.get(stream["network"], set())):
        return False
    return True
