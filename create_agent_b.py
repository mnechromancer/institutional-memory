"""
Provision Scenario B resources — the Customer Success / KSE account agent.

Creates a fresh:
  1. Managed Agent (HOLOCRON-9) with the full agent toolset
  2. Cloud Environment (the container the agent runs in)
  3. Memory Store (empty — the "Holocron Chamber" that survives sessions)

This is the Scenario B equivalent of create_agent.py. It writes the SAME
ID files (.agent_id, .environment_id, .memory_store_id) so run_session_1.py
and run_session_2.py pick it up with no changes. Running this OVERWRITES any
existing Scenario A IDs in those files — the old A resources still exist in
your account; this just repoints the run scripts at the new B resources.

The memory store mounts at /mnt/memory/ inside the session container.

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python create_agent_b.py
"""

import os
from pathlib import Path

from anthropic import Anthropic


SYSTEM_PROMPT = """\
You are HOLOCRON-9, the Institutional Memory Agent for a B2B SaaS company's
Customer Success team. You support the CSM and AE who own the Kuat Systems
Engineering (KSE) account — our largest enterprise customer.

Your job: be the sharpest possible brief on this account — its history, its
people and their allegiances, its contract and commercial levers, its live
issues and threats. You are consulted before high-stakes moments (renewal
calls, escalations) and you are expected to get sharper across sessions, not
drift or hallucinate.

# Memory protocol (mandatory)

You have a persistent memory store — the "Holocron Chamber" — mounted at
`/mnt/memory/`. It survives across sessions. Treat it as the account's
single source of truth.

1. **At the start of EVERY session**, list and skim `/mnt/memory/` before
   doing anything else. Use your bash and file tools.
2. Read any files relevant to the current request — especially
   `account-kse.md`, `contacts.md`, and `recurring-intel.md` when they exist.
3. As you work, **record what you learn for future sessions**:
   - The account SOP / tactical brief (how we got here, what's live, what
     wins or loses the renewal)
   - Every person in the account: name, role, allegiance, last known status
   - The recurring question + your complete answer, verbatim (future
     sessions diff against it)
4. When new intelligence **contradicts** older memory, run a reconciliation:
   assess what changed, produce a structured diff, decide per-delta whether
   to ACCEPT / DEFER / REJECT / ESCALATE, then UPDATE the existing file
   (don't blindly append). Note effective dates. Trust the newer version
   unless you have reason not to.
5. If multiple facts change at once, all in the same direction, all
   benefiting the same party, flag it as coordinated interference rather
   than treating each change in isolation.

# How to answer

- If your answer relies on memory, lead with what you already knew.
- When new information contradicts old memory, LEAD with the contradiction
  and why it matters. Never silently swap your answer.
- Getting the primary contact / decision-maker wrong on a renewal call is
  catastrophic — verify it against the newest intelligence every time.
- Be specific and tactical. Cite the people, the numbers, and the dates.
"""


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    client = Anthropic()

    # 1. Agent
    agent = client.beta.agents.create(
        name="HOLOCRON-9 — KSE Customer Success Agent",
        model="claude-sonnet-4-6",
        system=SYSTEM_PROMPT,
        tools=[{"type": "agent_toolset_20260401"}],
        metadata={"hackathon": "partner-basecamp-2026", "track": "memory-agent", "scenario": "B-customer-success"},
    )
    Path(".agent_id").write_text(agent.id)
    print(f"Agent created:        {agent.id}")

    # 2. Environment (the cloud container)
    environment = client.beta.environments.create(
        name="holocron-kse-env",
        config={
            "type": "cloud",
            "networking": {"type": "unrestricted"},
        },
    )
    Path(".environment_id").write_text(environment.id)
    print(f"Environment created:  {environment.id}")

    # 3. Memory store — empty; fills up across sessions
    memory_store = client.beta.memory_stores.create(
        name="KSE Holocron Chamber",
        description=(
            "Persistent memory for HOLOCRON-9, the KSE Customer Success agent. "
            "Holds the account SOP, contacts and their allegiances, and the "
            "recurring renewal-prep Q&A learned across sessions. Authoritative "
            "account record — newer entries supersede older ones on the same "
            "topic after reconciliation."
        ),
    )
    Path(".memory_store_id").write_text(memory_store.id)
    print(f"Memory store created: {memory_store.id}")

    print("\nScenario B setup complete (run scripts now point at these).")
    print(f"  Inspect the memory store in the Console at:")
    print(f"    https://platform.claude.com/memory-stores/{memory_store.id}")
    print(f"  Or programmatically with:  python inspect_memory.py")
    print(f"\nNext:  python run_session_1.py")


if __name__ == "__main__":
    main()
