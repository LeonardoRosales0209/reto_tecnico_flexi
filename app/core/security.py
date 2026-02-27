import hmac
import hashlib

def sign_hmac_sha256(secret: str, body_bytes: bytes) -> str:
    """
    Returns hex digest HMAC-SHA256(secret, body_bytes)
    """
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=body_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()