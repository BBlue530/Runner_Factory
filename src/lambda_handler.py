import boto3
import json
import base64
from ec2_config import get_ec2_config
from ec2_runner import create_ec2_runner
from verify_signatures import verify_github_signature

# Env vars used:
# REGION = region for ec2 funny enough
# ECR_IMAGE = runner image on ecr
# RUNNER_ROLE = the role that ec2 runner will assume
# INSTANCE_TYPE = t3.micro or whatever

ec2_client = boto3.client('ec2')
secrets_client = boto3.client('secretsmanager')

def lambda_handler(event, context):
    print("[+] Lambda started")
    print(event.get("headers"))

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

    if not verify_github_signature(secrets_client, raw_payload, signature_header):
        print("[!] Invalid signature")
        return {"statusCode": 401, "body": "Invalid signature"}

    if parsed_body.get("action") != "queued":
        print("[+] Action is not queued")
        return {"statusCode": 200, "body": "Ignored"}

    labels = parsed_body.get("workflow_job", {}).get("labels", [])

    if "self-hosted" not in labels:
        print("[+] Not self hosted job")
        return {"statusCode": 200, "body": "Not a self-hosted job"}
    
    print("[+] Job is self hosted and queued")

    githb_repo_full_name = parsed_body["repository"]["full_name"]

    runner_token, machine_image, subnet, security_group = get_ec2_config(ec2_client, secrets_client, githb_repo_full_name)

    return create_ec2_runner(ec2_client, githb_repo_full_name, parsed_body, runner_token, machine_image, subnet, security_group)