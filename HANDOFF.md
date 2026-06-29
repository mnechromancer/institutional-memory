# HANDOFF — HOLOCRON-9 visual / harness polish

You're picking up the **institutional-memory** demo app (HOLOCRON-9). It works
end-to-end and is live. Your job is to make the live harness **more visual and
stylized** — starting with a **"current session cost" counter** and other
run-time readouts — before this pattern gets cloned into two sibling demos.

Read this whole file first, then `README.md` (the original scenario) and skim
`viz_server.py` + `viz.html`.

---

## What this is (30-second version)

A Star Wars reskin of the "institutional memory" hackathon scenario: a **Claude
Managed Agent** with the **Memory tool** that gets sharper across sessions.
HOLOCRON-9 preps a renewal for *Kuat Systems Engineering* (KSE).

- **Session 1** reads the round-1 intel, answers, and writes 3 memory files to
  `/mnt/memory/` (`account-kse.md`, `contacts.md`, `recurring-intel.md`).
- **Session 2** reads memory back, **reconciles contradicting round-2 intel by
  updating those files**, and answers sharper. That reconcile moment is the demo.

The browser harness (`viz.html`) shows the agent working live: activity stream,
the streaming brief, and the memory chamber updating.

## Current status (all working — don't re-litigate)

- Live API runs verified against `anthropic==0.112`. Cloud resources are already
  provisioned (`.agent_id`, `.environment_id`, `.memory_store_id` exist on disk,
  gitignored). The model is **`claude-sonnet-4-6`** (see `create_agent.py`).
- Two clean replays captured + committed under `replays/viz_run_{1,2}.json`.
- **Published to GitHub Pages:** https://mnechromancer.github.io/institutional-memory/
- **Embedded in the portfolio** at `jamisonducey.com/demos/institutional-memory`
  via an `<iframe>` of the Pages `viz.html`. ⇒ **Any change you push to `main`
  here auto-rebuilds Pages and shows up in the portfolio with no portfolio
  redeploy.** (The portfolio just frames this page.)
- Recent fixes already in `main`: Windows cp1252 crashes (UTF-8 everywhere),
  the "frozen viz" hang (now renders the full event set), multi-message brief
  accumulation, and **static client-side replay** so replay needs no server.

## Your task

### 1. "Current session cost" counter (priority)
Add a running cost readout to the harness.
- First, **find out if token usage is in the stream**. Extend/!run `diag_events.py`
  and inspect `span.model_request_end` (and `agent.message`, `session.*_idle`)
  for a `usage` / `input_tokens` / `output_tokens` field. Dump full event reprs.
- If usage is exposed: accumulate input/output (and cache) tokens across the
  session and compute cost with **current `claude-sonnet-4-6` pricing** — get
  real numbers from the `claude-api` skill / Anthropic pricing docs, do **not**
  hardcode from memory.
- If usage is *not* in the stream: note it and fall back to a clearly-labeled
  estimate (e.g. from text length) rather than faking precision.
- Surface it as a new SSE frame (e.g. `{type:"usage", input, output, cost_usd}`)
  emitted from `viz_server.py`, accumulated + rendered in `viz.html` as a HUD /
  footer readout (cost, tokens, per-request latency). Keep the Star Wars voice
  ("CREDITS EXPENDED", etc. — KSE deals in "credits").

### 2. More harness visuals / stylization
The viz is functional but plain. Make it feel like a Holocron console:
- A persistent **stats HUD** (elapsed, tool calls, tokens, cost, model).
- Per-`span.model_request` timing so each reasoning round shows its latency.
- Lean into the aesthetic: the existing palette is good — consider CRT/scanline
  texture, Aurebesh accents, a sharper "Holocron Chamber" treatment for the
  memory panel, nicer status/pulse, the contradiction `flag` made dramatic.
- (Stretch, shared with future demos) a **Star Wars idle animation** that plays
  during dead air between/within runs so the screen is never static.

### 3. Cleanup
- Tidy `README.md` to match the shipped HOLOCRON-9 / KSE scenario + add the
  Windows "use the venv, key in `.env`" run notes.
