import requests
import jwt
import time
from secret_manager import read_app_id_secret, read_private_key_secret, read_installation_id_secret

def create_jwt(app_id, priv_key):
    now = int(time.time())

    payload = {
        "iat": now - 60,
        "exp": now + 600,
        "iss": app_id
    }

    priv_key = priv_key.replace("\\n", "\n")
    print(priv_key[:100])

    token = jwt.encode(payload, priv_key, algorithm="RS256")

    if isinstance(token, bytes):
        token = token.decode("utf-8")

    print("[+] JWT created")
    return token

def get_installation_token(jwt_token, installation_id):
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json"
    }

    r = requests.post(url, headers=headers)
    r.raise_for_status()

    print("[+] Installation token created")
    return r.json()["token"]

def get_runner_token(repo_full_name, installation_token):
    url = f"https://api.github.com/repos/{repo_full_name}/actions/runners/registration-token"

    headers = {
        "Authorization": f"Bearer {installation_token}",
        "Accept": "application/vnd.github+json"
    }

    r = requests.post(url, headers=headers)
    r.raise_for_status()

    print("[+] Runner token created")
    return r.json()["token"]

def fetch_runner_token(secrets_client, repo_full_name):
    app_id = read_app_id_secret(secrets_client)
    priv_key = read_private_key_secret(secrets_client)
    inst_id = read_installation_id_secret(secrets_client)

    jwt_token = create_jwt(app_id, priv_key)
    inst_token = get_installation_token(jwt_token, inst_id)

    return get_runner_token(repo_full_name, inst_token)