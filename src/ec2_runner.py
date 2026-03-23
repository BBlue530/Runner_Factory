import os
import textwrap

def create_ec2_runner(ec2_client, githb_repo_full_name, parsed_body, runner_token, machine_image, subnet, security_group):
    runner_bootstrap = textwrap.dedent(f"""#!/bin/bash
    set -euo pipefail

    echo "Starting bootstrap..."

    yum update -y
    yum install -y docker aws-cli

    systemctl enable docker
    systemctl start docker

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
    docker run --rm \
    --name github-runner \
    -e GITHUB_URL="https://github.com/{githb_repo_full_name}" \
    -e RUNNER_TOKEN="{runner_token}" \
    {os.environ.get("ECR_IMAGE")}

    echo "Runner finished, shutting down..."
    trap 'shutdown -h now' EXIT
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
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [
                {"Key": "Role", "Value": "github-runner"},
                {"Key": "Repo", "Value": githb_repo_full_name},
                {"Key": "CreatedBy", "Value": "lambda-runner-factory"},
                {"Key": "RunID", "Value": str(run_id)}
            ]
        }]
    )

    print("[+] Runner created")
    return response["Instances"][0]["InstanceId"]