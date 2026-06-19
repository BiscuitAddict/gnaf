import json
import uuid
import threading
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty
from datetime import datetime
import statistics


# =====================================================
# STATE MACHINE
# =====================================================

class TaskState(Enum):
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    MATCHED = "MATCHED"
    DISPATCHED = "DISPATCHED"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    FINALIZED = "FINALIZED"
    REJECTED = "REJECTED"


ALLOWED = {
    TaskState.CREATED: [TaskState.VALIDATED],
    TaskState.VALIDATED: [TaskState.MATCHED, TaskState.REJECTED],
    TaskState.MATCHED: [TaskState.DISPATCHED],
    TaskState.DISPATCHED: [TaskState.SUBMITTED],
    TaskState.SUBMITTED: [TaskState.UNDER_REVIEW],
    TaskState.UNDER_REVIEW: [TaskState.FINALIZED, TaskState.REJECTED],
    TaskState.REJECTED: [TaskState.VALIDATED],
}


# =====================================================
# TASK MODEL
# =====================================================

@dataclass
class Task:
    id: str
    description: str
    reward: float

    state: TaskState = TaskState.CREATED
    guild: str = ""
    node: str = ""
    history: list = field(default_factory=list)

    def log(self, actor, action):
        ts = datetime.utcnow().isoformat()
        self.history.append(f"[{ts}] [{actor}] {action}")


# =====================================================
# EVENT SYSTEM
# =====================================================

@dataclass
class Event:
    event_id: str
    timestamp: str
    module: str
    task_id: str
    event_type: str
    message: str
    metadata: dict


class EventStore:
    def __init__(self, path="gnaf_v32_log.jsonl"):
        self.path = path

    def append(self, event: Event):
        with open(self.path, "a") as f:
            f.write(json.dumps({
                "ts": datetime.utcnow().isoformat(),
                "event": event.__dict__
            }) + "\n")


class Broker:
    def __init__(self):
        self.topics = {}
        self.subs = {}
        self.store = None

    def attach_store(self, store):
        self.store = store

    def publish(self, topic, event):
        self.topics.setdefault(topic, Queue()).put(event)
        if self.store:
            self.store.append(event)

    def subscribe(self, topic, fn):
        self.subs.setdefault(topic, [])
        self.topics.setdefault(topic, Queue())

    def start(self):
        def worker(topic):
            while True:
                try:
                    event = self.topics[topic].get(timeout=1)
                    for fn in self.subs.get(topic, []):
                        fn(event)
                except Empty:
                    continue

        for t in self.topics:
            threading.Thread(target=worker, args=(t,), daemon=True).start()


# =====================================================
# PWDL (PASSIVE ONLY)
# =====================================================

class PWDL:
    def evaluate(self, data):
        return {
            "neutral": data.get("freedom", 0) + data.get("trust", 0),
            "autonomy": data.get("freedom", 0) * 2,
            "institutional": data.get("trust", 0) * 2
        }

    def divergence(self, results):
        vals = list(results.values())
        return statistics.pvariance(vals) if len(vals) > 1 else 0


def pwdl_audit(data, pwdl):
    results = pwdl.evaluate(data)
    return {
        "scores": results,
        "divergence": pwdl.divergence(results),
        "mode": "PASSIVE"
    }


# =====================================================
# GUILD SYSTEM
# =====================================================

class GuildRegistry:
    def __init__(self):
        self.guilds = {}

    def register(self, name, gid):
        self.guilds[name] = {
            "id": gid,
            "tasks": []
        }

    def assign(self, task, guild):
        self.guilds[guild]["tasks"].append(task.id)
        task.guild = guild


def binary_id(n):
    return format(n, "08b")


def choose_guild(registry):
    print("\n=== FEDERATION SELECTION ===\n")

    names = list(registry.guilds.keys())

    for i, name in enumerate(names):
        gid = registry.guilds[name]["id"]
        print(f"[{i}] {gid}:{name}")

    while True:
        try:
            c = int(input("\nSelect guild: "))
            if 0 <= c < len(names):
                return names[c]
        except:
            pass
        print("Invalid selection")


# =====================================================
# ENGINE
# =====================================================

class Engine:
    def __init__(self, broker, registry, pwdl):
        self.broker = broker
        self.registry = registry
        self.pwdl = pwdl

    def transition(self, task, new_state, actor):
        if new_state not in ALLOWED.get(task.state, []):
            print("❌ INVALID TRANSITION")
            return

        old = task.state
        task.state = new_state
        task.log(actor, f"{old.value} → {new_state.value}")

        event = Event(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            module="TASK",
            task_id=task.id,
            event_type="state_change",
            message=f"{actor} transitioned",
            metadata={"from": old.value, "to": new_state.value}
        )

        self.broker.publish("task", event)

    def run_pwdl(self, task):
        data = {"freedom": 0.7, "trust": 0.5}
        audit = pwdl_audit(data, self.pwdl)

        self.broker.publish("pwdl", Event(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            module="PWDL",
            task_id=task.id,
            event_type="analysis",
            message="evaluated",
            metadata=audit
        ))

        print("\n📊 PWDL divergence:", audit["divergence"])


# =====================================================
# BOOTSTRAP
# =====================================================

def bootstrap():
    registry = GuildRegistry()

    print("\n=== FEDERATION BOOTSTRAP ===\n")
    n = int(input("Number of guilds: "))

    for i in range(n):
        name = input(f"Guild {i+1}: ")
        registry.register(name, binary_id(i))
        print(f"Registered {binary_id(i)}:{name}")

    return registry


# =====================================================
# MAIN DEMO (v3.2 LOOP SYSTEM)
# =====================================================

if __name__ == "__main__":

    broker = Broker()
    broker.attach_store(EventStore())

    registry = bootstrap()
    pwdl = PWDL()
    engine = Engine(broker, registry, pwdl)

    broker.subscribe("task", lambda e: print(f"[TASK] {e.message}"))
    broker.subscribe("pwdl", lambda e: print(f"[PWDL] {e.message}"))
    broker.start()

    task = Task(
        id=str(uuid.uuid4()),
        description=input("\nTask description: "),
        reward=float(input("Reward: ") or 0)
    )

    task.log("USER", "created")

    engine.transition(task, TaskState.VALIDATED, "SYSTEM")

    # =================================================
    # LOOPABLE FEDERATION WORKFLOW (CORE v3.2 FEATURE)
    # =================================================

    while True:

        # ---- FEDERATION SELECTION ----
        guild = choose_guild(registry)

        # reset previous assignment safety
        task.guild = ""
        task.node = ""

        registry.assign(task, guild)
        engine.transition(task, TaskState.MATCHED, "FEDERATION")

        engine.transition(task, TaskState.DISPATCHED, "GUILD")

        input("\nPress ENTER when submitted...")
        engine.transition(task, TaskState.SUBMITTED, "NODE")

        engine.run_pwdl(task)

        # ---- REVIEW LOOP ----
        choice = input("\n1=Accept  2=Reject  3=Return: ")

        if choice == "1":
            engine.transition(task, TaskState.FINALIZED, "CONTRACTOR")
            break

        elif choice == "2":
            engine.transition(task, TaskState.REJECTED, "CONTRACTOR")

            # 🔁 FULL LOOP RESET (KEY FIX)
            print("\n↩ Rejected → restarting full federation selection...\n")

            engine.transition(task, TaskState.VALIDATED, "SYSTEM")
            continue

        else:
            engine.transition(task, TaskState.VALIDATED, "CONTRACTOR")
            continue

    print("\nFINAL STATE:", task.state.value)

    print("\nLEDGER:")
    for h in task.history:
        print(" ", h)