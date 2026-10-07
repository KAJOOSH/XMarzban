"""Materialize the default Xray presets using per-installation secrets.

Never overwrite an existing initialized config, certificate or credentials.
"""
import argparse
import base64
import hashlib
import json
import secrets
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, x25519
from cryptography.x509.oid import NameOID


def initialize(template, destination, refresh=False):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not refresh and "$TLS_CERTIFICATE_FILE" not in destination.read_text():
        return
    if destination.exists() and refresh:
        shutil.copy2(destination, destination.with_suffix(".json.backup"))
    cert_dir = destination.parent / "certs"
    cert_dir.mkdir(exist_ok=True)
    key_path, cert_path = cert_dir / "localhost.key", cert_dir / "localhost.crt"
    if not cert_path.exists():
        key = ec.generate_private_key(ec.SECP256R1())
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
        now = datetime.now(timezone.utc)
        cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                .public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - timedelta(minutes=5))
                .not_valid_after(now + timedelta(days=365))
                .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
                .sign(key, hashes.SHA256()))
        key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                                              serialization.PrivateFormat.PKCS8,
                                              serialization.NoEncryption()))
        key_path.chmod(0o600)
        cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
    # REALITY MLDSA needs enough target TLS certificate-record space for its signature.
    decoy_path = cert_dir / 'reality-decoy.crt'
    if not decoy_path.exists():
        decoy_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
        now = datetime.now(timezone.utc)
        padding = (x509.CertificateBuilder().subject_name(cert.subject).issuer_name(cert.subject)
                   .public_key(decoy_key.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(now - timedelta(minutes=5)).not_valid_after(now + timedelta(days=365))
                   .add_extension(x509.UnrecognizedExtension(x509.ObjectIdentifier('1.3.6.1.4.1.55555.1'), b'x' * 4096), critical=False)
                   .sign(decoy_key, hashes.SHA256()))
        decoy_path.write_bytes(cert_path.read_bytes() + padding.public_bytes(serialization.Encoding.PEM))
    credential_path = destination.parent / "local-credentials.json"
    if credential_path.exists():
        credentials = json.loads(credential_path.read_text())
    else:
        reality = x25519.X25519PrivateKey.generate()
        wg_server, wg_client = x25519.X25519PrivateKey.generate(), x25519.X25519PrivateKey.generate()
        credentials = {
            "REALITY_PRIVATE_KEY": base64.urlsafe_b64encode(reality.private_bytes_raw()).decode().rstrip("="),
            "REALITY_PUBLIC_KEY": base64.urlsafe_b64encode(reality.public_key().public_bytes_raw()).decode().rstrip("="),
            "WIREGUARD_PRIVATE_KEY": base64.b64encode(wg_server.private_bytes_raw()).decode(),
            "WIREGUARD_PUBLIC_KEY": base64.b64encode(wg_server.public_key().public_bytes_raw()).decode(),
            "WIREGUARD_CLIENT_PRIVATE_KEY": base64.b64encode(wg_client.private_bytes_raw()).decode(),
            "WIREGUARD_CLIENT_PUBLIC_KEY": base64.b64encode(wg_client.public_key().public_bytes_raw()).decode(),
            "HYSTERIA_TRANSPORT_AUTH": secrets.token_urlsafe(32),
            "SALAMANDER_PASSWORD": secrets.token_urlsafe(32),
            "LOCAL_PROXY_PASSWORD": secrets.token_urlsafe(32),
        }
        credential_path.write_text(json.dumps(credentials, indent=2))
        credential_path.chmod(0o600)
    if credentials.get("ECH_PUBLIC_NAME") != "ech.localhost":
        generated = subprocess.check_output(['xray', 'tls', 'ech', '--serverName', 'ech.localhost'], text=True).splitlines()
        credentials['ECH_CONFIG_LIST'] = generated[generated.index('ECH config list: ') + 1]
        credentials['ECH_SERVER_KEYS'] = generated[generated.index('ECH server keys: ') + 1]
        credentials['ECH_PUBLIC_NAME'] = 'ech.localhost'
    if "MLDSA65_SEED" not in credentials:
        generated = subprocess.check_output(['xray', 'mldsa65'], text=True).splitlines()
        credentials['MLDSA65_SEED'] = next(line.split(': ', 1)[1] for line in generated if line.startswith('Seed: '))
        credentials['MLDSA65_VERIFY'] = next(line.split(': ', 1)[1] for line in generated if line.startswith('Verify: '))
    credential_path.write_text(json.dumps(credentials, indent=2))
    credential_path.chmod(0o600)
    replacements = {**credentials, "TLS_CERTIFICATE_FILE": str(cert_path),
                    "REALITY_CERTIFICATE_FILE": str(decoy_path),
                    "TLS_KEY_FILE": str(key_path),
                    "TLS_CERT_PIN": hashlib.sha256(cert.public_bytes(serialization.Encoding.DER)).hexdigest()}
    def replace(value):
        if isinstance(value, str):
            return replacements.get(value.removeprefix("$"), value) if value.startswith("$") else value
        if isinstance(value, dict):
            return {k: replace(v) for k, v in value.items()}
        if isinstance(value, list):
            return [replace(v) for v in value]
        return value
    destination.write_text(json.dumps(replace(json.loads(Path(template).read_text())), indent=2))
    destination.chmod(0o600)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", default="/code/xray_config.json")
    parser.add_argument("--destination", default="/var/lib/marzban/xray_config.json")
    parser.add_argument("--refresh-presets", action="store_true")
    args = parser.parse_args()
    initialize(args.template, args.destination, refresh=args.refresh_presets)