- Remove any dead code; keep `diag_events.py` (it's the event-inspection tool).

### 4. Stretch goals (from `stretch-goals.md` — the owner wants these done too)
Read `stretch-goals.md` for the full S1–S9 list and rationale. Implement them,
but **lead with the ones that are also visual/demo wins** (they reinforce task 1–2):

- **S8 — "memory diff" view (do this first):** diff the memory store between
  session 1 and session 2 and render what changed. This is *the* headline visual
  and pairs perfectly with the harness work — surface it as its own panel/frame.
- **S3 — adversarial round:** add `synthetic-data/round3/` with implausible
  contradictions; the agent should **flag and ask**, not silently overwrite. Wire
  the contradiction into the dramatic `flag` visual. If it silently updates,
  that's a system-prompt bug to fix (tightens S1).
- **S4 — "what have you learned?" session:** a no-new-docs session that just asks
  the agent to summarize everything in memory. Very demo-able; add a 3rd run
  button.
- **S1 — explicit memory policy** in `create_agent.py`'s system prompt
  (ALWAYS-remember / NEVER-remember lists), then re-create the agent + re-run.
- **S2 — Memory Curator sub-agent** (`stretch_memory_curator.py` already exists) —
  run it, show memory getting cleaner; good multi-agent talking point.
- Deeper / optional (infra-heavy, lower visual payoff): **S5** per-tenant memory
  via `customer_id` metadata, **S6** Routines for passive accumulation, **S7**
  long-context compaction, **S9** per-topic sub-agents.

**Important:** S1/S2/S3 change agent behavior or the memory store, so **re-create
the agent if you edit its system prompt** and **re-capture `replays/`** afterward
(see below) — the committed replays and the public Pages/portfolio embed must
reflect the new behavior + visuals.

## Architecture & key files

| File | Role |
|---|---|
| `viz.html` | The harness UI. `handleFrame(f)` renders one frame (shared by live + replay); `replayStatic()` plays committed JSON; `run()` picks live vs replay. |
| `viz_server.py` | Local SSE backend. `/run?session=N` drives a **live** Managed-Agents session and streams frames + saves `outputs/viz_run_N.json`. `/replay` is the old server replay (Pages uses static instead). |
| `create_agent.py` | Provisions agent + environment + memory store (already run). |
| `run_session_{1,2}.py` | CLI versions of the two sessions (no viz). |
| `diag_events.py` | Dumps the raw event stream — use it to discover field shapes (e.g. usage). |
| `replays/viz_run_{1,2}.json` | Committed captures served on Pages for static replay. |
| `index.html` | Redirects Pages root → `viz.html`. |

### SSE frame contract (emitted by `viz_server.py`, rendered by `viz.html`)
```
{type:"status", text}            {type:"prompt", text, title}
{type:"think", text}             {type:"answer", text}        // accumulates
{type:"tool", name, target, body, memory}
{type:"tool_result", text}       {type:"memory", files:[{path,content}]}
{type:"heartbeat"}  {type:"done"}  {type:"error", text}
```
Real agent event types seen on the wire: `session.status_running`,
`session.thread_status_running`, `span.model_request_start`/`_end`,
`agent.thinking`, `agent.message`, `agent.tool_use`, `agent.tool_result`,
`session.thread_status_idle`, `session.status_idle`.
**Any new frame type (e.g. `usage`) must be handled in BOTH `viz_server.py`
(emit) and `viz.html` `handleFrame()` (render) so live and replay stay identical.**

## How to run & iterate

```bash
# from the repo root (Windows / Git Bash)
set -a; . ./.env; set +a            # ANTHROPIC_API_KEY (gitignored)
.venv/Scripts/python.exe viz_server.py        # -> http://localhost:8765
# drive a live run without a browser (also re-captures outputs/viz_run_N.json):
curl -N -s "http://127.0.0.1:8765/run?session=1"
```
Open `http://localhost:8765/` in a browser; **uncheck "replay"** for a live run.
`diag_events.py` runs a tiny cheap session and prints raw events.

### Re-capturing replays after you change the frame schema
The committed replays must match the current viz, or Pages replay breaks:
1. Run live session 1 and 2 (via the server `/run`, or the browser).
2. Copy `outputs/viz_run_1.json` and `viz_run_2.json` → `replays/`.
3. Commit + push `main` → Pages rebuilds → portfolio reflects it.

## Invariants / gotchas

- **Live runs cost real credits** and use the provisioned cloud agent. Keep test
  prompts small (`diag_events.py` style) while iterating; only do full KSE runs
  to capture final replays.
- **Windows encoding:** always pass `encoding="utf-8"` on file I/O; stdout is
  forced to UTF-8 in `main()`. Don't reintroduce bare `read_text()`/prints with
  unicode.
- **Live/replay parity:** all rendering goes through `handleFrame()`. Don't fork
  rendering logic. Replay must stay **server-free** (it's what runs on Pages).
- **Secrets:** `.env`, `.agent_id`, `.environment_id`, `.memory_store_id`,
  `outputs/`, `.venv/` are gitignored — keep them out of commits.
- If the viz gets taller, tell the portfolio side to bump `embedHeight` in
  `portfolio/src/content/demos/institutional-memory.json` (currently 980).

## Bigger picture (context, not your task yet)

This app is the **reference template** for two more demos to be built later:
**Imperial Probe-Droid Sentinel** (always-on agent) and **Jedi Council**
(specialist-swarm). Those will reuse this harness pattern and run **live via a
portfolio Vercel proxy with the visitor's own key (BYOK)** — but
institutional-memory stays **replay-only in public** (Managed Agents needs the
owner's workspace + provisioned agent). So: make this one shine as the pattern;
the visuals you add here will be extracted into a shared kit for the others.

## Definition of done
- A working, real (or honestly-estimated) **session cost + token + latency HUD**
  in the live harness, also visible in replay.
- Noticeably more stylized console that holds up in the portfolio iframe.
- Stretch goals implemented — at minimum the visual-leaning ones (**S8 memory
  diff**, **S3 adversarial flag**, **S4 reflection session**, **S1 memory
  policy**, **S2 curator**); deeper ones (S5–S7, S9) as time allows.
- Fresh `replays/` captures committed (re-captured after any behavior change) so
  Pages/portfolio show the new visuals + behavior.
- README updated; `npm`-free Python run path documented.
