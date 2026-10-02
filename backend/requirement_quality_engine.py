# ============================================================
# REQUIREMENT QUALITY ENGINE
# HARA AI Assistant
# ============================================================

import re


def check_requirements_quality(requirements):
    """Run deterministic quality checks on candidate FSR/TSR requirements."""
    results = []
    if not requirements:
        return results

    weak_terms = [
        "should", "may", "could", "appropriate", "adequate",
        "sufficient", "as needed", "if possible", "etc.",
    ]

    for item in requirements:
        requirement_id = item.get("id", "REQ-001")
        text = str(item.get("requirement", "")).strip()
        checks = []

        checks.append({
            "Check": "Requirement is not empty",
            "Status": "PASS" if text else "FAIL",
            "Details": "Requirement text is present." if text else "Requirement text is missing."
        })

        has_shall = bool(re.search(r"\bshall\b", text, flags=re.IGNORECASE))
        checks.append({
            "Check": "Uses mandatory 'shall' wording",
            "Status": "PASS" if has_shall else "REVIEW",
            "Details": "Mandatory 'shall' wording is present." if has_shall else "No 'shall' wording detected; review requirement wording."
        })

        found_weak = [term for term in weak_terms if re.search(rf"\b{re.escape(term)}\b", text, flags=re.IGNORECASE)]
        checks.append({
            "Check": "Avoids weak or vague wording",
            "Status": "FAIL" if found_weak else "PASS",
            "Details": "No configured weak/vague terms detected." if not found_weak else "Review vague wording: " + ", ".join(found_weak)
        })

        action_terms = [
            "detect", "monitor", "prevent", "transition", "inhibit",
            "provide", "store", "communicate", "identify", "control", "maintain",
        ]
        found_actions = [term for term in action_terms if re.search(rf"\b{re.escape(term)}\b", text, flags=re.IGNORECASE)]
        checks.append({
            "Check": "Contains an observable engineering action",
            "Status": "PASS" if found_actions else "REVIEW",
            "Details": ("Detected action term(s): " + ", ".join(found_actions)) if found_actions else "No configured engineering action term detected; review whether the requirement is sufficiently testable."
        })

        clauses = [p.strip() for p in re.split(r"\band\b", text, flags=re.IGNORECASE) if p.strip()]
        excessive = len(clauses) >= 4
        checks.append({
            "Check": "Avoids excessive combined clauses",
            "Status": "REVIEW" if excessive else "PASS",
            "Details": "Multiple clauses detected; consider splitting into separate atomic requirements." if excessive else "No excessive clause combination detected."
        })

        failed = sum(c["Status"] == "FAIL" for c in checks)
        review = sum(c["Status"] == "REVIEW" for c in checks)
        passed = sum(c["Status"] == "PASS" for c in checks)
        overall = "FAIL" if failed else ("REVIEW" if review else "PASS")

        results.append({
            "id": requirement_id,
            "requirement": text,
            "checks": checks,
            "passed": passed,
            "review": review,
            "failed": failed,
            "overall": overall,
        })

    return results


def get_requirement_quality_review_note():
    return (
        "Requirement quality checks are deterministic AI-assistance checks. "
        "They support engineering review but do not establish ISO 26262 compliance. "
        "Final requirement acceptance must be performed by an authorized functional-safety engineer."
    )
