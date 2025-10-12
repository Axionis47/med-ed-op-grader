import boto3
from boto3.dynamodb.conditions import Key  # noqa: F401


dynamodb = boto3.resource("dynamodb")


def put_submission(table_name: str, item: dict) -> None:
    table = dynamodb.Table(table_name)
    table.put_item(Item=item)


def get_submission(table_name: str, submission_id: str) -> dict | None:
    table = dynamodb.Table(table_name)
    resp = table.get_item(Key={"submission_id": submission_id})
    return resp.get("Item")

