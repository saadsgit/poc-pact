"""SQLite persistence layer for POC Pact.

Data is organized as companies that each contain one or more contacts.
A company moves through stages (recorded in stage_history); individual
contacts hold their own discussion notes, POC pack, and follow-up message.
"""

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
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                your_company TEXT NOT NULL DEFAULT '',
                your_country TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL DEFAULT '',
                company_country TEXT NOT NULL DEFAULT '',
                your_company TEXT NOT NULL DEFAULT '',
                your_country TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Captured',
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
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                contact_name TEXT NOT NULL DEFAULT '',
                contact_role TEXT NOT NULL DEFAULT '',
                contact_email TEXT NOT NULL DEFAULT '',
                meeting_context TEXT NOT NULL DEFAULT '',
                collaboration_idea TEXT NOT NULL DEFAULT '',
                next_step TEXT NOT NULL DEFAULT '',
                discussion TEXT NOT NULL DEFAULT '',
                confidence_notes_json TEXT NOT NULL DEFAULT '[]',
                raw_notes TEXT NOT NULL DEFAULT '',
                source_filename TEXT NOT NULL DEFAULT '',
                ai_mode TEXT NOT NULL DEFAULT '',
                poc_plan_json TEXT,
                follow_up_message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS stage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                stage TEXT NOT NULL,
                changed_at TEXT NOT NULL
            )
            """
        )
        _migrate_legacy_connections(connection)


def _migrate_legacy_connections(connection: sqlite3.Connection) -> None:
    """Convert the pre-restructure `connections` table into companies + contacts."""
    tables = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if "connections" not in tables:
        return
    already = connection.execute("SELECT COUNT(*) AS n FROM companies").fetchone()["n"]
    if already:
        return

    for row in connection.execute("SELECT * FROM connections ORDER BY id"):
        data = dict(row)
        cursor = connection.execute(
            """
            INSERT INTO companies (
                company_name, company_country, your_company, your_country,
                status, outcome_type, estimated_value, currency, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("contact_company", ""),
                data.get("contact_country", ""),
                data.get("your_company", ""),
                data.get("your_country", ""),
                data.get("status", "Captured"),
                data.get("outcome_type", ""),
                data.get("estimated_value", 0) or 0,
                data.get("currency", "USD") or "USD",
                data.get("created_at", _now()),
                data.get("updated_at", _now()),
            ),
        )
        company_id = int(cursor.lastrowid)
        connection.execute(
            """
            INSERT INTO contacts (
                company_id, contact_name, contact_role, contact_email,
                meeting_context, collaboration_idea, next_step, discussion,
                confidence_notes_json, raw_notes, source_filename, ai_mode,
                poc_plan_json, follow_up_message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_id,
                data.get("contact_name", ""),
                data.get("contact_role", ""),
                data.get("contact_email", ""),
                data.get("meeting_context", ""),
                data.get("collaboration_idea", ""),
                data.get("next_step", ""),
                data.get("raw_notes", ""),
                data.get("confidence_notes_json", "[]"),
                data.get("raw_notes", ""),
                data.get("source_filename", ""),
                data.get("ai_mode", ""),
                data.get("poc_plan_json"),
                data.get("follow_up_message", ""),
                data.get("created_at", _now()),
                data.get("updated_at", _now()),
            ),
        )
        connection.execute(
            "INSERT INTO stage_history (company_id, stage, changed_at) VALUES (?, ?, ?)",
            (
                company_id,
                data.get("status", "Captured"),
                data.get("created_at", _now()),
            ),
        )
    connection.execute("ALTER TABLE connections RENAME TO connections_migrated")


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Companies and contacts
# ---------------------------------------------------------------------------
def find_company_by_name(
    company_name: str, path: Path = DATABASE_PATH
) -> dict[str, Any] | None:
    name = company_name.strip()
    if not name:
        return None
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT * FROM companies WHERE lower(company_name) = lower(?) LIMIT 1",
            (name,),
        ).fetchone()
    return dict(row) if row else None


def create_company(
    *,
    company_name: str,
    company_country: str,
    your_company: str,
    your_country: str,
    path: Path = DATABASE_PATH,
) -> int:
    now = _now()
    with _connect(path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO companies (
                company_name, company_country, your_company, your_country,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'Captured', ?, ?)
            """,
            (
                company_name.strip(),
                company_country.strip(),
                your_company.strip(),
                your_country.strip(),
                now,
                now,
            ),
        )
        company_id = int(cursor.lastrowid)
        connection.execute(
            "INSERT INTO stage_history (company_id, stage, changed_at) VALUES (?, 'Captured', ?)",
            (company_id, now),
        )
        return company_id


