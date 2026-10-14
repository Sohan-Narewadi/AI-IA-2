"""Builds report figures: architecture diagram, tool-flow diagram, terminal-style screenshots of real logs."""
import json, os, re, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, text, fc, ec="#333", fs=9, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, p1, p2, label=None, rad=0.0, color="#333"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=14, lw=1.4, color=color,
                                 connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 + 0.12, label, fontsize=8, ha="center",
                color=color, style="italic", bbox=dict(fc="white", ec="none", pad=0.5))


def architecture():
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.set_xlim(0, 10); ax.set_ylim(-0.9, 6.2); ax.axis("off")
    box(ax, 0.2, 2.6, 1.5, 1.0, "User\n(goal / question)", "#fde9c9", bold=True)
    box(ax, 2.4, 1.5, 3.3, 3.2, "", "#e8f0fe")
    ax.text(4.05, 4.5, "ReAct Agent Controller (agent.py)", ha="center", fontsize=10, fontweight="bold")
    box(ax, 2.6, 3.3, 2.9, 0.8, "Prompt builder + short-term\nmemory (message history)", "#ffffff")
    box(ax, 2.6, 2.3, 2.9, 0.8, "Parser + guardrails\n(cuts fake Observations,\nvalidates tool name)", "#ffffff", fs=8.5)
    box(ax, 2.6, 1.65, 2.9, 0.5, "Loop: Thought → Action → Observation", "#ffffff", fs=8.5)
    box(ax, 6.6, 3.9, 2.9, 1.5, "LLM (OpenRouter API)\nNemotron-3-Super 120B (free)\nfallback: Gemma-4-31B", "#d9f2e3", bold=True)
    box(ax, 6.6, 0.3, 3.0, 3.1, "", "#fdeaea")
    ax.text(8.1, 3.15, "Tool layer (tools.py)", ha="center", fontsize=10, fontweight="bold")
    for i, t in enumerate(["calculator (safe AST)", "read_document / list_documents", "csv_query (CSV 'database')", "web_search (Wikipedia API)"]):
        box(ax, 6.75, 2.35 - i * 0.55, 2.7, 0.42, t, "#ffffff", fs=8.5)
    box(ax, 2.6, 0.15, 2.9, 0.9, "Observability\nlogs/*.jsonl + console trace", "#f3e8ff", bold=True, fs=8.5)
    box(ax, 0.2, 0.5, 1.8, 0.6, "docs/ folder\n(txt, pdf, csv)", "#eeeeee", fs=8.5)
    arrow(ax, (1.7, 3.1), (2.4, 3.1), "goal")
    arrow(ax, (5.5, 3.7), (6.6, 4.4), "messages", rad=-0.15)
    arrow(ax, (6.6, 4.1), (5.5, 3.5), "Thought+Action", rad=-0.15)
    arrow(ax, (5.5, 2.7), (6.6, 2.2), "tool call")
    arrow(ax, (6.6, 1.5), (5.5, 1.9), "Observation", rad=0.1)
    arrow(ax, (4.05, 1.65), (4.05, 1.05), "writes")
    arrow(ax, (2.4, 2.2), (1.7, 2.9), "Final Answer", rad=0.2)
    arrow(ax, (8.05, -0.2), (8.05, 0.3), "reads", color="#777")
    ax.set_title("Fig. 1  Architecture of the Research Assistant Agent", fontsize=11, fontweight="bold", y=0.98)
    fig.savefig(os.path.join(OUT, "architecture.png"), dpi=170, bbox_inches="tight"); plt.close(fig)


