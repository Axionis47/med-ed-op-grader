import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import boto3
from boto3.dynamodb.conditions import Key


def _table():
    table_name = os.environ.get("SUBMISSIONS_TABLE", "Submissions")
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(table_name)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_submission(submission_id: str) -> Optional[Dict[str, Any]]:
    tbl = _table()
    resp = tbl.get_item(Key={"submission_id": submission_id})
    return resp.get("Item")


def update_submission(submission_id: str, **fields) -> Dict[str, Any]:
    # Upsert using UpdateItem with SET expression
    tbl = _table()
    fields = dict(fields)
    fields["updated_at"] = now_iso()

    expr_names = {}
    expr_vals = {}
    set_parts = []
    i = 0
    for k, v in fields.items():
        name_key = f"#k{i}"
        val_key = f":v{i}"
        expr_names[name_key] = k
        expr_vals[val_key] = v
        set_parts.append(f"{name_key} = {val_key}")
        i += 1
    update_expr = "SET " + ", ".join(set_parts)

    resp = tbl.update_item(
        Key={"submission_id": submission_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_vals,
        ReturnValues="ALL_NEW",
    )
    return resp.get("Attributes", {})

