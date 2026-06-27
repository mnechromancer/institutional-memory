"""
Diagnostic — dump the RAW event stream from a Managed Agents session.

Why: the viz hangs with no visible updates. Prime suspect is that the
hard-coded event-type strings in viz_server.py / run_session_*.py
("agent.thinking", "agent.tool_use", "agent.message", "session.status_idle")
no longer match what the API actually emits — so the UI gets no frames during
work. This script prints every event's .type and a trimmed repr so we can see
the real names, using a tiny prompt to keep cost near zero.

Run (after create_agent.py has provisioned the IDs):
    .venv/Scripts/python.exe diag_events.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

if not os.environ.get("ANTHROPIC_API_KEY"):
    raise SystemExit("No ANTHROPIC_API_KEY (put it in .env).")

for f in (".agent_id", ".environment_id", ".memory_store_id"):
    if not Path(f).exists():
        raise SystemExit(f"Missing {f} — run create_agent.py first.")

agent_id = Path(".agent_id").read_text().strip()
environment_id = Path(".environment_id").read_text().strip()
store_id = Path(".memory_store_id").read_text().strip()

# strip the intercepting proxy that breaks Python TLS (same as viz_server)
for var in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "https_proxy", "http_proxy"):
    os.environ.pop(var, None)
os.environ["NO_PROXY"] = "*"

client = Anthropic()

session = client.beta.sessions.create(
    agent=agent_id,
    environment_id=environment_id,
    title="diag — event dump",
    resources=[{
        "type": "memory_store",
        "memory_store_id": store_id,
        "access": "read_write",
        "instructions": "Your persistent memory at /mnt/memory/.",
    }],
)
print(f"session: {session.id}\n--- events ---")

msg = ("List the files in /mnt/memory/, then write a one-line file "
       "/mnt/memory/diag.md saying 'diagnostic ok', then reply 'done'.")

n = 0
with client.beta.sessions.events.stream(session.id) as stream:
    client.beta.sessions.events.send(
        session.id,
        events=[{"type": "user.message", "content": [{"type": "text", "text": msg}]}],
    )
    for event in stream:
        n += 1
        etype = getattr(event, "type", "?")
        # trimmed repr of the event so we can see its shape without a wall of text
        body = repr(getattr(event, "content", "")) or ""
        extra = ""
        if hasattr(event, "name"):
            extra = f"  name={getattr(event,'name',None)} input={str(getattr(event,'input',None))[:120]}"
        print(f"[{n:02d}] type={etype!r}{extra}  content={body[:160]}")
        if etype in ("session.status_idle", "session.idle", "session.completed", "done"):
            print("--- idle/terminal reached ---")
            break

print(f"\ntotal events: {n}")
print("attrs on last event:", [a for a in dir(event) if not a.startswith('_')][:40])
