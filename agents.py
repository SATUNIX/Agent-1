# === agents.py ===
import os, requests, subprocess, tempfile, atexit

from memory import Memory

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


class BaseAgent:
    def __init__(self, name: str, role: str, model: str | None = None):
        self.name = name
        self.role = role
        self.model = model or os.getenv("AGENT_MODEL", "deepseek-r1:7b")

    # ------------------------------------------------------------------
    def _format_prompt(self, memory: Memory, task: str) -> str:
        ctx = (
            "The agents share the following context:\n"
            f"- Ongoing Plan: {memory.plan}\n"
            f"- Last Result: {memory.last_action_result}\n"
            f"- Recent Decisions:\n"
            + "\n".join(f"  * {d}" for d in memory.decisions[-5:])
            + "\n\n"
        )
        return f"You are {self.name}. {self.role}\n\n{ctx}User Task: {task}\n"

    # ------------------------------------------------------------------
    def _ollama_call(self, prompt: str, timeout: int = 300) -> str:
        payload = {"model": self.model, "prompt": prompt}
        r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=timeout)
        r.raise_for_status()
        if r.headers.get("content-type", "").startswith("application/json"):
            data = r.json()
            return data.get("output") or data.get("response") or ""
        return r.text

    # ------------------------------------------------------------------
    def act(self, memory: Memory, task: str) -> str:
        prompt = self._format_prompt(memory, task)
        return self._ollama_call(prompt)


class ManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "ManagerAgent",
            "Plan tasks and coordinate agents. Use <think>...</think> for reasoning; update the plan when needed.",
        )


class LLMDevAgent(BaseAgent):
    """
    Lightweight LLM-only developer (kept here) so we don’t collide with
    the legacy Open-Interpreter DevAgent that lives in dev_agent.py.
    """

    def __init__(self):
        super().__init__(
            "LLMDevAgent",
            "Write and (optionally) run code. Show reasoning in <think>...</think>. "
            "If you output code (```python) it will be executed.",
            model=os.getenv("DEV_MODEL", "deepseek-coder"),
        )
        self._temp_files: list[str] = []
        atexit.register(self._cleanup_temps)

    # ------------------------------------------------------------------
    def act(self, memory: Memory, task: str) -> str:
        llm_output = super().act(memory, task)
        code = self._extract_code(llm_output)
        if code:
            exec_result = self._run_code(code)
            llm_output += f"\n\n[Execution Result]: {exec_result}"
        return llm_output

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_code(text: str) -> str:
        if "```" not in text:
            return ""
        try:
            return text.split("```")[1]
        except IndexError:
            return ""

    # ------------------------------------------------------------------
    def _run_code(self, code: str) -> str:
        if not code.strip():
            return "No code to execute."
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
        tmp.write(code.encode())
        tmp.close()
        self._temp_files.append(tmp.name)
        try:
            res = subprocess.run(
                ["python", tmp.name], capture_output=True, text=True, timeout=15
            )
            return res.stdout or res.stderr
        except Exception as e:
            return f"Execution error: {e}"

    # ------------------------------------------------------------------
    def _cleanup_temps(self):
        for path in self._temp_files:
            try:
                os.remove(path)
            except OSError:
                pass
