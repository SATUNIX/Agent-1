# === run_loop.py ===
from agents import ManagerAgent, LLMDevAgent
from memory import Memory
import sys


def main(user_request: str) -> int:
    manager = ManagerAgent()
    developer = LLMDevAgent()
    memory = Memory()

    # Manager step
    plan = manager.act(memory, f"The user requests: {user_request}. Provide a step-by-step plan.")
    print("\n--- Manager Plan ---\n", plan)
    memory.update_from_agent(manager.name, plan)
    memory.trim()

    # Dev step (simplified: first step only)
    dev_task = f"Follow the plan: {memory.last_action_result}. Implement the requirement."
    dev_out = developer.act(memory, dev_task)
    print("\n--- DevAgent Output ---\n", dev_out)
    memory.update_from_agent(developer.name, dev_out)
    memory.trim()

    # Manager review
    review = manager.act(memory, "Review the development output and provide the final result for the user.")
    print("\n--- Final Manager Response ---\n", review)

    # You might check success criteria here; assume success
    return 0


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or "Build a simple calculator that adds two numbers."
    sys.exit(main(goal))
