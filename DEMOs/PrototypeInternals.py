import uuid
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime
import sys


# =====================================================
# ROBUST STATE MACHINE
# =====================================================

class TaskState(Enum):
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    MATCHED = "MATCHED"
    DISPATCHED = "DISPATCHED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    FINALIZED = "FINALIZED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


ALLOWED_TRANSITIONS: Dict[TaskState, List[TaskState]] = {
    TaskState.CREATED: [TaskState.VALIDATED],
    TaskState.VALIDATED: [TaskState.MATCHED, TaskState.REJECTED, TaskState.CANCELLED],
    TaskState.MATCHED: [TaskState.DISPATCHED, TaskState.VALIDATED],
    TaskState.DISPATCHED: [TaskState.SUBMITTED],
    TaskState.SUBMITTED: [TaskState.UNDER_REVIEW, TaskState.VALIDATED, TaskState.REJECTED],
    TaskState.UNDER_REVIEW: [TaskState.FINALIZED, TaskState.VALIDATED],
    TaskState.FINALIZED: [],
    TaskState.REJECTED: [],
    TaskState.CANCELLED: [],
}


# =====================================================
# TASK MODEL
# =====================================================

@dataclass
class Task:
    id: str
    description: str
    requirements: List[str]
    reward: float

    state: TaskState = TaskState.CREATED
    assigned_guild: str = ""
    assigned_node: str = ""
    board_notes: str = ""
    submission: str = ""

    history: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_to_ledger(self, actor: str, action: str):
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{actor}] {action}"
        self.history.append(entry)
        self.updated_at = datetime.utcnow().isoformat()

    def can_transition_to(self, new_state: TaskState) -> bool:
        return new_state in ALLOWED_TRANSITIONS.get(self.state, [])


# =====================================================
# SAFE INPUT HELPERS
# =====================================================

def safe_input(prompt: str, default: Optional[str] = None) -> str:
    try:
        value = input(prompt).strip()
        if not value and default is not None:
            return default
        return value
    except (EOFError, KeyboardInterrupt):
        print("\n\nOperation cancelled by user.")
        sys.exit(0)


def safe_float(prompt: str, default: float = 0.0) -> float:
    while True:
        try:
            value = safe_input(prompt)
            if not value:
                return default
            return float(value)
        except ValueError:
            print("Error: Please enter a valid number.")


# =====================================================
# PERSISTENCE
# =====================================================

def save_task(task: Task, filename: str = None):
    if filename is None:
        filename = f"task_{task.id[:8]}.json"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "id": task.id,
                "description": task.description,
                "requirements": task.requirements,
                "reward": task.reward,
                "state": task.state.value,
                "assigned_guild": task.assigned_guild,
                "assigned_node": task.assigned_node,
                "board_notes": task.board_notes,
                "submission": task.submission,
                "history": task.history,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
            }, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save task: {e}")


# =====================================================
# REPORTING
# =====================================================

def print_report(task: Task):
    print("\n" + "=" * 70)
    print("GNAF TASK REPORT")
    print("=" * 70)
    print(f"Task ID        : {task.id}")
    print(f"Description    : {task.description}")
    print(f"Reward         : ${task.reward:,.2f}")
    print(f"Current State  : {task.state.value}")
    print(f"Guild          : {task.assigned_guild or '—'}")
    print(f"Node           : {task.assigned_node or '—'}")
    print(f"Created        : {task.created_at}")
    print("\nTimeline:")

    for i, event in enumerate(task.history, start=1):
        print(f"  {i:2d}. {event}")

    print("=" * 70)


# =====================================================
# MAIN DEMO
# =====================================================

