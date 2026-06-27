"""
Session 1 — Baseline.

Starts a Managed Agents session with the memory store ATTACHED so the agent
can read and write /mnt/memory/. Inlines the round1 docs in the user message.

After this session, inspect the memory store to see what the agent saved:
    python inspect_memory.py
or in the Console UI under Memory Stores.

Usage:
    python run_session_1.py
"""

import os
from pathlib import Path

from anthropic import Anthropic


TEST_QUESTION = (
    "KSE's VP of Technology Lyra Antilles just sent a message asking us to "
    "prepare a renewal proposal. What do we know going into that call? "
    "Full picture — their history, live threats, key contacts, commercial "
    "situation, and what blows this up if we get it wrong."
)

MISSION_BRIEF = """
╔══════════════════════════════════════════════════════════════╗
║  MISSION BRIEF — SESSION 1                                   ║
║  Location:  Anthropic Basecamp, San Francisco                ║
║  Stardate:  June 23, 2026 — 14:00 local                     ║
║  Agent:     HOLOCRON-9 (first activation this session)       ║
╚══════════════════════════════════════════════════════════════╝

Situation on the ground:

  It's 2pm in SF. You're at Anthropic's partner training — "Basecamp."
  You just met Jamison this morning in the agentic AI session.
  He's sharp. Works in AI consulting at a firm you've heard of.
  You're going to use him to stress-test this demo.

  The room has people from everywhere:
  - Deloitte brought a 14-person delegation. They have matching shirts.
  - A McKinsey partner is in the corner drawing a 2x2 matrix to explain
    why memory agents are a "disruptive innovation in the retrieval quadrant."
  - Cognizant submitted their World Cup bracket to a shared spreadsheet
    that has 47 tabs and no documentation.
  - A PwC consultant just asked if HOLOCRON-9 can do SOX testing.
    (The answer is: sort of. Ask Alex later.)

  The World Cup is happening RIGHT NOW on someone's laptop in the corner.
  Portugal just destroyed Uzbekistan 5-0. Ronaldo scored twice.
  He is 41 years old. He is now the first human to score at SIX World Cups.
  The McKinsey partner just said this was "a blue ocean moment for aging
  athletes." Nobody laughed. Someone should have laughed.

  Messi broke the all-time World Cup scoring record yesterday — 18 goals,
  the most in history. Jamison's take: "He's basically Yoda at this point.
  900 years old, still the most dangerous thing in the room."
  Your take: fair.

  ANYWAY. You have a renewal call with Kuat Systems Engineering tomorrow.
  KSE is your largest account. $480,000 credits ARR.
  You need to prep tonight.
  HOLOCRON-9 goes online now.
"""

DOCS_DIR = Path("synthetic-data/round1")
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

    print(f"Loading round1 docs from {DOCS_DIR}/...")
    intel = load_docs_as_context(DOCS_DIR)

    print(f"\nStarting session with memory store {memory_store_id} attached...")
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title="Session 1 — KSE baseline",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "This is your persistent institutional memory. Mounted at "
                    "/mnt/memory/. Check it before starting. Record what you "
                    "learn for future sessions."
                ),
            }
        ],
    )

    user_message = f"""{MISSION_BRIEF}

HOLOCRON-9, you're live. Alex speaking.

Jamison is sitting next to me watching this happen in real time.
He just bet me a coffee that the agent would hallucinate something about
the client. Don't make me lose that bet.

We have a renewal call with Kuat Systems Engineering tomorrow morning.
I've uploaded our current account intel below. Here's what I need:

1. Check /mnt/memory/ first. Tell me if you already know anything.
2. Read all the intel docs below carefully.
3. Answer my question (end of this message).
4. Before you shut down, write to /mnt/memory/:

   account-kse.md     → The account SOP. Not a summary — a tactical brief.
                         How we got here, what's live, what wins us this renewal,
                         what kills it. Written like Rebel Alliance field orders.
   contacts.md        → Every person in this account: name, role, allegiance level,
                         last known status, and one thing to never say to them.
   recurring-intel.md → This exact question + your complete answer, verbatim.
                         Future sessions diff against this. Do not paraphrase.

One more thing: Ronaldo just scored at his sixth World Cup at age 41.
The man has been doing this since 2006. That's the same number of years
our longest enterprise customer has been with us.
If you can find a natural place to work that in, Jamison owes me a coffee.
Don't force it. Like Yoda says — "Force it, you should not."

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
                # Show file ops on /mnt/memory/ in particular — that's the demo
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
    out = OUTPUT_DIR / "session1.txt"
    out.write_text(
        f"=== SESSION 1 ===\nQuestion: {TEST_QUESTION}\n\n--- ANSWER ---\n{final_text}\n",
        encoding="utf-8",
    )
    print(f"\nSaved to {out}")
    print(f"\nInspect what the agent remembered:  python inspect_memory.py")
    print(f"Then run run_session_2.py.")


if __name__ == "__main__":
    main()
