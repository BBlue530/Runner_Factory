import base64
import json
import os
from variables import *

APP_ID = None
PRIV_KEY = None
HMAC = None
WEBHOOK = None

def read_secret_from_secret_manager(secrets_client, secret_key_name, secret_name, secret_status, events):
    response = secrets_client.get_secret_value(SecretId=secret_name)

    if "SecretString" in response:
        secret_payload = response["SecretString"]
    else:
        secret_payload = base64.b64decode(response["SecretBinary"]).decode("utf-8")

    try:
        secret_obj = json.loads(secret_payload)
    except json.JSONDecodeError:
        events[secret_status] = f"[!] Secret is not valid JSON. Key: ({secret_key_name})"
        raise ValueError("Secret is not valid JSON")

    if secret_key_name not in secret_obj:
        events[secret_status] = f"[!] Key: ({secret_key_name}) not found in secret ({secret_name})"
        raise KeyError(f"[!] Key: ({secret_key_name}) not found in secret ({secret_name})")

    events[secret_status] = f"[+] Called for secret successfully. Key: ({secret_key_name})"

    return secret_obj[secret_key_name], events

def read_app_id_secret(secrets_client, events):
    global APP_ID
    secret_name = os.environ.get("SECRET_NAME")
    github_app_id_secret_name = os.environ.get("GITHUB_APP_ID_SECRET_NAME")

    if APP_ID is not None:
        print("[+] APP_ID already present")
        events[app_id_secret_status] = "[+] APP_ID already present"
        return APP_ID, events
    
    print("[+] Calling secret manager for APP_ID")
    APP_ID, events = read_secret_from_secret_manager(secrets_client, github_app_id_secret_name, secret_name, app_id_secret_status, events)
    return APP_ID, events

def read_private_key_secret(secrets_client, events):
    global PRIV_KEY
    secret_name = os.environ.get("SECRET_NAME")
    github_private_key_secret_name = os.environ.get("GITHUB_PRIV_KEY_SECRET_NAME")

    if PRIV_KEY is not None:
        print("[+] PRIV_KEY already present")
        events[priv_key_secret_status] = "[+] PRIV_KEY already present"
        return PRIV_KEY, events
    
    print("[+] Calling secret manager for PRIV_KEY")
    PRIV_KEY, events = read_secret_from_secret_manager(secrets_client, github_private_key_secret_name, secret_name, priv_key_secret_status, events)
    return PRIV_KEY, events

def read_hmac_secret(secrets_client, events):
    global HMAC
    secret_name = os.environ.get("SECRET_NAME")
    github_hmac_secret_name = os.environ.get("GITHUB_HMAC_SECRET_NAME")

    if HMAC is not None:
        print("[+] HMAC already present")
        events[hmac_secret_status] = "[+] HMAC already present"
        return HMAC, events
    
    print("[+] Calling secret manager for HMAC")
    HMAC, events = read_secret_from_secret_manager(secrets_client, github_hmac_secret_name, secret_name, hmac_secret_status, events)
    return HMAC, events

def read_webhook_secret(secrets_client, events):
    global WEBHOOK
    secret_name = os.environ.get("SECRET_NAME")
    webhook_secret_name = os.environ.get("WEBHOOK_SECRET_NAME")

    if WEBHOOK is not None:
        print("[+] WEBHOOK already present")
        events[webhook_secret_status] = "[+] WEBHOOK already present"
        return WEBHOOK, events
    
    print("[+] Calling secret manager for WEBHOOK")
    WEBHOOK, events = read_secret_from_secret_manager(secrets_client, webhook_secret_name, secret_name, webhook_secret_status, events)
    return WEBHOOK, events