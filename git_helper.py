"""
Git helpers – minimal, no GitPython needed.
"""
import subprocess, datetime


def _run(cmd: list[str], check: bool = True):
    subprocess.run(cmd, check=check, capture_output=not check)


def ensure_clean_state() -> None:
    """Stash anything dirty so each task starts from HEAD."""
    _run(["git", "stash", "--include-untracked", "--quiet"], check=False)


def commit_all(msg: str) -> None:
    """Stage everything and commit with an ISO-timestamp prefix, then clear stash."""
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    _run(["git", "add", "-A"])
    _run(["git", "commit", "-m", f"{ts}  {msg}"])
    # drop temp stash created by ensure_clean_state (ignore if none)
    _run(["git", "stash", "drop"], check=False)


def revert_working_copy() -> None:
    """Undo *all* uncommitted edits and drop the temporary stash."""
    _run(["git", "reset", "--hard", "HEAD"])
    _run(["git", "clean", "-fd"])
    _run(["git", "stash", "drop"], check=False)
