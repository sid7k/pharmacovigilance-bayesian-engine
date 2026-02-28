import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("data/registry/registry.sqlite")

def get_conn(db_path: str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path.as_posix(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS signal_registry (
      signal_id TEXT PRIMARY KEY,
      drug_key TEXT NOT NULL,
      event_key TEXT NOT NULL,
      status TEXT NOT NULL,
      priority INTEGER NOT NULL DEFAULT 3,
      first_seen_run TEXT,
      last_seen_run TEXT,
      ic REAL,
      ic025 REAL,
      ic975 REAL,
      n11 INTEGER,
      n1p INTEGER,
      np1 INTEGER,
      npp INTEGER,
      notes TEXT DEFAULT "",
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS signal_status_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      signal_id TEXT NOT NULL,
      from_status TEXT,
      to_status TEXT NOT NULL,
      changed_by TEXT,
      reason TEXT,
      run_id TEXT,
      created_at TEXT DEFAULT (datetime('now'))
    );
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_signal_registry_status ON signal_registry(status);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_signal_registry_drug_event ON signal_registry(drug_key, event_key);")
    conn.commit()