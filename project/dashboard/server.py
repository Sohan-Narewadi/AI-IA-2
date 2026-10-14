"""Demo dashboard server for the Research Assistant Agent (stdlib only).

Run:  python dashboard/server.py        then open http://localhost:8000
Live mode needs OPENROUTER_API_KEY; Replay mode plays the saved logs/ runs offline.
"""
import json, os, sys, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import agent
from classical_agent import classical_agent
from run_demo import GOALS
from tools import TOOLS

PORT = int(os.environ.get("DASH_PORT", "8000"))
LIVE_LOG = "dashboard_live"
REPLAY_FILES = {1: "demo_goal1", 2: "demo_goal2", 3: "demo_goal3", 4: "demo_goal4_memory"}
SESSION_MEM = []          # short-term memory shared by every live goal in this session
RUN_LOCK = threading.Lock()
_llm = None


def read_log(name):
    path = os.path.join(agent.LOG_DIR, name + ".jsonl")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def get_llm():
    global _llm
    if _llm is None:
        _llm = agent.openrouter_llm()
    return _llm


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, ctype):
        if not os.path.isfile(path):
            return self.send_json({"error": "not found"}, 404)
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path in ("/", "/index.html"):
            return self.send_file(os.path.join(HERE, "index.html"), "text/html; charset=utf-8")
        if u.path == "/architecture.png":
            return self.send_file(os.path.join(ROOT, "figures", "architecture.png"), "image/png")
        if u.path == "/api/status":
            return self.send_json({"has_key": bool(os.environ.get("OPENROUTER_API_KEY")),
                                   "models": agent.MODELS, "max_steps": agent.MAX_STEPS,
                                   "memory_messages": len(SESSION_MEM)})
        if u.path == "/api/goals":
            return self.send_json(GOALS)
        if u.path == "/api/tools":
            return self.send_json([{"name": n, "desc": d} for n, (_, d) in TOOLS.items()])
        if u.path == "/api/replay":
            return self.send_json(read_log(REPLAY_FILES.get(int(q.get("n", 1)), "")))
        if u.path == "/api/classical":
            return self.send_json({"answer": classical_agent(q.get("goal", ""))})
        if u.path == "/api/reset":
            SESSION_MEM.clear()
            return self.send_json({"memory_messages": 0})
        if u.path == "/api/run":
            return self.stream_run(q.get("goal", "").strip())
        self.send_json({"error": "not found"}, 404)

    def stream_run(self, goal):
        """Server-Sent Events: run the real agent in a thread and tail the JSONL log it writes."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        def push(obj):
            self.wfile.write(("data: " + json.dumps(obj) + "\n\n").encode("utf-8"))
            self.wfile.flush()

        if not goal:
            return push({"kind": "error", "text": "Empty goal."}) or push({"kind": "done"})
        if not os.environ.get("OPENROUTER_API_KEY"):
            push({"kind": "error", "text": "OPENROUTER_API_KEY is not set. Use Replay mode."})
            return push({"kind": "done"})
        if not RUN_LOCK.acquire(blocking=False):
            push({"kind": "error", "text": "Another run is still in progress."})
            return push({"kind": "done"})

        err = []

        def work():
            try:
                agent.run(goal, llm_fn=get_llm(), memory=SESSION_MEM, log_name=LIVE_LOG, verbose=False)
            except Exception as e:  # e.g. all free models busy
                err.append(str(e))

        t = threading.Thread(target=work, daemon=True)
        t.start()
        sent = 0
        try:
            while True:
                alive = t.is_alive()
                events = read_log(LIVE_LOG)
                for ev in events[sent:]:
                    push(ev)
                sent = len(events)
                if not alive:
                    break
                time.sleep(0.3)
            if err:
                push({"kind": "error", "text": err[0]})
            push({"kind": "done", "memory_messages": len(SESSION_MEM)})
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            t.join(timeout=0)
            RUN_LOCK.release()


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"Dashboard running at {url}  (Ctrl+C to stop)")
    print("Live mode:", "ready" if os.environ.get("OPENROUTER_API_KEY") else "no OPENROUTER_API_KEY -> Replay only")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
