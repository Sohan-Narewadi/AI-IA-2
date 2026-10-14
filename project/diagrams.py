"""Clean diagrams drawn at true print size (inches) so fonts stay readable in the report."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
INK = "#1f2937"
C = dict(user="#FDE7C8", ctrl="#E3EDFB", llm="#D5F0E0", tool="#FBE0E0", log="#EADDF9", white="#FFFFFF", warn="#FFF3BF")


def box(ax, x, y, w, h, text, fc, fs=9, bold=False, ec=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.07", fc=fc, ec=ec, lw=1.1))
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                fontweight="bold" if bold else "normal", color=INK, linespacing=1.25)


def arrow(ax, p1, p2, label=None, lpos=(0, 0.09), fs=8, color=INK):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=11, lw=1.3, color=color,
                                 shrinkA=0, shrinkB=0))
    if label:
        ax.text((p1[0] + p2[0]) / 2 + lpos[0], (p1[1] + p2[1]) / 2 + lpos[1], label, ha="center",
                va="bottom" if lpos[1] >= 0 else "top", fontsize=fs, color="#374151", style="italic")


def canvas(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    return fig, ax


def architecture():
    fig, ax = canvas(6.5, 4.3)
    box(ax, 0.05, 1.75, 1.3, 0.95, "User\n(goal /\nquestion)", C["user"], bold=True, fs=8.5)
    # controller
    box(ax, 1.85, 0.2, 2.2, 3.85, "", C["ctrl"])
    ax.text(2.95, 3.82, "ReAct Agent Controller", ha="center", fontsize=9.5, fontweight="bold", color=INK)
    ax.text(2.95, 3.62, "agent.py", ha="center", fontsize=8, color="#4b5563", style="italic")
    for i, t in enumerate(["Short-term memory\n(message history)", "Prompt builder +\nThought-Action-Observation loop",
                           "Parser + guardrails\n(strips fake Observations)", "Logger\n(logs/*.jsonl + console)"]):
        box(ax, 2.0, 2.9 - i * 0.8, 1.9, 0.62, t, C["white"] if i < 3 else C["log"], fs=8)
    # LLM
    box(ax, 4.75, 3.0, 1.7, 1.1, "LLM\nNemotron-3-Super 120B\nvia OpenRouter API", C["llm"], fs=8.5, bold=True)
    # tools
    box(ax, 4.75, 0.05, 1.7, 2.6, "", C["tool"])
    ax.text(5.6, 2.42, "Tool layer", ha="center", fontsize=9.5, fontweight="bold", color=INK)
    ax.text(5.6, 2.24, "tools.py", ha="center", fontsize=8, color="#4b5563", style="italic")
    for i, t in enumerate(["calculator", "read_document", "csv_query", "web_search"]):
        box(ax, 4.9, 1.75 - i * 0.4, 1.4, 0.32, t, C["white"], fs=8.5)
    # arrows
    arrow(ax, (1.35, 2.45), (1.85, 2.45), "goal", (0, 0.06))
    arrow(ax, (1.85, 2.0), (1.35, 2.0), "answer", (0, -0.06))
    arrow(ax, (4.05, 3.75), (4.75, 3.75), "prompt", (0, 0.06))
    arrow(ax, (4.75, 3.35), (4.05, 3.35), "Thought +\nAction", (0, -0.06))
    arrow(ax, (4.05, 1.65), (4.75, 1.65), "Action", (0, 0.06))
    arrow(ax, (4.75, 1.2), (4.05, 1.2), "Observation", (0, -0.06))
    ax.text(5.6, 0.3, "Data sources:\ndocs/ folder, Wikipedia", ha="center", va="center", fontsize=7.5,
            color="#4b5563", style="italic")
    fig.savefig(os.path.join(OUT, "architecture.png"), dpi=220); plt.close(fig)


def toolflow():
    fig, ax = canvas(6.5, 3.6)
    def dia(cx, cy, t, hw=0.62, hh=0.45):
        ax.add_patch(Polygon([[cx, cy + hh], [cx + hw, cy], [cx, cy - hh], [cx - hw, cy]], fc=C["warn"], ec=INK, lw=1.1))
        ax.text(cx, cy, t, ha="center", va="center", fontsize=8, fontweight="bold", color=INK)
    y1 = 2.85
    box(ax, 0.05, y1 - 0.3, 1.0, 0.6, "User goal", C["user"], fs=8.5, bold=True)
    box(ax, 1.4, y1 - 0.3, 1.45, 0.6, "Add goal to memory,\nsend history to LLM", C["ctrl"], fs=8)
    box(ax, 3.2, y1 - 0.3, 1.3, 0.6, "LLM writes Thought\n+ Action / Final Answer", C["llm"], fs=8)
    dia(5.25, y1, "Final\nAnswer?")
    box(ax, 5.95, y1 - 0.3, 0.5, 0.6, "", C["log"])
    ax.text(6.2, y1, "Return\nanswer\n+ log", ha="center", va="center", fontsize=6.6, fontweight="bold", color=INK)
    arrow(ax, (1.05, y1), (1.4, y1)); arrow(ax, (2.85, y1), (3.2, y1)); arrow(ax, (4.5, y1), (4.63, y1))
    arrow(ax, (5.87, y1), (5.95, y1), "yes", (0, 0.12), fs=7.5)
    y2 = 1.15
    dia(5.25, y2, "Valid\ntool?")
    arrow(ax, (5.25, y1 - 0.45), (5.25, y2 + 0.45), "no", (0.17, -0.05), fs=7.5)
    box(ax, 2.95, y2 - 0.33, 1.45, 0.66, "Run tool\ncalculator | read_document\ncsv_query | web_search", C["tool"], fs=6.8)
    arrow(ax, (4.63, y2), (4.4, y2), "yes", (0, 0.1), fs=7.5)
    box(ax, 1.3, y2 - 0.33, 1.3, 0.66, "Append result to\nmemory as the\nObservation", C["ctrl"], fs=7.2)
    arrow(ax, (2.95, y2), (2.6, y2))
    # next step loop back to prompt box
    arrow(ax, (1.95, y2 + 0.33), (1.95, y1 - 0.3), "next step", (0.33, 0.0), fs=7.5)
    # invalid tool -> error observation -> memory
    box(ax, 4.35, 0.06, 2.1, 0.4, "ERROR observation (LLM self-corrects)", C["tool"], fs=7)
    arrow(ax, (5.25, y2 - 0.45), (5.25, 0.46), "no", (0.17, -0.02), fs=7.5)
    ax.plot([4.35, 1.95], [0.26, 0.26], color=INK, lw=1.3); arrow(ax, (1.95, 0.26), (1.95, y2 - 0.33))
    fig.savefig(os.path.join(OUT, "toolflow.png"), dpi=220); plt.close(fig)


if __name__ == "__main__":
    architecture(); toolflow()