def toolflow():
    fig, ax = plt.subplots(figsize=(8.5, 7.4))
    ax.set_xlim(0, 9.0); ax.set_ylim(0, 7.4); ax.axis("off")
    box(ax, 3.0, 6.7, 2.5, 0.55, "User goal", "#fde9c9", bold=True)
    box(ax, 2.75, 5.65, 3.0, 0.65, "Add goal to memory;\nsend history to LLM", "#e8f0fe")
    box(ax, 2.75, 4.55, 3.0, 0.65, "LLM output: Thought +\nAction / Final Answer", "#d9f2e3")
    ax.add_patch(plt.Polygon([[4.25, 3.95], [5.5, 3.35], [4.25, 2.75], [3.0, 3.35]], fc="#fff4c2", ec="#333", lw=1.3))
    ax.text(4.25, 3.35, "Final Answer?", ha="center", va="center", fontsize=9, fontweight="bold")
    box(ax, 6.2, 3.05, 2.1, 0.6, "Return answer\n+ save log", "#f3e8ff", bold=True)
    ax.add_patch(plt.Polygon([[4.25, 2.45], [5.55, 1.95], [4.25, 1.45], [2.95, 1.95]], fc="#fff4c2", ec="#333", lw=1.3))
    ax.text(4.25, 1.95, "Valid tool?", ha="center", va="center", fontsize=9, fontweight="bold")
    box(ax, 0.2, 1.65, 2.3, 0.6, "Error Observation\n(self-correction)", "#fdeaea")
    box(ax, 2.2, 0.35, 4.1, 0.65, "Run tool: calculator | read_document | csv_query | web_search", "#fdeaea", fs=8.5)
    box(ax, 6.1, 1.65, 2.3, 0.6, "Append real Observation\nto memory", "#e8f0fe", fs=8.5)
    arrow(ax, (4.25, 6.7), (4.25, 6.3)); arrow(ax, (4.25, 5.65), (4.25, 5.2)); arrow(ax, (4.25, 4.55), (4.25, 3.95))
    arrow(ax, (5.5, 3.35), (6.2, 3.35), "yes")
    arrow(ax, (4.25, 2.75), (4.25, 2.45), "no")
    arrow(ax, (2.95, 1.95), (2.5, 1.95), "no")
    arrow(ax, (4.25, 1.45), (4.25, 1.0), "yes")
    arrow(ax, (6.3, 0.7), (7.1, 1.65), "")
    ax.plot([1.35, 1.35], [2.25, 5.95], color="#333", lw=1.4)
    arrow(ax, (1.35, 5.95), (2.75, 5.95))
    ax.plot([8.1, 8.7, 8.7], [1.95, 1.95, 5.95], color="#333", lw=1.4)
    arrow(ax, (8.7, 5.95), (5.75, 5.95), "next step")
    ax.set_title("Fig. 2  Tool-flow (ReAct loop, max 10 steps)", fontsize=11, fontweight="bold")
    fig.savefig(os.path.join(OUT, "toolflow.png"), dpi=170, bbox_inches="tight"); plt.close(fig)


def font(sz):
    for f in ("consola.ttf", "cour.ttf", "DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def term_image(lines, name, title, width_chars=98):
    f = font(15)
    wrapped = []
    for ln in lines:
        wrapped += textwrap.wrap(ln, width_chars, replace_whitespace=False, drop_whitespace=False) or [""]
    h = 44 + 20 * len(wrapped) + 14
    img = Image.new("RGB", (int(width_chars * 9.1) + 30, h), "#1e1e1e")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, img.width, 30], fill="#333")
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        d.ellipse([10 + i * 20, 9, 22 + i * 20, 21], fill=c)
    d.text((80, 7), title, fill="#ccc", font=font(13))
    y = 40
    for ln in wrapped:
        col = "#d4d4d4"
        s = ln.lstrip()
        if s.startswith(("=== GOAL", "Percept")): col = "#ffd866"
        elif s.startswith("[Step"): col = "#78dce8"
        elif s.startswith("Thought"): col = "#a9dc76"
        elif s.startswith(("Action:", "Action Input")): col = "#fc9867"
        elif s.startswith("Observation") or s.startswith("Response"): col = "#ab9df2"
        elif s.startswith((">>>", "Final Answer")): col = "#ff6188"
        d.text((15, y), ln, fill=col, font=f)
        y += 20
    img.save(os.path.join(OUT, name))


def short(s, n=300):
    return s if len(s) <= n else s[:n] + " ...[truncated in screenshot]"


def screenshots():
    for i in (1, 2, 3, 4):
        p = os.path.join(HERE, "logs", f"demo_goal{i}" + ("_memory" if i == 4 else "") + ".jsonl")
        recs = [json.loads(l) for l in open(p, encoding="utf-8")]
        lines = []
        for r in recs:
            if r["kind"] == "goal": lines += [f"=== GOAL: {r['text']}", ""]
            elif r["kind"] == "llm": lines += [f"[Step {r['step']}] model={r['model']}"] + r["text"].split("\n")
            elif r["kind"] == "tool":
                lines += [short("Observation: " + r["observation"].replace("\n", " | ")), ""]
            elif r["kind"] == "final": lines += [">>> FINAL ANSWER: " + r["text"]]
        term_image(lines, f"shot_goal{i}.png", f"python run_demo.py   (goal {i})")
    t = open(os.path.join(HERE, "logs", "demo_transcript.txt"), encoding="utf-8").read()
    seg = t.split("##### CLASSICAL RULE-BASED AGENT ON THE SAME GOALS #####")[1].split("=== GOAL")[0]
    lines = ["##### CLASSICAL RULE-BASED AGENT ON THE SAME GOALS #####"] + [short(l, 200) for l in seg.strip().split("\n")]
    term_image(lines, "shot_classical.png", "python classical_agent.py")
    sys_prompt = open(os.path.join(HERE, "agent.py"), encoding="utf-8").read().split('SYSTEM = """')[1].split('"""')[0]
    term_image(["SYSTEM PROMPT (agent.py)", ""] + sys_prompt.split("\n"), "shot_prompt.png", "system prompt")


if __name__ == "__main__":
    import diagrams; diagrams.architecture(); diagrams.toolflow(); screenshots()
    print(os.listdir(OUT))