def add_contact_from_draft(
    company_id: int,
    draft: ConnectionDraft,
    *,
    discussion: str,
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
            INSERT INTO contacts (
                company_id, contact_name, contact_role, contact_email,
                meeting_context, collaboration_idea, next_step, discussion,
                confidence_notes_json, raw_notes, source_filename, ai_mode,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_id,
                values["contact_name"],
                values["contact_role"],
                values["contact_email"],
                values["meeting_context"],
                values["collaboration_idea"],
                values["next_step"],
                discussion,
                json.dumps(values["confidence_notes"]),
                raw_notes,
                source_filename,
                ai_mode,
                now,
                now,
            ),
        )
        connection.execute(
            "UPDATE companies SET updated_at = ? WHERE id = ?", (now, company_id)
        )
        return int(cursor.lastrowid)


def capture_connection(
    draft: ConnectionDraft,
    *,
    discussion: str,
    raw_notes: str,
    source_filename: str,
    ai_mode: str,
    path: Path = DATABASE_PATH,
) -> tuple[int, int]:
    """Create or reuse a company from the draft, then attach a contact.

    Returns (company_id, contact_id).
    """
    existing = find_company_by_name(draft.contact_company, path=path)
    if existing:
        company_id = int(existing["id"])
    else:
        company_id = create_company(
            company_name=draft.contact_company
            or draft.contact_name
            or "Unnamed company",
            company_country=draft.contact_country,
            your_company=draft.your_company,
            your_country=draft.your_country,
            path=path,
        )
    contact_id = add_contact_from_draft(
        company_id,
        draft,
        discussion=discussion,
        raw_notes=raw_notes,
        source_filename=source_filename,
        ai_mode=ai_mode,
        path=path,
    )
    return company_id, contact_id


def update_company_fields(
    company_id: int, fields_to_update: dict[str, Any], path: Path = DATABASE_PATH
) -> None:
    editable = {"company_name", "company_country", "your_company", "your_country"}
    updates = {k: v for k, v in fields_to_update.items() if k in editable}
    if not updates:
        return
    assignments = ", ".join(f"{column} = ?" for column in updates)
    values = [*updates.values(), _now(), company_id]
    with _connect(path) as connection:
        connection.execute(
            f"UPDATE companies SET {assignments}, updated_at = ? WHERE id = ?", values
        )


def update_contact_fields(
    contact_id: int, fields_to_update: dict[str, Any], path: Path = DATABASE_PATH
) -> None:
    editable = {
        "contact_name",
        "contact_role",
        "contact_email",
        "meeting_context",
        "collaboration_idea",
        "next_step",
        "discussion",
        "follow_up_message",
    }
    updates = {k: v for k, v in fields_to_update.items() if k in editable}
    if not updates:
        return
    assignments = ", ".join(f"{column} = ?" for column in updates)
    values = [*updates.values(), _now(), contact_id]
    with _connect(path) as connection:
        connection.execute(
            f"UPDATE contacts SET {assignments}, updated_at = ? WHERE id = ?", values
        )
        row = connection.execute(
            "SELECT company_id FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
        if row:
            connection.execute(
                "UPDATE companies SET updated_at = ? WHERE id = ?",
                (_now(), row["company_id"]),
            )


def delete_company(company_id: int, path: Path = DATABASE_PATH) -> None:
    with _connect(path) as connection:
        connection.execute("DELETE FROM companies WHERE id = ?", (company_id,))


def delete_contact(contact_id: int, path: Path = DATABASE_PATH) -> None:
    with _connect(path) as connection:
        connection.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))


def list_companies(
    *, include_closed: bool = False, search: str = "", path: Path = DATABASE_PATH
) -> list[dict[str, Any]]:
    """Return companies with their contacts.

    By default, closed companies are excluded (they live in the Completed view).
    `search` matches company name or any contact name (case-insensitive).
    """
    with _connect(path) as connection:
        companies = [
            dict(r)
            for r in connection.execute(
                "SELECT * FROM companies ORDER BY updated_at DESC, id DESC"
            )
        ]
        contacts_by_company: dict[int, list[dict[str, Any]]] = {}
        for row in connection.execute("SELECT * FROM contacts ORDER BY id"):
            contacts_by_company.setdefault(row["company_id"], []).append(
                _decode_contact(row)
            )

    needle = search.strip().lower()
    result = []
    for company in companies:
        if not include_closed and company["status"] == "Closed":
            continue
        company["contacts"] = contacts_by_company.get(company["id"], [])
        if needle:
            hay = [company["company_name"].lower()]
            hay += [c["contact_name"].lower() for c in company["contacts"]]
            if not any(needle in value for value in hay):
                continue
        result.append(company)
    return result


