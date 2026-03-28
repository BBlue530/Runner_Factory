import requests
import jwt
import time
from secret_manager import read_app_id_secret, read_private_key_secret, read_installation_id_secret
from variables import *

def create_jwt(app_id, priv_key, events):
    now = int(time.time())

    payload = {
        "iat": now - 60,
        "exp": now + 600,
        "iss": app_id
    }

    priv_key = priv_key.replace("\\n", "\n")

    token = jwt.encode(payload, priv_key, algorithm="RS256")

    if isinstance(token, bytes):
        token = token.decode("utf-8")

    print("[+] JWT created")
    events[jwt_status] = "[+] JWT created"
    return token, events

def get_installation_token(jwt_token, installation_id, events):
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json"
    }

    try:
        r = requests.post(url, headers=headers)
        r.raise_for_status()

        print("[+] Installation token created")
        events[inst_token_status] = "[+] Installation token created"

        return r.json()["token"], events

    except requests.exceptions.HTTPError as e:
        error_msg = f"[!] HTTP error: {e} Response: {r.text}"
        print(error_msg)
        events[inst_token_status] = error_msg

    except requests.exceptions.RequestException as e:
        error_msg = f"[!] Request failed: {e}"
        print(error_msg)
        events[inst_token_status] = error_msg

    return None, events

def get_runner_token(repo_full_name, installation_token, events):
    url = f"https://api.github.com/repos/{repo_full_name}/actions/runners/registration-token"

    headers = {
        "Authorization": f"Bearer {installation_token}",
        "Accept": "application/vnd.github+json"
    }

    try:
        r = requests.post(url, headers=headers)
        r.raise_for_status()

        print("[+] Runner token created")
        events["runner_token_status"] = "[+] Runner token created"

        return r.json()["token"], events

    except requests.exceptions.HTTPError as e:
        error_msg = f"[!] HTTP error: {e} Response: {r.text}"
        print(error_msg)
        events["runner_token_status"] = error_msg

    except requests.exceptions.RequestException as e:
        error_msg = f"[!] Request failed: {e}"
        print(error_msg)
        events["runner_token_status"] = error_msg

    return None, events

def fetch_runner_token(secrets_client, repo_full_name, events):
    app_id, events = read_app_id_secret(secrets_client, events)
    priv_key, events = read_private_key_secret(secrets_client, events)
    inst_id, events = read_installation_id_secret(secrets_client, events)

    jwt_token, events = create_jwt(app_id, priv_key, events)
    inst_token, events = get_installation_token(jwt_token, inst_id, events)

    runner_token, events = get_runner_token(repo_full_name, inst_token, events)

    return runner_token, events