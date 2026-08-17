"""
Run history tracking for the Data Rescue Agent, backed by Firestore.
This gives the agent persistent memory across sessions -- it can look
back at what it's cleaned before, not just what's happening right now.
"""

import os
from datetime import datetime, timezone
from google.cloud import firestore

_db = None


def _get_db():
    global _db
    if _db is None:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        _db = firestore.Client(project=project_id)
    return _db


def log_run(file_name: str, before_score: int, after_score: int, changes_summary: list, issues_found: int) -> None:
    """Logs a completed cleaning run to Firestore. Called internally after a fix, not directly by the agent."""
    try:
        db = _get_db()
        db.collection("rescue_runs").add({
            "file_name": file_name,
            "before_score": before_score,
            "after_score": after_score,
            "improvement": after_score - before_score,
            "changes_summary": changes_summary,
            "issues_found": issues_found,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        # Don't let a logging failure break the actual cleaning result
        print(f"Warning: failed to log run history: {e}")


def get_run_history(limit: int = 10) -> str:
    """Retrieves a summary of past file-cleaning runs performed by this agent.

    Use this tool when the user asks about past activity, run history,
    what files have been cleaned before, or wants a summary of the
    agent's work over time.

    Args:
        limit: Maximum number of past runs to return (default 10, most recent first).

    Returns:
        A formatted summary of past runs, or a message if there's no history yet.
    """
    try:
        db = _get_db()
        docs = (
            db.collection("rescue_runs")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        runs = [doc.to_dict() for doc in docs]
    except Exception as e:
        return f"Unable to retrieve run history: {e}"

    if not runs:
        return "No run history yet. This will be the first file I've cleaned!"

    lines = [f"Here are the last {len(runs)} file(s) I've cleaned:\n"]
    for run in runs:
        lines.append(
            f"- {run.get('file_name', 'unknown')}: "
            f"{run.get('before_score', '?')}/100 -> {run.get('after_score', '?')}/100 "
            f"(+{run.get('improvement', '?')} points), "
            f"{run.get('issues_found', '?')} issues found "
            f"at {run.get('timestamp', 'unknown time')}"
        )
    return "\n".join(lines)