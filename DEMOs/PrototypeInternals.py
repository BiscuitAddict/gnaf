import uuid
from dataclasses import dataclass, field
from typing import List

# =====================================================
# TESM STATES
# =====================================================

CREATED = "CREATED"
VALIDATED = "VALIDATED"
MATCHED = "MATCHED"
DISPATCHED = "DISPATCHED"
IN_PROGRESS = "IN_PROGRESS"
SUBMITTED = "SUBMITTED"
UNDER_REVIEW = "UNDER_REVIEW"
FINALIZED = "FINALIZED"
REJECTED = "REJECTED"


# =====================================================
# TASK MODEL
# =====================================================

@dataclass
class Task:
    id: str
    description: str
    requirements: List[str]
    reward: float

    state: str = CREATED

    assigned_guild: str = ""
    assigned_node: str = ""

    board_notes: str = ""
    submission: str = ""

    history: List[str] = field(default_factory=list)


# =====================================================
# LEDGER
# =====================================================

def ledger(task: Task, actor: str, action: str):
    entry = f"[{actor}] {action}"
    task.history.append(entry)


# =====================================================
# REPORTING
# =====================================================

def print_report(task: Task):

    print("\n" + "=" * 60)
    print("GNAF TASK REPORT")
    print("=" * 60)

    print(f"Task ID        : {task.id}")
    print(f"Description    : {task.description}")
    print(f"Requirements   : {task.requirements}")
    print(f"Reward         : {task.reward}")

    print(f"\nCurrent State  : {task.state}")
    print(f"Guild          : {task.assigned_guild}")
    print(f"Node           : {task.assigned_node}")

    print("\nTimeline")

    for i, event in enumerate(task.history, start=1):
        print(f"{i}. {event}")

    print("=" * 60)


# =====================================================
# MAIN LOOP
# =====================================================

def main():

    print("\n=== GNAF PROTOCOL REFEREE ===\n")

    # -------------------------------------------------
    # CONTRACTOR
    # -------------------------------------------------

    print("[CONTRACTOR]")

    description = input("Task Description: ")

    requirements = [
        x.strip()
        for x in input("Requirements (comma separated): ").split(",")
    ]

    reward = float(input("Reward: "))

    task = Task(
        id=str(uuid.uuid4()),
        description=description,
        requirements=requirements,
        reward=reward,
    )

    task.state = VALIDATED

    ledger(task, "CONTRACTOR", "Created Task")
    ledger(task, "SYSTEM", "State -> VALIDATED")

    # -------------------------------------------------
    # MAIN TESM LOOP
    # -------------------------------------------------

    while task.state != FINALIZED:

        # =============================================
        # VALIDATED
        # =============================================

        if task.state == VALIDATED:

            print("\n[FEDERATION]")
            print("Assign Guild")

            guild = input("Guild Name: ")

            task.assigned_guild = guild
            task.state = MATCHED

            ledger(task, "FEDERATION", f"Assigned Guild: {guild}")
            ledger(task, "SYSTEM", "State -> MATCHED")

        # =============================================
        # MATCHED
        # =============================================

        elif task.state == MATCHED:

            print(f"\n[GUILD] ({task.assigned_guild})")

            accept = input("Accept Contract? (y/n): ")

            if accept.lower() != "y":

                ledger(
                    task,
                    "GUILD",
                    "Rejected Contract"
                )

                task.state = VALIDATED

                ledger(
                    task,
                    "SYSTEM",
                    "Returned -> VALIDATED"
                )

                continue

            notes = input("Board Notes: ")
            node = input("Assigned Node: ")

            task.board_notes = notes
            task.assigned_node = node

            task.state = DISPATCHED

            ledger(
                task,
                "GUILD",
                f"Accepted Contract; Assigned {node}"
            )

            ledger(task, "SYSTEM", "State -> DISPATCHED")

        # =============================================
        # DISPATCHED
        # =============================================

        elif task.state == DISPATCHED:

            print(f"\n[NODE] ({task.assigned_node})")

            work_notes = input("Work Notes: ")
            submission = input("Submission: ")

            task.submission = submission

            task.state = SUBMITTED

            ledger(
                task,
                "NODE",
                f"Submitted Work: {work_notes}"
            )

            ledger(task, "SYSTEM", "State -> SUBMITTED")

        # =============================================
        # SUBMITTED
        # =============================================

        elif task.state == SUBMITTED:

            print("\n[CONTRACTOR]")

            print("1 = Fixed")
            print("2 = Not Fixed")
            print("3 = Retract Contract")

            choice = input("> ")

            if choice == "1":

                task.state = UNDER_REVIEW

                ledger(
                    task,
                    "CONTRACTOR",
                    "Marked Fixed"
                )

                ledger(
                    task,
                    "SYSTEM",
                    "State -> UNDER_REVIEW"
                )

            elif choice == "2":

                reason = input("Failure Reason: ")

                ledger(
                    task,
                    "CONTRACTOR",
                    f"Rejected Submission: {reason}"
                )

                task.state = VALIDATED

                ledger(
                    task,
                    "SYSTEM",
                    "Returned -> VALIDATED"
                )

            elif choice == "3":

                ledger(
                    task,
                    "CONTRACTOR",
                    "Retracted Contract"
                )

                task.state = REJECTED

                ledger(
                    task,
                    "SYSTEM",
                    "State -> REJECTED"
                )

                break

        # =============================================
        # UNDER REVIEW
        # =============================================

        elif task.state == UNDER_REVIEW:

            print(f"\n[GUILD] ({task.assigned_guild})")

            release = input(
                "Release Reward? (y/n): "
            )

            if release.lower() == "y":

                task.state = FINALIZED

                ledger(
                    task,
                    "GUILD",
                    "Released Reward"
                )

                ledger(
                    task,
                    "SYSTEM",
                    "State -> FINALIZED"
                )

            else:

                ledger(
                    task,
                    "GUILD",
                    "Declined Release"
                )

                task.state = VALIDATED

                ledger(
                    task,
                    "SYSTEM",
                    "Returned -> VALIDATED"
                )

        print_report(task)

    # =================================================
    # FINAL REPORT
    # =================================================

    print("\nFINAL OUTCOME")
    print_report(task)


if __name__ == "__main__":
    main()