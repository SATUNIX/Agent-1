"""
Enhanced planner/router: breaks a goal into [Code] / [Doc] tasks.
Retries once on Ollama timeout, with 300-second ceiling.
"""
import os, requests, time


class PlannerAgent:
    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("PLANNER_MODEL", "deepseek-r1:7b")
        self.api = os.getenv("OLLAMA_API", "http://localhost:11434/api/generate")

    # ──────────────────────────────────────────────────────────────────────
    def plan(self, goal: str) -> list[tuple[str, str]]:
        prompt = (
            "You are a senior tech-lead assistant.  Break the goal below into "
            "an ordered checklist of independent tasks.  Prefix every task "
            "with either [Code] or [Doc].  Only return the list.\n\nGoal:\n" + goal
        )
        raw = self._llm_with_retry(prompt)
        return self._parse(raw)

    # ──────────────────────────────────────────────────────────────────────
    def _llm_with_retry(self, prompt: str) -> str:
        body = {"model": self.model, "prompt": prompt, "stream": False}
        for attempt in (1, 2):
            try:
                r = requests.post(self.api, json=body, timeout=300)
                r.raise_for_status()
                return r.json()["response"]
            except requests.Timeout:
                if attempt == 1:
                    print("Planner LLM timed out – retrying once…")
                    time.sleep(1)
                    continue
                raise

    @staticmethod
    def _parse(text: str) -> list[tuple[str, str]]:
        tasks = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            line = line.lstrip("•").lstrip("0123456789. ").strip()
            if line.lower().startswith("[code]"):
                tasks.append(("code", line[6:].strip()))
            elif line.lower().startswith("[doc]"):
                tasks.append(("doc", line[5:].strip()))
        return tasks
