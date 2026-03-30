import requests
import json
from secret_manager import read_discord_webhook_secret
from variables import *

def send_events_discord_webhook(events, secrets_client):
    discord_webhook, events = read_discord_webhook_secret(secrets_client, events)

    def get(key):
        return events.get(key, "-")

    if any("[!]" in str(v) for v in events.values()):
        color = 16711680 # red
    elif any("[i]" in str(v) for v in events.values()):
        color = 16776960 # yellow
    else:
        color = 65280 # green

    fields = [
        {"name": "Action", "value": get(webhook_action), "inline": True},
        {"name": "Label", "value": get(webhook_label), "inline": True},

        {"name": "Signature", "value": get(signature_verified), "inline": True},

        {"name": "IP Whitelist", "value": "\n".join([
            get(client_ip_status),
            get(ip_whitelist_status),
        ]), "inline": False},

        {"name": "Runner Lock", "value": "\n".join([
            get(lock_runner_status),
        ]), "inline": False},

        {"name": "Secrets (HMAC / App / Key)", "value": "\n".join([
            get(hmac_secret_status),
            get(app_id_secret_status),
            get(priv_key_secret_status),
        ]), "inline": False},

        {"name": "Auth (JWT / Install / Runner)", "value": "\n".join([
            get(jwt_status),
            get(inst_token_status),
            get(runner_token_status),
        ]), "inline": False},

        {"name": "EC2 Config", "value": "\n".join([
            get(machine_image_status),
            get(subnet_status),
            get(security_group_status),
        ]), "inline": False},

        {"name": "Runner Capacity", "value": get(runner_cap), "inline": True},
        {"name": "Purge", "value": get(purge_old_runners), "inline": True},

        {"name": "Runner Creation", "value": get(create_runner_status), "inline": False},
    ]

    fields = [f for f in fields if f["value"] != "-"]

    payload = {
        "embeds": [{
            "title": "GitHub Runner",
            "color": color,
            "fields": fields,
            "footer": {
                "text": "Lambda Runner Factory"
            }
        }]
    }

    try:
        response = requests.post(
            discord_webhook,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )

        if response.status_code not in [200, 204]:
            print("[!] Failed to send alert to webhook!")
            print(f"[!] Status: ({response.status_code}), Body: ({response.text})")

    except Exception as e:
        print(f"[!] Webhook exception: ({e})")