import hashlib
from .audit import audit_event

ALLOWED_STATUSES = ["DETECTED", "VALIDATING", "ASSESSED", "CLOSED"]

def make_signal_id(drug_key: str, event_key: str) -> str:
    raw = f"{drug_key}||{event_key}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:12]

def register_signal(conn, *, drug_key, event_key, run_id=None, metrics=None, created_by="user") -> str:
    metrics = metrics or {}
    signal_id = make_signal_id(drug_key, event_key)

    cur = conn.cursor()
    cur.execute("""
      INSERT OR IGNORE INTO signal_registry(
        signal_id, drug_key, event_key, status, priority,
        first_seen_run, last_seen_run, ic, ic025, ic975, n11, n1p, np1, npp, notes
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        signal_id, drug_key, event_key, "DETECTED", int(metrics.get("priority", 3)),
        run_id, run_id,
        metrics.get("ic"), metrics.get("ic025"), metrics.get("ic975"),
        metrics.get("n11"), metrics.get("n1p"), metrics.get("np1"), metrics.get("npp"),
        metrics.get("notes", "")
    ))
    conn.commit()

    audit_event("signal_registered", {
        "signal_id": signal_id,
        "drug_key": drug_key,
        "event_key": event_key,
        "run_id": run_id,
        "created_by": created_by,
        "metrics": metrics,
    })
    return signal_id

def update_status(conn, *, signal_id, to_status, reason="", changed_by="user", run_id=None) -> None:
    if to_status not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status: {to_status}")

    cur = conn.cursor()
    cur.execute("SELECT status FROM signal_registry WHERE signal_id = ?", (signal_id,))
    row = cur.fetchone()
    if not row:
        raise ValueError("signal_id not found")

    from_status = row["status"]
    cur.execute("""
      UPDATE signal_registry
      SET status = ?, updated_at = datetime('now'), last_seen_run = COALESCE(?, last_seen_run)
      WHERE signal_id = ?
    """, (to_status, run_id, signal_id))

    cur.execute("""
      INSERT INTO signal_status_history(signal_id, from_status, to_status, changed_by, reason, run_id)
      VALUES (?, ?, ?, ?, ?, ?)
    """, (signal_id, from_status, to_status, changed_by, reason, run_id))

    conn.commit()

    audit_event("signal_status_changed", {
        "signal_id": signal_id,
        "from_status": from_status,
        "to_status": to_status,
        "reason": reason,
        "changed_by": changed_by,
        "run_id": run_id,
    })

def update_notes(conn, *, signal_id, notes, changed_by="user") -> None:
    cur = conn.cursor()
    cur.execute("""
      UPDATE signal_registry
      SET notes = ?, updated_at = datetime('now')
      WHERE signal_id = ?
    """, (notes, signal_id))
    conn.commit()

    audit_event("signal_notes_updated", {
        "signal_id": signal_id,
        "changed_by": changed_by,
        "notes_len": len(notes or ""),
    })