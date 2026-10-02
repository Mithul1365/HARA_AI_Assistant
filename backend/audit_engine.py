# ============================================================
# AUDIT / DECISION HISTORY ENGINE
# HARA AI Assistant
# ============================================================

from datetime import datetime, timezone
import json
from pathlib import Path


def _utc_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_audit_event(
    history_path,
    event,
    details,
    hara_id="HARA-001",
    asil=None,
    safety_goal_id=None,
    fsr_id=None,
    tsr_ids=None,
):
    """Append one engineering decision/action to a local audit log."""
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        history = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(history, list):
            history = []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        history = []

    history.append(
        {
            "timestamp_utc": _utc_timestamp(),
            "event": event,
            "details": details,
            "HARA ID": hara_id,
            "ASIL": asil or "",
            "Safety Goal ID": safety_goal_id or "",
            "FSR ID": fsr_id or "",
            "TSR IDs": ", ".join(tsr_ids or []),
        }
    )

    path.write_text(
        json.dumps(history, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_audit_history(history_path):
    """Load local audit history, newest event first."""
    path = Path(history_path)

    try:
        history = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(history, list):
            return []
        return list(reversed(history))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def clear_audit_history(history_path):
    """Clear the local audit history file."""
    path = Path(history_path)
    if path.exists():
        path.unlink()


def get_audit_review_note():
    return (
        "Audit history records AI-assisted engineering actions and decision "
        "context for review. It is not an approval record and does not replace "
        "the authorized functional-safety engineer's review or sign-off."
    )
