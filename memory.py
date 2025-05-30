# === memory.py ===
from typing import List

try:
    import tiktoken

    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")  # any tokenizer
except ImportError:
    enc = None


class Memory:
    """Global shared memory for all agents."""

    def __init__(self, initial_plan: str = ""):
        self.plan: str = initial_plan
        self.last_action_result: str = ""
        self.decisions: List[str] = []

    # ---------------------------------------------------------------------
    def update_from_agent(self, agent_name: str, agent_output: str):
        summary = self._summarize_output(agent_name, agent_output)
        self.last_action_result = summary
        self.decisions.append(f"{agent_name}: {summary}")
        if agent_name == "ManagerAgent" and "PLAN UPDATE:" in agent_output:
            self.plan = agent_output.split("PLAN UPDATE:")[-1].strip()

    # ---------------------------------------------------------------------
    def _summarize_output(self, agent_name: str, output: str) -> str:
        if agent_name == "DevAgent":
            if "Error" in output or "Exception" in output:
                return f"DevAgent error: {output.splitlines()[0]}"
            return "DevAgent completed code execution successfully."
        lines = output.strip().splitlines()
        return (lines[-1][:100] + ("..." if len(lines[-1]) > 100 else "")) if lines else output[:100]

    # ---------------------------------------------------------------------
    def _token_len(self, text: str) -> int:
        if enc:
            return len(enc.encode(text))
        return len(text)

    def trim(self, max_decisions: int = 5, max_tokens: int = 1500):
        """Trim memory: keep last `max_decisions` and ensure token budget."""
        if len(self.decisions) > max_decisions:
            older = self.decisions[:-max_decisions]
            summary = "; ".join(d.split(": ", 1)[-1] for d in older)
            self.decisions = [f"Earlier: {summary}"] + self.decisions[-max_decisions:]

        # token-based plan trimming
        while self._token_len(self.plan) > max_tokens:
            self.plan = self.plan[: int(len(self.plan) * 0.8)] + "..."
