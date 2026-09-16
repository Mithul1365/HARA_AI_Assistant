# ============================================================
# ENGINEERING REVIEW / APPROVAL ENGINE
# HARA AI Assistant
# ============================================================

from datetime import datetime, timezone
import json
from pathlib import Path


def _utc_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_review_decisions(path):
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def save_review_decision(
    path,
    artifact_type,
    artifact_id,
    decision,
    reviewer_name,
    comment="",
):
    """
    Record an authorized engineer's review decision.

    This is a workflow/audit aid only. It does not perform autonomous
    safety approval and does not establish ISO 26262 compliance.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    decisions = load_review_decisions(path)

    record = {
        "timestamp_utc": _utc_timestamp(),
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "decision": decision,
        "reviewer_name": reviewer_name.strip(),
        "comment": comment.strip(),
    }

    decisions.append(record)

    path.write_text(
        json.dumps(decisions, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return record


def clear_review_decisions(path):
    path = Path(path)
    if path.exists():
        path.unlink()


def get_latest_review_decision(decisions, artifact_type, artifact_id):
    for item in reversed(decisions):
        if (
            item.get("artifact_type") == artifact_type
            and item.get("artifact_id") == artifact_id
        ):
            return item
    return None


def get_review_status(decisions, artifact_type, artifact_id):
    latest = get_latest_review_decision(
        decisions,
        artifact_type,
        artifact_id,
    )
    return latest.get("decision", "Pending Review") if latest else "Pending Review"


def get_review_note():
    return (
        "Engineering review decisions are recorded only after the reviewer "
        "confirms that they are an authorized functional-safety engineer. "
        "This workflow does not provide autonomous safety approval or establish "
        "ISO 26262 compliance."
    )
