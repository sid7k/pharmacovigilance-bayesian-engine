import json
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT_DIR = Path("artifacts/signal_review_packs")

def export_signal_pack(conn, *, signal_id: str, provenance: dict | None = None) -> Path:
    provenance = provenance or {}
    cur = conn.cursor()

    cur.execute("SELECT * FROM signal_registry WHERE signal_id = ?", (signal_id,))
    sig = cur.fetchone()
    if not sig:
        raise ValueError("signal_id not found")

    cur.execute("""
      SELECT from_status, to_status, changed_by, reason, run_id, created_at
      FROM signal_status_history
      WHERE signal_id = ?
      ORDER BY id ASC
    """, (signal_id,))
    history = [dict(r) for r in cur.fetchall()]

    pack = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "signal": dict(sig),
        "history": history,
        "provenance": provenance,
    }

    base = OUT_DIR / signal_id
    base.mkdir(parents=True, exist_ok=True)

    json_path = base / "pack.json"
    json_path.write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")

    pdf_path = base / "pack.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4

    y = height - 50
    def line(txt, dy=16):
        nonlocal y
        c.drawString(50, y, str(txt)[:120])
        y -= dy
        if y < 70:
            c.showPage()
            y = height - 50

    line("Nexus-PV — Signal Review Pack")
    line(f"Signal ID: {sig['signal_id']}")
    line(f"Drug: {sig['drug_key']}")
    line(f"Event: {sig['event_key']}")
    line(f"Status: {sig['status']}   Priority: {sig['priority']}")
    line(f"Runs: first_seen={sig['first_seen_run']}  last_seen={sig['last_seen_run']}")
    line(f"Metrics: IC={sig['ic']}  IC025={sig['ic025']}  IC975={sig['ic975']}")
    line(f"Counts: n11={sig['n11']} n1p={sig['n1p']} np1={sig['np1']} npp={sig['npp']}")
    line("")
    line("Notes / Rationale:")
    notes = (sig["notes"] or "").splitlines() or [""]
    for n in notes:
        line(f"- {n}", dy=14)

    line("")
    line("Status History:")
    if not history:
        line("  (no transitions recorded)")
    else:
        for h in history:
            line(f"- {h['created_at']}: {h['from_status']} -> {h['to_status']} by {h['changed_by']} (run={h['run_id']})")
            if h.get("reason"):
                line(f"    reason: {h['reason']}", dy=14)

    line("")
    line("Provenance:")
    for k, v in provenance.items():
        line(f"- {k}: {v}", dy=14)

    c.save()
    return pdf_path