"""
run.py – legacy planner + writer + Open-Interpreter DevAgent pipeline.
Use _this_ entrypoint if you want code edits with Open Interpreter.
"""
import sys
from planner_agent import PlannerAgent
from dev_agent import DevAgent  # Open-Interpreter implementation
from writer_agent import WriterAgent


def main(goal: str) -> int:
    plan = PlannerAgent().plan(goal)
    if not plan:
        print("Could not parse any tasks from your goal.")
        return 1

    print("Planned tasks:")
    for ttype, desc in plan:
        print(f" • [{ttype.upper()}] {desc}")

    for ttype, desc in plan:
        if ttype == "code":
            print(f"\n=== CODE: {desc}")
            if not DevAgent().implement_with_retry(desc):
                print("❌  Code task failed irrecoverably. Stopping.")
                return 1
        else:
            print(f"\n=== DOC : {desc}")
            WriterAgent().generate_document(desc)
            print("✅  Documentation committed.")
    return 0


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or input("Goal > ")
    sys.exit(main(goal))