def list_completed(path: Path = DATABASE_PATH) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        companies = [
            dict(r)
            for r in connection.execute(
                "SELECT * FROM companies WHERE status = 'Closed' ORDER BY updated_at DESC"
            )
        ]
        for company in companies:
            company["contacts"] = [
                _decode_contact(r)
                for r in connection.execute(
                    "SELECT * FROM contacts WHERE company_id = ? ORDER BY id",
                    (company["id"],),
                )
            ]
            company["stage_history"] = [
                dict(r)
                for r in connection.execute(
                    "SELECT stage, changed_at FROM stage_history WHERE company_id = ? ORDER BY id",
                    (company["id"],),
                )
            ]
    return companies


def get_company(company_id: int, path: Path = DATABASE_PATH) -> dict[str, Any] | None:
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT * FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
        if not row:
            return None
        company = dict(row)
        company["contacts"] = [
            _decode_contact(r)
            for r in connection.execute(
                "SELECT * FROM contacts WHERE company_id = ? ORDER BY id", (company_id,)
            )
        ]
        company["stage_history"] = [
            dict(r)
            for r in connection.execute(
                "SELECT stage, changed_at FROM stage_history WHERE company_id = ? ORDER BY id",
                (company_id,),
            )
        ]
    return company


def get_contact(contact_id: int, path: Path = DATABASE_PATH) -> dict[str, Any] | None:
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
    return _decode_contact(row) if row else None


def update_stage(company_id: int, stage: str, path: Path = DATABASE_PATH) -> None:
    """Set the company's current stage and append a timestamped history entry."""
    now = _now()
    with _connect(path) as connection:
        current = connection.execute(
            "SELECT status FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
        connection.execute(
            "UPDATE companies SET status = ?, updated_at = ? WHERE id = ?",
            (stage, now, company_id),
        )
        if not current or current["status"] != stage:
            connection.execute(
                "INSERT INTO stage_history (company_id, stage, changed_at) VALUES (?, ?, ?)",
                (company_id, stage, now),
            )


def save_contact_poc(
    contact_id: int,
    plan: PocPlan,
    follow_up_message: str,
    *,
    ai_mode: str,
    path: Path = DATABASE_PATH,
) -> None:
    now = _now()
    with _connect(path) as connection:
        connection.execute(
            """
            UPDATE contacts
            SET poc_plan_json = ?, follow_up_message = ?, ai_mode = ?, updated_at = ?
            WHERE id = ?
            """,
            (json.dumps(plan.to_dict()), follow_up_message, ai_mode, now, contact_id),
        )
        row = connection.execute(
            "SELECT company_id FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
        if row:
            company_id = row["company_id"]
            current = connection.execute(
                "SELECT status FROM companies WHERE id = ?", (company_id,)
            ).fetchone()
            if current and current["status"] == "Captured":
                connection.execute(
                    "UPDATE companies SET status = 'POC proposed', updated_at = ? WHERE id = ?",
                    (now, company_id),
                )
                connection.execute(
                    "INSERT INTO stage_history (company_id, stage, changed_at) VALUES (?, 'POC proposed', ?)",
                    (company_id, now),
                )
            else:
                connection.execute(
                    "UPDATE companies SET updated_at = ? WHERE id = ?",
                    (now, company_id),
                )


def save_outcome(
    company_id: int,
    outcome_type: str,
    estimated_value: float,
    currency: str,
    path: Path = DATABASE_PATH,
) -> None:
    with _connect(path) as connection:
        connection.execute(
            """
            UPDATE companies
            SET outcome_type = ?, estimated_value = ?, currency = ?, updated_at = ?
            WHERE id = ?
            """,
            (outcome_type, estimated_value, currency, _now(), company_id),
        )


def _decode_contact(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["confidence_notes"] = json.loads(item.pop("confidence_notes_json") or "[]")
    raw_plan = item.pop("poc_plan_json")
    item["poc_plan"] = json.loads(raw_plan) if raw_plan else None
    return item
