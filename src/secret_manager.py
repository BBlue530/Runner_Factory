import base64
import json
import os

PAT = None
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

def read_pat_secret(secrets_client):
    global PAT
    secret_name = os.environ.get("SECRET_NAME")
    github_pat_secret_name = os.environ.get("GITHUB_PAT_SECRET_NAME")

    if PAT is not None:
        print("[+] PAT already present")
        return PAT
    
    print("[+] Calling secret manager for PAT")
    PAT = read_secret_from_secret_manager(secrets_client, github_pat_secret_name, secret_name)
    return PAT

def read_hmac_secret(secrets_client):
    global HMAC
    secret_name = os.environ.get("SECRET_NAME")
    github_pat_secret_name = os.environ.get("GITHUB_HMAC_SECRET_NAME")

    if HMAC is not None:
        print("[+] HMAC already present")
        return HMAC
    
    print("[+] Calling secret manager for HMAC")
    HMAC = read_secret_from_secret_manager(secrets_client, github_pat_secret_name, secret_name)
    return HMAC