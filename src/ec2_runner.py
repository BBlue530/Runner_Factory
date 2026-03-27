import os
import textwrap
import time

def create_ec2_runner(ec2_client, github_repo_full_name, parsed_body, runner_token, machine_image, subnet, security_group):
    runner_bootstrap = textwrap.dedent(f"""#!/bin/bash
    set -euo pipefail

    IDLE_TIMEOUT=300
    CHECK_INTERVAL=30
    idle_time=0

    (sleep 3600 && shutdown -h now) &

    echo "Starting bootstrap..."

    yum update -y

    yum install -y docker aws-cli
    systemctl enable docker
    systemctl start docker

    yum install -y amazon-ssm-agent
    systemctl enable amazon-ssm-agent
    systemctl start amazon-ssm-agent

    until docker info >/dev/null 2>&1; do
    echo "Waiting for Docker..."
    sleep 2
    done

    echo "Logging into ECR..."
    aws ecr get-login-password --region {os.environ.get("REGION")} | \
    docker login --username AWS --password-stdin {os.environ.get("ECR_IMAGE").split("/")[0]}

    echo "Pulling runner image..."
    docker pull {os.environ.get("ECR_IMAGE")}

    echo "Starting GitHub runner container..."
    docker run -d \
    --name github-runner \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --group-add $(stat -c '%g' /var/run/docker.sock) \
    -e GITHUB_URL="https://github.com/{github_repo_full_name}" \
    -e RUNNER_TOKEN="{runner_token}" \
    {os.environ.get("ECR_IMAGE")}

    echo "Monitoring runner..."
    while true; do
        if docker exec github-runner ps -eo cmd | grep -q "Runner.Worker"; then
            echo "Runner is BUSY"
            idle_time=0
        else
            echo "Runner is IDLE"
            idle_time=$((idle_time + CHECK_INTERVAL))
        fi

        if [ "$idle_time" -ge "$IDLE_TIMEOUT" ]; then
            echo "Idle timeout reached, shutting down..."
            break
        fi

        sleep "$CHECK_INTERVAL"
    done

    docker ps -a
    docker logs github-runner
    shutdown -h now
    """)

    run_id = str(parsed_body["workflow_job"]["run_id"])

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
                {"Key": "RunID", "Value": str(run_id)},
                {"Key": "CreatedAt", "Value": str(int(time.time()))},
                {"Key": "TTLSeconds", "Value": "3600"}
            ]
        }]
    )

    print("[+] Runner created")
    return response["Instances"][0]["InstanceId"]

def purge_runners(ec2_client):
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
                    expiry = int(launch_time) + 3600
            except Exception:
                print(f"[!] Bad tags on {instance_id}, terminating as fallback")
                instances_to_terminate.append(instance_id)
                continue

            if now > expiry:
                print(f"[+] Instance expired: {instance_id}")
                instances_to_terminate.append(instance_id)

    if instances_to_terminate:
        print(f"[+] Terminating: {instances_to_terminate}")
        ec2_client.terminate_instances(InstanceIds=instances_to_terminate)
    else:
        print("[+] No instances to terminate")