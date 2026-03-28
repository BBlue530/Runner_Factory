from botocore.exceptions import ClientError, BotoCoreError
from runner_token import fetch_runner_token
from variables import *

MACHINE_IMAGE = None

def get_latest_machine_image(ec2_client, events):
    global MACHINE_IMAGE

    try:
        if MACHINE_IMAGE is not None:
            msg = f"[+] MACHINE_IMAGE already present. {MACHINE_IMAGE}"
            print(msg)
            events["machine_image_status"] = msg
            return MACHINE_IMAGE, events

        print("[+] Calling for images")

        response = ec2_client.describe_images(
            Owners=["amazon"],
            Filters=[{"Name": "name", "Values": ["amzn2-ami-hvm-*-x86_64-gp2"]}]
        )

        images = response.get("Images", [])

        if not images:
            msg = "[!] No AMIs found matching filter"
            events["machine_image_status"] = msg
            raise ValueError(msg)

        MACHINE_IMAGE = sorted(images, key=lambda x: x["CreationDate"], reverse=True)[0]["ImageId"]

        msg = f"[+] MACHINE_IMAGE called. {MACHINE_IMAGE}"
        events["machine_image_status"] = msg
        return MACHINE_IMAGE, events

    except ClientError as e:
        msg = f"[!] AWS ClientError: {e}"
        print(msg)
        events["machine_image_status"] = msg

    except BotoCoreError as e:
        msg = f"[!] BotoCoreError: {e}"
        print(msg)
        events["machine_image_status"] = msg

    except ValueError as e:
        print(str(e))

def get_subnet(ec2_client, events):
    try:
        response = ec2_client.describe_subnets()
        subnets = response.get("Subnets", [])

        if not subnets:
            msg = "[!] No subnets found"
            print(msg)
            events[subnet_status] = msg
            return None, events

        subnet_id = subnets[0]["SubnetId"]

        msg = f"[+] Subnet retrieved: {subnet_id}"
        print(msg)
        events[subnet_status] = msg

        return subnet_id, events

    except ClientError as e:
        msg = f"[!] AWS ClientError: {e}"
        print(msg)
        events[subnet_status] = msg

    except BotoCoreError as e:
        msg = f"[!] BotoCoreError: {e}"
        print(msg)
        events[subnet_status] = msg

    return None, events

def get_security_group(ec2_client, events):
    try:
        response = ec2_client.describe_security_groups()
        groups = response.get("SecurityGroups", [])

        if not groups:
            msg = "[!] No security groups found"
            print(msg)
            events[security_group_status] = msg
            return None, events

        group_id = groups[0]["GroupId"]

        msg = f"[+] Security group retrieved: {group_id}"
        print(msg)
        events[security_group_status] = msg

        return group_id, events

    except ClientError as e:
        msg = f"[!] AWS ClientError: {e}"
        print(msg)
        events[security_group_status] = msg

    except BotoCoreError as e:
        msg = f"[!] BotoCoreError: {e}"
        print(msg)
        events[security_group_status] = msg

    return None, events

def get_ec2_config(ec2_client, secrets_client, githb_repo_full_name, events):
    runner_token, events = fetch_runner_token(secrets_client, githb_repo_full_name, events)
    machine_image, events = get_latest_machine_image(ec2_client, events)
    subnet, events = get_subnet(ec2_client, events)
    security_group, events = get_security_group(ec2_client, events)

    return runner_token, machine_image, subnet, security_group, events