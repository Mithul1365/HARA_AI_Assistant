# ============================================================
# VERIFICATION EVIDENCE ENGINE
# HARA AI Assistant
# ============================================================

from datetime import datetime, timezone
import json
from pathlib import Path


def _timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_verification_records(path):
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def save_verification_record(
    path,
    artifact_id,
    artifact_name,
    verification_method,
    result,
    linked_requirement,
    evidence_reference="",
    notes="",
):
    """Save a verification-evidence mapping for engineering review."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    records = load_verification_records(path)

    record = {
        "timestamp_utc": _timestamp(),
        "artifact_id": artifact_id.strip(),
        "artifact_name": artifact_name.strip(),
        "verification_method": verification_method.strip(),
        "result": result,
        "linked_requirement": linked_requirement.strip(),
        "evidence_reference": evidence_reference.strip(),
        "notes": notes.strip(),
    }

    records.append(record)

    path.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return record


def clear_verification_records(path):
    path = Path(path)
    if path.exists():
        path.unlink()


def get_verification_note():
    return (
        "Verification evidence mappings are engineering traceability aids. "
        "A recorded result does not establish safety compliance or replace "
        "formal verification, validation, or authorized functional-safety review."
    )
