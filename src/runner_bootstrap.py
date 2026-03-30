import textwrap
import os

def get_runner_bootstrap(github_repo_full_name, runner_token):

    ami = os.environ.get("AMI_MACHINE_IMAGE")
    if ami:
        runner_bootstrap = textwrap.dedent(f"""#!/bin/bash
        set -euo pipefail

        IDLE_TIMEOUT=300
        CHECK_INTERVAL=30
        idle_time=0

        (sleep 3600 && shutdown -h now) &

        echo "Starting bootstrap..."

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
        docker exec github-runner ./config.sh remove --unattended --token "{runner_token}"
        shutdown -h now
        """)
    else:
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
        docker exec github-runner ./config.sh remove --unattended --token "{runner_token}"
        shutdown -h now
        """)
    
    return runner_bootstrap