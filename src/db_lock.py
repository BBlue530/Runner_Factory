import os
from variables import ttl_seconds

def db_lock_runner(dynamodb_client, run_id, created_at):
    ttl = int(created_at) + int(ttl_seconds)

    try:
        dynamodb_client.put_item(
            TableName=os.environ.get("DYNAMODB_LOCK_TABLE"),
            Item={
                "LockID": {"S": run_id},
                "created_at": {"N": created_at},
                "expires_at": {"N": str(ttl)},
            },
            ConditionExpression="attribute_not_exists(LockID) OR expires_at < :now",
            ExpressionAttributeValues={
                ":now": {"N": created_at}
            }
        )
        return True, None

    except dynamodb_client.exceptions.ConditionalCheckFailedException:
        return False, "Lock already exists and is still valid"