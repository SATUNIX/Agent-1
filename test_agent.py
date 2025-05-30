"""
Run pytest (env TEST_COMMAND) or fall back to syntax checks.
"""
import subprocess, os, sys


class TestAgent:
    def __init__(self):
        self.cmd = os.getenv("TEST_COMMAND", "pytest").split()

    # ──────────────────────────────────────────────────────────────────────
    def run(self) -> tuple[bool, str]:
        try:
            res = subprocess.run(
                self.cmd, capture_output=True, text=True, timeout=300
            )
        except FileNotFoundError:
            return self._syntax_only()

        ok = res.returncode == 0
        return ok, res.stdout + res.stderr

    # ──────────────────────────────────────────────────────────────────────
    def _syntax_only(self) -> tuple[bool, str]:
        py_files = [
            f
            for f in os.popen("git ls-files -o -m --exclude-standard").read().splitlines()
            if f.endswith(".py")
        ]
        for f in py_files:
            if subprocess.run([sys.executable, "-m", "py_compile", f]).returncode:
                return False, f"syntax error in {f}"
        return True, "syntax-only check passed"
