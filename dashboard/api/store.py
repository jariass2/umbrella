"""Almacenamiento SQLite para runs y resultados de agentes."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "dashboard.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                formula_text TEXT NOT NULL,
                output_dir TEXT,
                status TEXT DEFAULT 'running',
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                agent_name TEXT NOT NULL,
                status TEXT NOT NULL,
                output_json TEXT,
                output_md TEXT,
                duration_s REAL,
                completed_at TEXT
            )
        """)
        conn.commit()


def create_run(product_name: str, formula_text: str, output_dir: str | None = None) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO runs (product_name, formula_text, output_dir, status, created_at) VALUES (?, ?, ?, 'running', ?)",
            (product_name, formula_text, output_dir, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return cur.lastrowid


def update_run_status(run_id: int, status: str):
    with _conn() as conn:
        completed_at = datetime.now(timezone.utc).isoformat() if status != "running" else None
        conn.execute(
            "UPDATE runs SET status = ?, completed_at = COALESCE(?, completed_at) WHERE id = ?",
            (status, completed_at, run_id),
        )
        conn.commit()


def save_agent_result(run_id: int, agent_name: str, status: str,
                      output_json: str | None = None, output_md: str | None = None,
                      duration_s: float | None = None):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO agent_results (run_id, agent_name, status, output_json, output_md, duration_s, completed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, agent_name, status, output_json, output_md, duration_s,
             datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


def get_run(run_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return dict(row) if row else None


def get_agent_results(run_id: int) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_results WHERE run_id = ? ORDER BY id", (run_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def list_runs(limit: int = 20) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def load_run_results(run_id: int) -> dict[str, dict]:
    """Devuelve un dict {agent_name: output_json_parsed} para un run."""
    results = {}
    for r in get_agent_results(run_id):
        if r["output_json"]:
            try:
                results[r["agent_name"]] = json.loads(r["output_json"])
            except json.JSONDecodeError:
                results[r["agent_name"]] = {"raw": r["output_json"]}
    return results
