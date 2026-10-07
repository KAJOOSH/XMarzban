"""Per-user WireGuard keys and deterministic, collision-free tunnel addresses."""
import base64
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey


def private_key():
    return base64.b64encode(X25519PrivateKey.generate().private_bytes_raw()).decode()


def public_key(secret):
    return base64.b64encode(X25519PrivateKey.from_private_bytes(base64.b64decode(secret, validate=True)).public_key().public_bytes_raw()).decode()


def addresses(user_id):
    user_id = int(user_id)
    if not 1 <= user_id <= 64515:
        raise ValueError('WireGuard user ID exceeds the managed IPv4 address pool')
    subnet, host = divmod(user_id, 254)
    return [f'10.78.{subnet+1}.{host+1}/32', f'fd00:78::{user_id+2:x}/128']
