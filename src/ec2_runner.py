import os
import time
from botocore.exceptions import ClientError, BotoCoreError
from runner_bootstrap import get_runner_bootstrap
from variables import *

def create_ec2_runner(ec2_client, github_repo_full_name, run_id, created_at, runner_token, machine_image, subnet, security_group, events):
    runner_bootstrap = get_runner_bootstrap(github_repo_full_name, runner_token)

    try:

        print(f"[+] Creating EC2 runner for run_id=({run_id})")
        print(f"[+] AMI=({machine_image}), Subnet=({subnet}), SG=({security_group})")

        response = ec2_client.run_instances(
            MinCount=1,
            MaxCount=1,

            InstanceType=os.environ.get("INSTANCE_TYPE"),
            ImageId=machine_image,
            SubnetId=subnet,
            SecurityGroupIds=[security_group],
            IamInstanceProfile={"Name": os.environ.get("RUNNER_ROLE")},
            UserData=runner_bootstrap,
            ClientToken=str(run_id),
            InstanceInitiatedShutdownBehavior="terminate",
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": f"github-runner-{run_id}"},
                    {"Key": "Role", "Value": os.environ.get("RUNNER_ROLE")},
                    {"Key": "Repo", "Value": github_repo_full_name},
                    {"Key": "CreatedBy", "Value": "lambda-runner-factory"},
                    {"Key": "RunID", "Value": run_id},
                    {"Key": "CreatedAt", "Value": created_at},
                    {"Key": "TTLSeconds", "Value": ttl_seconds}
                ]
            }]
        )

        instance = response["Instances"][0]
        instance_id = instance["InstanceId"]
        private_ip = instance.get("PrivateIpAddress")

        msg = f"[+] Runner created: ({instance_id}) IP: ({private_ip}). Run ID: ({run_id})"
        print(msg)
        events[create_runner_status] = msg

        return events

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")

        if error_code == "IdempotentParameterMismatch":
            msg = f"[i] Idempotency conflict for run_id=({run_id}) (parameters differ)"
            print(msg)
            events[create_runner_status] = msg
        else:
            msg = f"[!] AWS ClientError ({error_code}): ({e}). Run ID: ({run_id})"
            print(msg)
            events[create_runner_status] = msg

    except BotoCoreError as e:
        msg = f"[!] BotoCoreError: ({e})"
        print(msg)
        events[create_runner_status] = msg

    except KeyError as e:
        msg = f"[!] Malformed response or payload: missing ({e}). Run ID: ({run_id})"
        print(msg)
        events[create_runner_status] = msg

    return events


def purge_runners(ec2_client, events):
    print("[+] Purging old runners...")

    response = ec2_client.describe_instances(
        Filters=[
            {"Name": "tag:Role", "Values": [os.environ.get("RUNNER_ROLE")]},
            {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]}
        ]
    )

    instances_to_terminate = []
    now = int(time.time())

    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            instance_id = instance["InstanceId"]

            tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}

            created_at = tags.get("CreatedAt")
            ttl = tags.get("TTLSeconds")

            try:
                if created_at and ttl:
                    expiry = int(created_at) + int(ttl)
                else:
                    launch_time = instance["LaunchTime"].timestamp()
                    expiry = int(launch_time) + int(ttl_seconds)
            except Exception:
                print(f"[!] Bad tags on ({instance_id}), terminating as fallback")
                instances_to_terminate.append(instance_id)
                continue

            if now > expiry:
                print(f"[+] Instance expired: ({instance_id})")
                instances_to_terminate.append(instance_id)

    if instances_to_terminate:
        print(f"[!] Terminating: ({instances_to_terminate})")
        events[purge_old_runners] = f"[!] Terminating: ({instances_to_terminate})"
        ec2_client.terminate_instances(InstanceIds=instances_to_terminate)
    else:
        print("[+] No instances to terminate")
        events[purge_old_runners] = "[+] No instances to terminate"
    
    return events

def get_active_runner_count(ec2_client):
    response = ec2_client.describe_instances(
        Filters=[
            {"Name": "tag:Role", "Values": [os.environ.get("RUNNER_ROLE")]},
            {"Name": "instance-state-name", "Values": ["pending", "running"]}
        ]
    )

    return sum(len(r["Instances"]) for r in response["Reservations"])

def get_runner(ec2_client, run_id):
    response = ec2_client.describe_instances(
        Filters=[
            {"Name": "tag:Role", "Values": [os.environ.get("RUNNER_ROLE")]},
            {"Name": "tag:RunID", "Values": [run_id]},
            {"Name": "instance-state-name", "Values": ["pending", "running"]}
        ]
    )

    return sum(len(r["Instances"]) for r in response["Reservations"])