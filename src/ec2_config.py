from runner_token import fetch_runner_token

MACHINE_IMAGE = None

def get_latest_machine_image(ec2_client):
    global MACHINE_IMAGE

    if MACHINE_IMAGE is not None:
        print("[+] MACHINE_IMAGE already present")
        return MACHINE_IMAGE
    
    print("[+] Calling for images")

    response = ec2_client.describe_images(
        Owners=["amazon"],
        Filters=[{"Name": "name", "Values": ["amzn2-ami-hvm-*-x86_64-gp2"]}]
    )

    images = response.get("Images", [])

    if not images:
        raise Exception("No AMIs found matching filter")

    MACHINE_IMAGE = sorted(images, key=lambda x: x["CreationDate"], reverse=True)[0]["ImageId"]

    return MACHINE_IMAGE

def get_subnet(ec2_client):
    return ec2_client.describe_subnets()["Subnets"][0]["SubnetId"]

def get_security_group(ec2_client):
    return ec2_client.describe_security_groups()["SecurityGroups"][0]["GroupId"]

def get_ec2_config(ec2_client, secrets_client, githb_repo_full_name):
    runner_token = fetch_runner_token(secrets_client, githb_repo_full_name)
    machine_image = get_latest_machine_image(ec2_client)
    subnet = get_subnet(ec2_client)
    security_group = get_security_group(ec2_client)

    return runner_token, machine_image, subnet, security_group