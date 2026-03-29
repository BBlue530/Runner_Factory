import boto3
import json
import base64
import os
from ec2_config import get_ec2_config
from ec2_runner import create_ec2_runner, purge_runners, get_active_runner_count
from verify_signatures import verify_github_signature
from discord_webhook import send_events_discord_webhook
from ip_whitelist import verify_ip_whitelist
from variables import *

ec2_client = boto3.client('ec2')
secrets_client = boto3.client('secretsmanager')

def lambda_handler(event, context):
    events = {}
    try:
        print("[+] Lambda started")

        client_ip = event.get("requestContext", {}).get("http", {}).get("sourceIp")
        print(f"[+] Client ip: ({client_ip})")
        events[client_ip_status] = f"[+] Client ip: ({client_ip})"

        if os.environ.get("ENABLE_IP_WHITELIST", "true").lower() == "true":
            if not verify_ip_whitelist(client_ip):
                print(f"[!] Client ip not found in whitelist. Client ip: ({client_ip})")
                events[ip_whitelist_status] = f"[!] Client ip not found in whitelist. Client ip: ({client_ip})"
                return {"statusCode": 403, "body": json.dumps({"error": "IP not allowed"})}
            events[ip_whitelist_status] = f"[+] Client ip found in whitelist. Client ip: ({client_ip})"
        else:
            events[ip_whitelist_status] = f"[i] Whitelist not enabled. Client ip: ({client_ip})"

        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        signature_header = headers.get("x-hub-signature-256")

        raw_body = event.get("body") or ""

        if event.get("isBase64Encoded"):
            raw_payload = base64.b64decode(raw_body)
            parsed_body = json.loads(raw_payload.decode("utf-8"))
        else:
            raw_payload = raw_body.encode("utf-8")
            parsed_body = json.loads(raw_body)
        
        print(f"[+] Parsed body: {parsed_body}")

        verified_signature, events = verify_github_signature(secrets_client, raw_payload, signature_header, events)

        if not verified_signature:
            print("[!] Invalid signature")
            events[signature_verified] = "[!] Invalid signature"
            return {"statusCode": 401, "body": "Invalid signature"}
        else:
            events[signature_verified] = "[+] Valid signature"
        
        events = purge_runners(ec2_client, events)

        if parsed_body.get("action") != "queued":
            print("[i] Action is not queued")
            events[webhook_action] = f"[i] Action is not queued. Current action: ({parsed_body.get('action')})"
            return {"statusCode": 200, "body": "Ignored"}
        events[webhook_action] = f"[+] Action is queued. Current action: ({parsed_body.get('action')})"

        labels = parsed_body.get("workflow_job", {}).get("labels", [])

        if "self-hosted" not in labels:
            print("[i] Not self hosted job")
            events[webhook_label] = f"[i] Not self hosted job label. Current label: ({labels})"
            return {"statusCode": 200, "body": "Not a self-hosted job"}
        events[webhook_label] = f"[+] Self hosted job label. Current label: ({labels})"
        print("[+] Job is self hosted and queued")

        MAX_RUNNERS = int(os.environ.get("MAX_RUNNERS", "10"))

        current_runners = get_active_runner_count(ec2_client)

        if current_runners >= MAX_RUNNERS:
            print(f"[!] Runner cap reached: ({current_runners}/{MAX_RUNNERS})")
            events[runner_cap] = f"[!] Runner cap reached: ({current_runners}/{MAX_RUNNERS})"
            return {"statusCode": 429, "body": "Runner capacity reached"}
        events[runner_cap] = f"[+] Runner cap: ({current_runners}/{MAX_RUNNERS})"
        print(f"[+] Runner cap: ({current_runners}/{MAX_RUNNERS})")
        
        githb_repo_full_name = parsed_body["repository"]["full_name"]

        runner_token, machine_image, subnet, security_group, events = get_ec2_config(ec2_client, secrets_client, githb_repo_full_name, events)

        create_ec2_runner(ec2_client, githb_repo_full_name, parsed_body, runner_token, machine_image, subnet, security_group, events)

    finally:
        try:
            send_events_discord_webhook(events, secrets_client)
        except Exception as webhook_error:
            print(f"[!] Failed to send Discord webhook: ({webhook_error})")