def main():
    print("\n=== GNAF PROTOCOL REFEREE (Hardened Demo) ===\n")

    try:
        # Contractor creates task
        print("[CONTRACTOR]")
        description = safe_input("Task Description: ")
        req_input = safe_input("Requirements (comma separated): ")
        requirements = [x.strip() for x in req_input.split(",") if x.strip()]
        reward = safe_float("Reward ($): ")

        task = Task(
            id=str(uuid.uuid4()),
            description=description,
            requirements=requirements,
            reward=reward,
            state=TaskState.VALIDATED,
        )

        task.add_to_ledger("CONTRACTOR", "Created Task")
        task.add_to_ledger("SYSTEM", "State → VALIDATED")

        print(f"\nTask created successfully! ID: {task.id[:8]}...\n")

        # Main TESM Loop
        while task.state not in (TaskState.FINALIZED, TaskState.REJECTED, TaskState.CANCELLED):
            print_report(task)

            if task.state == TaskState.VALIDATED:
                print("[FEDERATION]")
                guild = safe_input("Assign Guild Name: ")
                if guild:
                    task.assigned_guild = guild
                    task.state = TaskState.MATCHED
                    task.add_to_ledger("FEDERATION", f"Assigned Guild: {guild}")
                    task.add_to_ledger("SYSTEM", "State → MATCHED")

            elif task.state == TaskState.MATCHED:
                print(f"[GUILD] ({task.assigned_guild})")
                accept = safe_input("Accept Contract? (y/n): ").lower()

                if accept != "y":
                    task.add_to_ledger("GUILD", "Rejected Contract")
                    task.state = TaskState.VALIDATED
                    task.add_to_ledger("SYSTEM", "Returned → VALIDATED")
                    continue

                notes = safe_input("Board Notes: ")
                node = safe_input("Assigned Node: ")

                task.board_notes = notes
                task.assigned_node = node
                task.state = TaskState.DISPATCHED

                task.add_to_ledger("GUILD", f"Accepted Contract | Assigned Node: {node}")
                task.add_to_ledger("SYSTEM", "State → DISPATCHED")

            elif task.state == TaskState.DISPATCHED:
                print(f"[NODE] ({task.assigned_node})")
                work_notes = safe_input("Work Notes: ")
                submission = safe_input("Submission (summary or link): ")

                task.submission = submission
                task.state = TaskState.SUBMITTED

                task.add_to_ledger("NODE", f"Submitted Work: {work_notes}")
                task.add_to_ledger("SYSTEM", "State → SUBMITTED")

            elif task.state == TaskState.SUBMITTED:
                print("\n[CONTRACTOR REVIEW]")
                print("1 = Accept (Fixed)")
                print("2 = Reject (Not Fixed)")
                print("3 = Retract Contract")

                choice = safe_input("> ")

                if choice == "1":
                    task.state = TaskState.UNDER_REVIEW
                    task.add_to_ledger("CONTRACTOR", "Marked as Fixed")
                    task.add_to_ledger("SYSTEM", "State → UNDER_REVIEW")
                elif choice == "2":
                    reason = safe_input("Rejection Reason: ")
                    task.add_to_ledger("CONTRACTOR", f"Rejected Submission: {reason}")
                    task.state = TaskState.VALIDATED
                    task.add_to_ledger("SYSTEM", "Returned → VALIDATED")
                elif choice == "3":
                    task.add_to_ledger("CONTRACTOR", "Retracted Contract")
                    task.state = TaskState.REJECTED
                    task.add_to_ledger("SYSTEM", "State → REJECTED")
                    break

            elif task.state == TaskState.UNDER_REVIEW:
                print(f"[GUILD] ({task.assigned_guild})")
                release = safe_input("Release Reward? (y/n): ").lower()

                if release == "y":
                    task.state = TaskState.FINALIZED
                    task.add_to_ledger("GUILD", "Released Reward")
                    task.add_to_ledger("SYSTEM", "State → FINALIZED")
                else:
                    task.add_to_ledger("GUILD", "Declined Release")
                    task.state = TaskState.VALIDATED
                    task.add_to_ledger("SYSTEM", "Returned → VALIDATED")

        # Final Report
        print("\n" + "═" * 70)
        print("FINAL OUTCOME")
        print("═" * 70)
        print_report(task)
        save_task(task)

    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Saving current task state for recovery...")
        if 'task' in locals():
            save_task(task)


if __name__ == "__main__":
    main()