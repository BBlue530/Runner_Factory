import requests
from secret_manager import read_pat_secret


def get_runner_token(secrets_client, githb_repo_full_name):
    pat = read_pat_secret(secrets_client)

    url = f"https://api.github.com/repos/{githb_repo_full_name}/actions/runners/registration-token"
    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json"
    }

    r = requests.post(url, headers=headers)
    r.raise_for_status()
    return r.json()["token"]


def get_latest_machine_image(ec2_client):
    images = ec2_client.describe_images(
        Owners=["amazon"],
        Filters=[{"Name": "name", "Values": ["amzn2-ami-hvm-*-x86_64-gp2"]}]
    )["Images"]

    return sorted(images, key=lambda x: x["CreationDate"], reverse=True)[0]["ImageId"]


def get_subnet(ec2_client):
    return ec2_client.describe_subnets(
        Filters=[{"Name": "tag:Role", "Values": ["runner-subnet"]}]
    )["Subnets"][0]["SubnetId"]


def get_security_group(ec2_client):
    return ec2_client.describe_security_groups(
        Filters=[{"Name": "tag:Role", "Values": ["runner-sg"]}]
    )["SecurityGroups"][0]["GroupId"]

def get_ec2_config(ec2_client, secrets_client, githb_repo_full_name):
    runner_token = get_runner_token(secrets_client, githb_repo_full_name)
    machine_image = get_latest_machine_image(ec2_client)
    subnet = get_subnet(ec2_client)
    security_group = get_security_group(ec2_client)

    return runner_token, machine_image, subnet, security_group