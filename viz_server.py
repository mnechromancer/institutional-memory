"""
Live visualization backend for HOLOCRON-9.

A tiny stdlib HTTP server that:
  - holds the API key (sourced from the environment) — the browser never sees it
  - bypasses the local intercepting proxy that breaks Python's TLS
  - drives a real Managed Agents session (round1 or round2 intel)
  - streams the agent's events to the browser over SSE as they happen
  - snapshots the memory store when the agent goes idle
  - saves every run to outputs/viz_run_<session>.json for offline replay

Run:
    export ANTHROPIC_API_KEY=...      (or have it in .env; serve.sh handles that)
    python viz_server.py              # serves http://localhost:8765

Then open http://localhost:8765 in a browser.

Endpoints:
    GET  /                      -> viz.html
    GET  /run?session=1|2       -> SSE stream of frames for a LIVE run
    GET  /replay?session=1|2    -> SSE replay of the last saved run (no API calls)
"""

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from anthropic import Anthropic

PORT = 8765
ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "outputs"

QUESTION = (
    "KSE's VP of Technology Lyra Antilles just sent a message asking us to "
    "prepare a renewal proposal. What do we know going into that call? "
    "Full picture — their history, live threats, key contacts, commercial "
    "situation, and what blows this up if we get it wrong."
)

SESSIONS = {
    "1": {
        "docs": ROOT / "synthetic-data/round1",
        "title": "Session 1 — KSE baseline",
        "preamble": (
            "HOLOCRON-9, you're live. Check /mnt/memory/ first and tell me what "
            "you already know. Then read the intel below and answer. Before you "
            "finish, write account-kse.md, contacts.md, and recurring-intel.md "
            "to /mnt/memory/.\n\n"
        ),
    },
    "2": {
        "docs": ROOT / "synthetic-data/round2",
        "title": "Session 2 — KSE reconciliation",
        "preamble": (
            "HOLOCRON-9, back online. New intel came in overnight and some of it "
            "contradicts what you saved yesterday. Read /mnt/memory/ (especially "
            "recurring-intel.md), read the new intel below, reconcile conflicts by "
            "UPDATING the existing memory files (don't just append), then answer. "
            "Lead with what changed and why it matters.\n\n"
        ),
    },
}


def load_intel(docs_dir: Path) -> str:
    blocks = []
    for path in sorted(docs_dir.glob("*.md")):
        blocks.append(f"=====  DOCUMENT: {path.name}  =====\n{path.read_text()}")
    return "\n\n".join(blocks)


def memory_snapshot(client: Anthropic, store_id: str) -> list[dict]:
    """Return [{path, content}] for every memory file in the store."""
    out = []
    try:
        page = client.beta.memory_stores.memories.list(
            store_id, path_prefix="/", order_by="path"
        )
        for item in page.data:
            if getattr(item, "type", None) != "memory":
                continue
            full = client.beta.memory_stores.memories.retrieve(
                item.id, memory_store_id=store_id
            )
            out.append({"path": item.path, "content": full.content or ""})
    except Exception as e:  # snapshot is best-effort; never kill the stream
        out.append({"path": "(snapshot error)", "content": str(e)})
    return out


