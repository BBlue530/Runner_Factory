import hmac
import hashlib
from secret_manager import read_hmac_secret

def verify_github_signature(secrets_client, raw_payload, signature_header):
    if not signature_header:
        return False

    if not signature_header.startswith("sha256="):
        return False

    signature = signature_header.split("=", 1)[1]

    hmac_secret = read_hmac_secret(secrets_client)

    if isinstance(raw_payload, str):
        raw_payload = raw_payload.encode("utf-8")

    mac = hmac.new(
        hmac_secret.encode("utf-8"),
        msg=raw_payload,
        digestmod=hashlib.sha256
    )

    expected = mac.hexdigest()

    return hmac.compare_digest(expected, signature)