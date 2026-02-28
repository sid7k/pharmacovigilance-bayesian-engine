import json
from pathlib import Path
from datetime import datetime, timezone

AUDIT_LOG_PATH = Path("data/registry/audit_log.jsonl")

def audit_event(event_type: str, payload: dict) -> None:
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        **payload,
    }
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