def sse(frame: dict) -> bytes:
    return f"data: {json.dumps(frame)}\n\n".encode()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # quiet

    def _send_html(self):
        body = (ROOT / "viz.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _open_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

    def _emit(self, frame, record):
        record.append(frame)
        lock = getattr(self, "_wlock", None)
        try:
            if lock:
                with lock:
                    self.wfile.write(sse(frame)); self.wfile.flush()
            else:
                self.wfile.write(sse(frame)); self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            raise

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html", "/viz.html"):
            return self._send_html()
        qs = parse_qs(parsed.query)
        sess = (qs.get("session") or ["1"])[0]
        if parsed.path == "/run":
            return self._run_live(sess)
        if parsed.path == "/replay":
            return self._replay(sess)
        self.send_response(404)
        self.end_headers()

    # ---- live run ----------------------------------------------------------
    def _run_live(self, sess):
        cfg = SESSIONS.get(sess)
        if cfg is None:
            self.send_response(400); self.end_headers(); return
        self._open_sse()
        record = []
        try:
            agent_id = (ROOT / ".agent_id").read_text().strip()
            environment_id = (ROOT / ".environment_id").read_text().strip()
            store_id = (ROOT / ".memory_store_id").read_text().strip()
            client = Anthropic()

            self._emit({"type": "status", "text": f"Starting {cfg['title']}…"}, record)
            intel = load_intel(cfg["docs"])
            session = client.beta.sessions.create(
                agent=agent_id,
                environment_id=environment_id,
                title=cfg["title"],
                resources=[{
                    "type": "memory_store",
                    "memory_store_id": store_id,
                    "access": "read_write",
                    "instructions": "Your persistent Holocron Chamber at /mnt/memory/.",
                }],
            )
            self._emit({"type": "status", "text": f"Session {session.id} online"}, record)

            user_message = cfg["preamble"] + intel + (
                f"\n\n========================\nQUESTION: {QUESTION}"
            )
            # Show the operator what HOLOCRON-9 was actually asked. The intel docs
            # are huge, so send the instruction + question, noting the intel inline.
            prompt_view = (
                cfg["preamble"].strip()
                + f"\n\n[+ {len(intel):,} chars of KSE intel docs attached]\n\n"
                + f"QUESTION: {QUESTION}"
            )
            self._emit({"type": "prompt", "text": prompt_view,
                        "title": cfg["title"]}, record)

            # Heartbeat: the agent can go quiet for many seconds before its first
            # event. Ping the browser ~every 2s so the connection stays warm and
            # the UI can show "still working". Guarded by a lock so it never
            # interleaves with a real frame mid-write.
            self._wlock = threading.Lock()
            stop_hb = threading.Event()

            def heartbeat():
                while not stop_hb.wait(2.0):
                    try:
                        with self._wlock:
                            self.wfile.write(sse({"type": "heartbeat"}))
                            self.wfile.flush()
                    except Exception:
                        return

            hb = threading.Thread(target=heartbeat, daemon=True)
            hb.start()

            with client.beta.sessions.events.stream(session.id) as stream:
                client.beta.sessions.events.send(
                    session.id,
                    events=[{"type": "user.message",
                             "content": [{"type": "text", "text": user_message}]}],
                )
                for event in stream:
                    if event.type == "agent.thinking":
                        # earliest signal — stream the agent's reasoning live
                        txt = ""
                        for block in getattr(event, "content", []) or []:
                            if getattr(block, "type", None) == "thinking":
                                txt += getattr(block, "thinking", "") or ""
                        if txt:
                            self._emit({"type": "think", "text": txt}, record)
                    elif event.type == "agent.message":
                        for block in event.content:
                            if getattr(block, "type", None) == "text":
                                self._emit({"type": "answer", "text": block.text}, record)
                    elif event.type == "agent.tool_use":
                        name = getattr(event, "name", "?")
                        inp = getattr(event, "input", {}) or {}
                        target = inp.get("path") or inp.get("file_path") or inp.get("command") or ""
                        # the body the agent is writing — file content or bash cmd
                        body = inp.get("file_text") or inp.get("content") or inp.get("command") or ""
                        self._emit({"type": "tool", "name": name,
                                    "target": str(target),
                                    "body": str(body)[:1200],
                                    "memory": "/mnt/memory" in str(target)}, record)
                    elif event.type == "session.status_idle":
                        stop_hb.set()
                        self._emit({"type": "status", "text": "reading back the Holocron…"}, record)
                        snap = memory_snapshot(client, store_id)
                        self._emit({"type": "memory", "files": snap}, record)
                        self._emit({"type": "done"}, record)
                        break
            stop_hb.set()
        except Exception as e:
            try: stop_hb.set()
            except Exception: pass
            self._emit({"type": "error", "text": f"{type(e).__name__}: {e}"}, record)
        finally:
            # Only overwrite the replay file if this run actually COMPLETED.
            # An interrupted/errored run (BrokenPipe from a closed tab) must not
            # poison a previously-good capture used for the offline fallback.
            record = [f for f in record if f.get("type") != "heartbeat"]
            completed = any(f.get("type") == "done" for f in record)
            if completed:
                OUTPUT_DIR.mkdir(exist_ok=True)
                (OUTPUT_DIR / f"viz_run_{sess}.json").write_text(json.dumps(record))

    # ---- replay last saved run --------------------------------------------
    def _replay(self, sess):
        path = OUTPUT_DIR / f"viz_run_{sess}.json"
        self._open_sse()
        if not path.exists():
            self.wfile.write(sse({"type": "error", "text": "No saved run to replay."}))
            return
        frames = json.loads(path.read_text())
        for frame in frames:
            try:
                self.wfile.write(sse(frame)); self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return
            # answer text streams fast, structural frames pause for effect
            time.sleep(0.02 if frame.get("type") == "answer" else 0.4)


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running (see serve.sh).")
    # neutralize the local intercepting proxy that breaks Python TLS
    for var in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "https_proxy", "http_proxy"):
        os.environ.pop(var, None)
    os.environ["NO_PROXY"] = "*"
    print(f"HOLOCRON-9 viz server → http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
