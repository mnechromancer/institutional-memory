"""
Session 2 — After memory + new context.

Same agent, same memory store, fresh session. Round2 docs contradict round1.
The agent should:
- Read memory first (`/mnt/memory/`)
- Notice the contradictions in the new docs
- UPDATE memory rather than appending
- Lead its answer with what changed and why

Usage:
    python run_session_2.py
"""

import os
from pathlib import Path

from anthropic import Anthropic


# Match session 1
TEST_QUESTION = (
    "KSE's VP of Technology Lyra Antilles just sent a message asking us to "
    "prepare a renewal proposal. What do we know going into that call? "
    "Full picture — their history, live threats, key contacts, commercial "
    "situation, and what blows this up if we get it wrong."
)

MORNING_BRIEF = """
╔══════════════════════════════════════════════════════════════╗
║  MISSION BRIEF — SESSION 2                                   ║
║  Location:  Anthropic Basecamp, San Francisco — DAY 2        ║
║  Stardate:  June 24, 2026 — 08:30 local                     ║
║  Status:    DISTURBANCE IN THE FORCE DETECTED                ║
╚══════════════════════════════════════════════════════════════╝

What happened while you were sleeping:

  England beat Ghana 2-1. Harry Kane scored a penalty in the 89th minute
  and is now two goals shy of England's all-time World Cup record.
  Jamison watched all of it. He's on his third coffee and very loud
  about this in the breakfast area.

  Half the room is debating the USMNT playing Türkiye tonight.
  The US already clinched the Round of 32 — first time they've done
  that before the final group game. Room is split 50/50 on whether
  Tyler Adams can contain the midfield. The Deloitte delegation has
  built a tactical breakdown in PowerPoint. 47 slides. For one game.

  A McKinsey partner lost a bet and had to wear a Japan shirt to
  breakfast. He is telling everyone it's "ironic." It's not ironic.
  He lost. He's wearing the shirt. We respect this.

  BUT MORE IMPORTANTLY:

  Three intelligence updates about KSE landed overnight.
  They contradict what HOLOCRON-9 saved in session 1.

  One of them looks like a double agent situation.

  This is exactly what happened with Count Dooku.
  He was on the Jedi Council. He was respected. He was trusted.
  Then one day the intelligence picture changed and nobody had
  run the reconciliation protocol.

  We run the protocol now.
  The renewal call is in 3 hours.
"""

DOCS_DIR = Path("synthetic-data/round2")
OUTPUT_DIR = Path("outputs")


def load_docs_as_context(docs_dir: Path) -> str:
    blocks = []
    for path in sorted(docs_dir.glob("*.md")):
        print(f"  including {path.name}")
        blocks.append(f"=====  DOCUMENT: {path.name}  =====\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(blocks)


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    for required in (".agent_id", ".environment_id", ".memory_store_id"):
        if not Path(required).exists():
            raise SystemExit(f"Missing {required}. Run create_agent.py first.")

    agent_id = Path(".agent_id").read_text().strip()
    environment_id = Path(".environment_id").read_text().strip()
    memory_store_id = Path(".memory_store_id").read_text().strip()

    client = Anthropic()

    print(f"Loading round2 docs from {DOCS_DIR}/...")
    intel = load_docs_as_context(DOCS_DIR)

    print(f"\nStarting fresh session with same memory store {memory_store_id}...")
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title="Session 2 — KSE reconciliation",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "This is your persistent institutional memory. Some entries "
                    "may be out of date — reconcile against the new documents in "
                    "this session and UPDATE existing entries (don't just append)."
                ),
            }
        ],
    )

    user_message = f"""{MORNING_BRIEF}

HOLOCRON-9, back online. Alex again. Jamison is here too.

Three intelligence updates came in overnight about KSE.
I'm loading them below. Some of this contradicts what you saved yesterday.

Here is what I need you to do — and Jamison is watching the whole thing,
so show your work:

1. Read the Holocron Chamber (/mnt/memory/). Check account-kse.md,
   contacts.md, and especially recurring-intel.md — that's your session 1
   answer. That's what you're diffing against.

2. Read the new intelligence docs below.

3. Run the full reconciliation protocol:
   ⚡ DISTURBANCE ASSESSMENT — does today's answer differ from session 1?
   ⚔  HOLOCRON DIFF — produce the structured diff block (policy-level)
   ⚖  JEDI COUNCIL — ACCEPT / DEFER / REJECT / ESCALATE each delta
   💎  COMMIT — update the Holocron with accepted changes + changelog

4. If any contradictions look like coordinated interference — multiple
   things changing simultaneously, all in the same direction, all benefiting
   the same person — flag THREAT: IMPERIAL INTERFERENCE SUSPECTED.
   That's not paranoia. That's pattern recognition. It's what Mace Windu
   would do. And Mace Windu was right about Palpatine.

5. Answer the question below. Lead with what changed and why it matters.

Side note: if the answer to "who is our primary contact at KSE" has changed
overnight, that is the EXACT thing that would be catastrophic to get wrong
on a renewal call. Like sending a lightsaber to a pacifist.
Don't be the person who does that.

{intel}

══════════════════════════════════════════════════
MISSION QUESTION: {TEST_QUESTION}
══════════════════════════════════════════════════"""

    final_text_parts: list[str] = []
    print("\nAgent working...\n")
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [{"type": "text", "text": user_message}],
                }
            ],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        final_text_parts.append(block.text)
                        print(block.text, end="", flush=True)
            elif event.type == "agent.tool_use":
                name = getattr(event, "name", "?")
                inp = getattr(event, "input", {}) or {}
                target = inp.get("path") or inp.get("file_path") or inp.get("command") or ""
                if "/mnt/memory" in str(target):
                    print(f"\n  [memory: {name}  {target}]", flush=True)
                else:
                    print(f"\n  [{name}]", flush=True)
            elif event.type == "session.status_idle":
                print("\n\n[agent finished]")
                break

    final_text = "".join(final_text_parts)
    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / "session2.txt"
    out.write_text(
        f"=== SESSION 2 ===\nQuestion: {TEST_QUESTION}\n\n--- ANSWER ---\n{final_text}\n",
        encoding="utf-8",
    )
    print(f"\nSaved to {out}")
    print(f"\nDiff outputs/session1.txt and outputs/session2.txt — the demo lives there.")
    print(f"Inspect updated memory:  python inspect_memory.py")


if __name__ == "__main__":
    main()
