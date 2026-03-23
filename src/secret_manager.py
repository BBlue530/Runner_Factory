import base64
import json
import os

APP_ID = None
PRIV_KEY = None
INST_ID = None
HMAC = None

def read_secret_from_secret_manager(secrets_client, secret_key_name, secret_name):
    response = secrets_client.get_secret_value(SecretId=secret_name)

    if "SecretString" in response:
        secret_payload = response["SecretString"]
    else:
        secret_payload = base64.b64decode(response["SecretBinary"]).decode("utf-8")

    try:
        secret_obj = json.loads(secret_payload)
    except json.JSONDecodeError:
        raise ValueError("Secret is not valid JSON")

    if secret_key_name not in secret_obj:
        raise KeyError(f"[!] Key: '{secret_key_name}' not found in secret '{secret_name}'")

    return secret_obj[secret_key_name]

def read_app_id_secret(secrets_client):
    global APP_ID
    secret_name = os.environ.get("SECRET_NAME")
    github_app_id_secret_name = os.environ.get("GITHUB_APP_ID_SECRET_NAME")

    if APP_ID is not None:
        print("[+] APP_ID already present")
        return APP_ID
    
    print("[+] Calling secret manager for APP_ID")
    APP_ID = read_secret_from_secret_manager(secrets_client, github_app_id_secret_name, secret_name)
    return APP_ID

def read_private_key_secret(secrets_client):
    global PRIV_KEY
    secret_name = os.environ.get("SECRET_NAME")
    github_private_key_secret_name = os.environ.get("GITHUB_PRIV_KEY_SECRET_NAME")

    if PRIV_KEY is not None:
        print("[+] PRIV_KEY already present")
        return PRIV_KEY
    
    print("[+] Calling secret manager for PRIV_KEY")
    PRIV_KEY = read_secret_from_secret_manager(secrets_client, github_private_key_secret_name, secret_name)
    return PRIV_KEY

def read_installation_id_secret(secrets_client):
    global INST_ID
    secret_name = os.environ.get("SECRET_NAME")
    github_inst_id_secret_name = os.environ.get("GITHUB_INST_ID_SECRET_NAME")

    if INST_ID is not None:
        print("[+] INST_ID already present")
        return INST_ID
    
    print("[+] Calling secret manager for INST_ID")
    INST_ID = read_secret_from_secret_manager(secrets_client, github_inst_id_secret_name, secret_name)
    return INST_ID

def read_hmac_secret(secrets_client):
    global HMAC
    secret_name = os.environ.get("SECRET_NAME")
    github_hmac_secret_name = os.environ.get("GITHUB_HMAC_SECRET_NAME")

    if HMAC is not None:
        print("[+] HMAC already present")
        return HMAC
    
    print("[+] Calling secret manager for HMAC")
    HMAC = read_secret_from_secret_manager(secrets_client, github_hmac_secret_name, secret_name)
    return HMAC