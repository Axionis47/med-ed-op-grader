from __future__ import annotations
import json
import os
from typing import Any, Dict, Optional

import boto3
from jsonschema import validate, ValidationError

MODEL_ID = os.getenv("BEDROCK_MODEL_EXTRACTOR", "anthropic.claude-3-5-sonnet-20240620-v1:0")
GUARDRAILS_ID = os.getenv("GUARDRAILS_ID", "opgrader-guardrails")
PROMPT_BUNDLE_ID = os.getenv("PROMPT_BUNDLE_ID", "bundle_2025_10_op@1.0.0")

_runtime = None

def _runtime_client():
    global _runtime
    if _runtime is None:
        _runtime = boto3.client("bedrock-runtime")
    return _runtime


def load_schema(schema_name: str) -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", "schemas", f"{schema_name}.schema.json")
    # Resolve relative from this file
    here = os.path.dirname(__file__)
    path = os.path.normpath(os.path.join(here, "..", "prompts", "schemas", f"{schema_name}.schema.json"))
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _anthropic_messages_body(system: str, user_json: Dict[str, Any], temperature: float = 0.0, max_tokens: int = 1200) -> Dict[str, Any]:
    return {
        "anthropic_version": "bedrock-2023-05-31",
        "system": system,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": json.dumps(user_json)}]},
        ],
        # Guardrails configuration
        "guardrailConfig": {"guardrailIdentifier": GUARDRAILS_ID, "guardrailVersion": "DRAFT"},
    }


def converse_json(schema_name: str, system: str, user_payload: Dict[str, Any], *, temperature: float = 0.0, max_tokens: int = 1200, repair: bool = True) -> Optional[Dict[str, Any]]:
    """Call Claude 3.5 Sonnet via Bedrock and validate against JSON schema.
    Returns parsed object or None on failure. Performs a 1x repair attempt on schema fail.
    """
    schema = load_schema(schema_name)
    body = _anthropic_messages_body(system, {"bundle": PROMPT_BUNDLE_ID, "task": schema_name, "input": user_payload})
    rt = _runtime_client()
    try:
        resp = rt.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
        data = json.loads(resp.get("body").read().decode("utf-8"))
        text = "".join([c.get("text", "") for c in (data.get("content") or [])])
        obj = json.loads(text) if text.strip().startswith("{") else None
        if obj is None:
            return None
        validate(instance=obj, schema=schema)
        return obj
    except ValidationError:
        if not repair:
            return None
        # 1x repair attempt: instruct model to return only corrected JSON
        try:
            repair_user = {"bundle": PROMPT_BUNDLE_ID, "task": f"repair:{schema_name}", "schema": schema, "previous": user_payload}
            body2 = _anthropic_messages_body("Return ONLY valid JSON that satisfies the provided JSON schema.", repair_user, temperature=0.0, max_tokens=max_tokens)
            resp2 = rt.invoke_model(modelId=MODEL_ID, body=json.dumps(body2))
            data2 = json.loads(resp2.get("body").read().decode("utf-8"))
            txt2 = "".join([c.get("text", "") for c in (data2.get("content") or [])])
            obj2 = json.loads(txt2) if txt2.strip().startswith("{") else None
            if obj2 is None:
                return None
            validate(instance=obj2, schema=schema)
            return obj2
        except Exception:
            return None
    except Exception:
        return None

