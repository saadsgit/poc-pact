"""Small SQLite persistence layer for POC Pact."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from poc_pact.config import DATABASE_PATH
from poc_pact.models import ConnectionDraft, PocPlan


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _connect(path: Path = DATABASE_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(path: Path = DATABASE_PATH) -> None:
    with _connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_name TEXT NOT NULL DEFAULT '',
                contact_role TEXT NOT NULL DEFAULT '',
                contact_company TEXT NOT NULL DEFAULT '',
                contact_country TEXT NOT NULL DEFAULT '',
                contact_email TEXT NOT NULL DEFAULT '',
                your_company TEXT NOT NULL DEFAULT '',
                your_country TEXT NOT NULL DEFAULT '',
                meeting_context TEXT NOT NULL DEFAULT '',
                collaboration_idea TEXT NOT NULL DEFAULT '',
                next_step TEXT NOT NULL DEFAULT '',
                confidence_notes_json TEXT NOT NULL DEFAULT '[]',
                raw_notes TEXT NOT NULL DEFAULT '',
                source_filename TEXT NOT NULL DEFAULT '',
                ai_mode TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Captured',
                poc_plan_json TEXT,
                follow_up_message TEXT NOT NULL DEFAULT '',
                outcome_type TEXT NOT NULL DEFAULT '',
                estimated_value REAL NOT NULL DEFAULT 0,
                currency TEXT NOT NULL DEFAULT 'USD',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                your_company TEXT NOT NULL DEFAULT '',
                your_country TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT ''
            )
            """
        )
        _add_missing_columns(connection)


def _add_missing_columns(connection: sqlite3.Connection) -> None:
    """Add columns introduced after the first release to existing databases."""
    existing = {
        row["name"] for row in connection.execute("PRAGMA table_info(connections)")
    }
    if "contact_email" not in existing:
        connection.execute(
            "ALTER TABLE connections ADD COLUMN contact_email TEXT NOT NULL DEFAULT ''"
        )


def get_profile(path: Path = DATABASE_PATH) -> dict[str, str]:
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT your_company, your_country FROM profile WHERE id = 1"
        ).fetchone()
    if row:
        return {
            "your_company": row["your_company"],
            "your_country": row["your_country"],
        }
    return {"your_company": "", "your_country": ""}


def save_profile(
    your_company: str, your_country: str, path: Path = DATABASE_PATH
) -> None:
    with _connect(path) as connection:
        connection.execute(
            """
            INSERT INTO profile (id, your_company, your_country, updated_at)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                your_company = excluded.your_company,
                your_country = excluded.your_country,
                updated_at = excluded.updated_at
            """,
            (your_company, your_country, _now()),
        )


def create_connection(
    draft: ConnectionDraft,
    *,
    raw_notes: str,
    source_filename: str,
    ai_mode: str,
    path: Path = DATABASE_PATH,
) -> int:
    now = _now()
    values = draft.to_dict()
    with _connect(path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO connections (
                contact_name, contact_role, contact_company, contact_country,
                contact_email, your_company, your_country, meeting_context,
                collaboration_idea, next_step, confidence_notes_json, raw_notes,
                source_filename, ai_mode, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                values["contact_name"],
                values["contact_role"],
                values["contact_company"],
                values["contact_country"],
                values["contact_email"],
                values["your_company"],
                values["your_country"],
                values["meeting_context"],
                values["collaboration_idea"],
                values["next_step"],
                json.dumps(values["confidence_notes"]),
                raw_notes,
                source_filename,
                ai_mode,
                now,
                now,
            ),
        )
        return int(cursor.lastrowid)


def update_connection_fields(
    connection_id: int,
    fields_to_update: dict[str, Any],
    path: Path = DATABASE_PATH,
) -> None:
    """Update editable connection fields. Only known columns are written."""
    editable = {
        "contact_name",
        "contact_role",
        "contact_company",
        "contact_country",
        "contact_email",
        "your_company",
        "your_country",
        "meeting_context",
        "collaboration_idea",
        "next_step",
        "status",
        "follow_up_message",
    }
    updates = {key: value for key, value in fields_to_update.items() if key in editable}
    if not updates:
        return
    assignments = ", ".join(f"{column} = ?" for column in updates)
    values = [*updates.values(), _now(), connection_id]
    with _connect(path) as connection:
        connection.execute(
            f"UPDATE connections SET {assignments}, updated_at = ? WHERE id = ?",
            values,
        )


def list_connections(path: Path = DATABASE_PATH) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        rows = connection.execute(
            "SELECT * FROM connections ORDER BY updated_at DESC, id DESC"
        ).fetchall()
    return [_decode_row(row) for row in rows]


def get_connection(
    connection_id: int, path: Path = DATABASE_PATH
) -> dict[str, Any] | None:
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT * FROM connections WHERE id = ?", (connection_id,)
        ).fetchone()
    return _decode_row(row) if row else None


def update_status(connection_id: int, status: str, path: Path = DATABASE_PATH) -> None:
    with _connect(path) as connection:
        connection.execute(
            "UPDATE connections SET status = ?, updated_at = ? WHERE id = ?",
            (status, _now(), connection_id),
        )


def save_poc_pack(
    connection_id: int,
    plan: PocPlan,
    follow_up_message: str,
    *,
    ai_mode: str,
    path: Path = DATABASE_PATH,
) -> None:
    with _connect(path) as connection:
        connection.execute(
            """
            UPDATE connections
            SET poc_plan_json = ?, follow_up_message = ?, ai_mode = ?,
                status = CASE WHEN status = 'Captured' THEN 'POC proposed' ELSE status END,
                updated_at = ?
            WHERE id = ?
            """,
            (
                json.dumps(plan.to_dict()),
                follow_up_message,
                ai_mode,
                _now(),
                connection_id,
            ),
        )


def save_outcome(
    connection_id: int,
    outcome_type: str,
    estimated_value: float,
    currency: str,
    path: Path = DATABASE_PATH,
) -> None:
    with _connect(path) as connection:
        connection.execute(
            """
            UPDATE connections
            SET outcome_type = ?, estimated_value = ?, currency = ?,
                status = CASE WHEN ? <> '' THEN 'Outcome recorded' ELSE status END,
                updated_at = ?
            WHERE id = ?
            """,
            (
                outcome_type,
                estimated_value,
                currency,
                outcome_type,
                _now(),
                connection_id,
            ),
        )


def _decode_row(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["confidence_notes"] = json.loads(item.pop("confidence_notes_json") or "[]")
    raw_plan = item.pop("poc_plan_json")
    item["poc_plan"] = json.loads(raw_plan) if raw_plan else None
    return item
