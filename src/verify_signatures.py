import hmac
import hashlib
from secret_manager import read_hmac_secret
from variables import *

def verify_github_signature(secrets_client, raw_payload, signature_header, events):
    if not signature_header:
        print("[!] Signature header missing")
        events[signature] = "[!] Signature header missing"
        return False, events

    if not signature_header.startswith("sha256="):
        print("[!] Signature header did not start with 'sha256='")
        events[signature] = "[!] Signature header did not start with 'sha256='"
        return False, events

    signature = signature_header.split("=", 1)[1]

    hmac_secret, events = read_hmac_secret(secrets_client, events)

    if isinstance(raw_payload, str):
        raw_payload = raw_payload.encode("utf-8")

    mac = hmac.new(
        hmac_secret.encode("utf-8"),
        msg=raw_payload,
        digestmod=hashlib.sha256
    )

    expected = mac.hexdigest()

    events[signature] = "[+] Signature header present"

    return hmac.compare_digest(expected, signature), events