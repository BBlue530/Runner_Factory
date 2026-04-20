import requests
import json
from secret_manager import read_webhook_secret
from variables import *

def event_webhook(events, secrets_client):
    webhook, events = read_webhook_secret(secrets_client, events)

    if "discord" in webhook:
        send_events_discord_webhook(events, webhook)
    else:
        send_events_webhook(events, webhook)

def send_events_webhook(events, webhook):

    payload = {
        "title": "GitHub Runner",
        "status": {
            signature_verified: events.get(signature_verified),
            signature: events.get(signature),
            purge_old_runners: events.get(purge_old_runners),
            runner_cap: events.get(runner_cap),
            webhook_action: events.get(webhook_action),
            webhook_label: events.get(webhook_label),
            hmac_secret_status: events.get(hmac_secret_status),
            priv_key_secret_status: events.get(priv_key_secret_status),
            app_id_secret_status: events.get(app_id_secret_status),
            webhook_secret_status: events.get(webhook_secret_status),
            jwt_status: events.get(jwt_status),
            inst_id_status: events.get(inst_id_status),
            inst_token_status: events.get(inst_token_status),
            runner_token_status: events.get(runner_token_status),
            machine_image_status: events.get(machine_image_status),
            subnet_status: events.get(subnet_status),
            security_group_status: events.get(security_group_status),
            create_runner_status: events.get(create_runner_status),
            client_ip_status: events.get(client_ip_status),
            ip_whitelist_status: events.get(ip_whitelist_status),
            lock_runner_status: events.get(lock_runner_status),
        },
        "footer": {
            "text": "Runner Factory"
        }
    }

    try:
        response = requests.post(
            webhook,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )

        if response.status_code not in [200, 204]:
            print("[!] Failed to send alert to webhook!")
            print(f"[!] Status: ({response.status_code}), Body: ({response.text})")

    except Exception as e:
        print(f"[!] Webhook exception: ({e})")

def send_events_discord_webhook(events, discord_webhook):

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
            get(inst_id_status),
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
                "text": "Runner Factory"
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