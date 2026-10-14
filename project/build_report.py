"""Builds the IA-II report (docx) from the college template, using real run logs."""
import copy, json, os, sys
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG = os.path.join(HERE, "figures")
TEMPLATE = os.path.join(ROOT, "AI IA2 report format.docx")
OUT = os.path.join(ROOT, "AI_IA2_Report.docx")

TOPIC = "Research Assistant Agent using a ReAct LLM Agent with Tool Orchestration"
MEMBERS = [("Roll No", "Name 1"), ("Roll No", "Name 2"), ("Roll No", "Name 3")]
if os.path.exists(os.path.join(HERE, "members.json")):
    MEMBERS = [tuple(m) for m in json.load(open(os.path.join(HERE, "members.json"), encoding="utf-8"))]

d = docx.Document(TEMPLATE)
P = d.paragraphs

# ---- title page: topic + members (template has 4 member lines; we have 3) ----
def set_text(p, text):
    for r in p.runs[1:]:
        r._r.getparent().remove(r._r)
    p.runs[0].text = text

set_text(P[3], TOPIC)
for i in range(3):
    set_text(P[6 + i], f"{MEMBERS[i][0]}: {MEMBERS[i][1]}")
P[9]._p.getparent().remove(P[9]._p)

# ---- drop everything after the title page's page break; we re-create the body ----
body = d.element.body
paras = list(d.paragraphs)
idx = next(i for i, p in enumerate(paras) if 'w:br w:type="page"' in p._p.xml)
cut_from = paras[idx + 1]._p
sect = body.find(qn("w:sectPr"))
el = cut_from
while el is not None and el is not sect:
    nxt = el.getnext()
    body.remove(el)
    el = nxt


# ---- helpers ----
def para(text="", bold=False, size=11, align=None, italic=False, space_after=4, color=None):
    p = d.add_paragraph()
    if align == "c": p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "j": p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(0)
    if text:
        r = p.add_run(text); r.bold = bold; r.italic = italic; r.font.size = Pt(size)
        if color: r.font.color.rgb = RGBColor(*color)
    return p

def rich(parts, size=11, align="j", style=None):
    """parts: list of (text, bold) tuples."""
    p = d.add_paragraph(style=style)
    if align == "j": p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(3)
    for t, b in parts:
        r = p.add_run(t); r.bold = b; r.font.size = Pt(size)
    return p

def _kn(p):
    p.paragraph_format.keep_with_next = True
    return p
def h1(t): return _kn(para(t, bold=True, size=14, space_after=6))
def h2(t): return _kn(para(t, bold=True, size=12, space_after=3))
def body_(t): return para(t, size=11, align="j", space_after=4)
def bullet(t, boldlead=None):
    p = d.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Inches(0.25); p.paragraph_format.first_line_indent = Inches(-0.2)
    p.add_run("•  ").font.size = Pt(11)
    if boldlead:
        r = p.add_run(boldlead); r.bold = True; r.font.size = Pt(11)
    r = p.add_run(t); r.font.size = Pt(11)
    return p

def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hexcolor)
    tcPr.append(sh)

def _borders(t, color="9AA5B1"):
    tblPr = t._tbl.tblPr
    bd = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:" + edge)
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:space"), "0"); e.set(qn("w:color"), color)
        bd.append(e)
    tblPr.append(bd)
    mar = OxmlElement("w:tblCellMar")
    for edge, v in (("top", 50), ("left", 90), ("bottom", 50), ("right", 90)):
        e = OxmlElement("w:" + edge); e.set(qn("w:w"), str(v)); e.set(qn("w:type"), "dxa"); mar.append(e)
    tblPr.append(mar)

def table(rows, widths=None, header=True, size=10, bold_first_col=True):
    t = d.add_table(rows=len(rows), cols=len(rows[0]))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    _borders(t)
    for i, row in enumerate(rows):
        trPr = t.rows[i]._tr.get_or_add_trPr()
        cs = OxmlElement("w:cantSplit"); trPr.append(cs)
        if i == 0 and header:
            th = OxmlElement("w:tblHeader"); trPr.append(th)
        for j, txt in enumerate(row):
            c = t.cell(i, j); c.text = ""
            c.vertical_alignment = 1  # center
            pp = c.paragraphs[0]
            pp.paragraph_format.space_after = Pt(0); pp.paragraph_format.space_before = Pt(0)
            r = pp.add_run(txt); r.font.size = Pt(size)
            if i < len(rows) - 1: pp.paragraph_format.keep_with_next = True
            if header and i == 0:
                r.bold = True; r.font.color.rgb = RGBColor(255, 255, 255); shade(c, "1F3864")
            else:
                if j == 0 and bold_first_col: r.bold = True
                if i % 2 == 0: shade(c, "F1F4F9")
            if widths: c.width = Inches(widths[j])
    d.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

def fig(name, width, caption):
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(1); p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(os.path.join(FIG, name), width=Inches(width))
    para(caption, italic=True, size=9, align="c", space_after=6)

def page_break():
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# ---- real metrics from logs ----
def load(i):
    n = f"demo_goal{i}" + ("_memory" if i == 4 else "") + ".jsonl"
    return [json.loads(l) for l in open(os.path.join(HERE, "logs", n), encoding="utf-8")]
stats = []
for i in (1, 2, 3, 4):
    r = load(i)
    stats.append((sum(x["kind"] == "llm" for x in r), [x["tool"] for x in r if x["kind"] == "tool"],
                  next(x["text"] for x in r if x["kind"] == "final")))
tcount = lambda i: len(stats[i - 1][1])

# =====================================================================
# PAGE 2: intro
# =====================================================================
para(TOPIC, bold=True, size=18, align="c", space_after=6)
para("Group of 3, same lab batch  |  Demo to be taken in lab duration", size=10, align="c", italic=True, space_after=10)

h1("1. Introduction and Abstract")
body_("Classical agents studied in the syllabus (simple reflex and model-based agents) choose actions from fixed "
      "condition-action rules. Modern agentic AI replaces the hand-written rules with a Large Language Model (LLM) "
      "that reads a goal, decides what to do next, calls external tools, observes the result and repeats until the "
      "goal is met. The focus is therefore on tool usage, reasoning and orchestration, not on model training.")
body_("This project builds a Research Assistant Agent. The user gives a goal in plain English, for example "
      "\"read the campus AI report and compute the cost per student\". The agent plans the steps, reads local "
      "documents and CSV files, uses a calculator for exact arithmetic, searches the web for general facts, and returns "
      "a cited answer. Every step (Thought, Action, Observation) is logged for inspection. We also implement a "
      "classical rule-based agent and run both on the same goals to compare them (Part C).")
rich([("AI framework(s) used: ", True), ("ReAct-style agent written from scratch in Python (Thought, Action, Observation loop, "
      "no heavy framework, so every step is visible and explainable); OpenRouter API (OpenAI-compatible, free tier) "
      "for LLM access via the openai Python SDK.", False)])
rich([("Tools integrated with agent: ", True), ("(1) Calculator (safe AST evaluator), (2) Document reader (txt/pdf) with a "
      "document lister, (3) CSV query tool (simple database), (4) Web search (Wikipedia search API).", False)])

# =====================================================================
h1("2. Part A: Agent Design (Modern View)")
table([
    ["Element", "Design decision"],
    ["Goal of the agent", "Answer multi-part research questions by combining facts from local documents, data tables and the web, "
                          "with exact numeric results and source citations."],
    ["Agent role", "Autonomous research assistant: it decomposes the goal, chooses tools, interprets observations, "
                   "recovers from errors and decides when it has enough information to answer."],
    ["Tools used", "calculator, list_documents, read_document, csv_query, web_search (details in Part B)."],
    ["Memory type", "Short-term / context memory: the full message history (system prompt, goals, thoughts, "
                    "observations) is resent to the LLM at each step and kept across user turns in one session."],
    ["Planning strategy", "ReAct (Reason + Act): at each step the LLM writes a Thought, picks one Action with an input, "
                          "receives a real Observation, and repeats (max 10 steps) until it writes a Final Answer."],
    ["Environment (PEAS)", "Performance: answer correctness, correct tool use, few steps. Environment: local docs folder, "
                           "CSV files, Wikipedia. Actuators: tool calls + answer text. Sensors: tool observations and user text."],
], widths=[1.55, 4.95], size=10)

# =====================================================================
h1("3. Part B: Implementation (Modern AI Tools)")
h2("3.1 LLM-based agent")
body_("The agent is one LLM that acts as the planner and reasoner. We call NVIDIA Nemotron-3-Super (120B parameters, "
      "12B active) through OpenRouter's free tier, with automatic fallback to Gemma-4-31B and Nemotron-3-Ultra if a model "
      "is rate-limited or unavailable. Reasons for this choice: (a) it is free, so the project needs no paid credits; "
      "(b) the model is large enough to follow the strict Thought/Action/Observation text format; (c) OpenRouter exposes an "
      "OpenAI-compatible API, so the model can be swapped by changing one string without touching the agent code. "
      "Temperature is 0.1 to keep tool decisions stable. The system prompt (Fig. 7) defines the tools, the exact output format and "
      "the rules (never invent facts, use the calculator for all arithmetic, one tool per step).")
h2("3.2 Tools used")
table([
    ["Tool", "What it does", "Why chosen / features"],
    ["calculator", "Evaluates arithmetic expressions", "LLMs make arithmetic errors; the tool is exact. Uses Python ast with a whitelist of operators, "
                   "never eval(), so it is safe against code injection."],
    ["list_documents / read_document", "Lists and reads .txt and .pdf files in docs/", "Gives the agent private knowledge it was not trained on "
                   "(document reader). PDF via pypdf; output truncated at 4000 chars; path sanitised with basename."],
    ["csv_query", "Previews a CSV or returns count/sum/mean/min/max of a numeric column", "Acts as a simple database tool (CSV/JSON option in the brief)."],
    ["web_search", "Wikipedia search API, plus intro paragraph of the top hit", "Brings in open-world facts; no API key needed, so the demo is "
                   "reproducible by anyone."],
], widths=[1.45, 1.95, 3.1], size=9.5)
h2("3.3 Multi-step reasoning")
body_("The agent never answers from a single call. In Goal 3 (see logs) it first previewed the CSV to learn the column names, then "
      "called the calculator twice (mean adoption, score improvement), then searched the web, noticed the first search "
      "returned irrelevant pages, reformulated the query, and only then wrote the answer. This sequence was chosen by the LLM at "
      "run time; nothing in the code fixes it. Orchestration code in agent.py handles four things:")
bullet(" parses the LLM text (also tolerates JSON-style actions), validates the tool name, runs the tool, and feeds back the Observation.", "Parse and dispatch:")
bullet(" the LLM sometimes ignores the stop sequence and invents its own Observation. In our first run it fabricated a CSV with wrong "
       "columns and numbers and answered from it. agent.py now cuts the output at the first \"Observation:\", so only real tool output is used.", "Hallucination guardrail:")
bullet(" invalid format or unknown tool returns an ERROR observation and the LLM corrects itself on the next step.", "Error recovery:")
bullet(" max 10 steps prevents infinite loops.", "Step limit:")

# =====================================================================
h2("3.4 Architecture diagram")
fig("architecture.png", 5.6, "Fig. 1: Architecture. The controller keeps memory, calls the LLM, validates the Action and dispatches to tools; every step is logged.")
h2("3.5 Tool flow diagram")
fig("toolflow.png", 6.3, "Fig. 2: Tool flow of one goal: loop until the LLM emits a Final Answer or the step limit is reached.")

# =====================================================================
h2("3.6 Observable agent behaviour (logs / traces)")
body_("Every run writes a JSON-lines trace (logs/demo_goalN.jsonl) with a timestamp and one record per event: goal, llm (model + "
      "full Thought/Action text), tool (tool name, input, observation) and final. The same trace is printed live on the console, "
      "and logs/demo_transcript.txt holds the whole session. The table summarises the four demo runs; the screenshots follow.")
table([
    ["Goal", "LLM steps", "Tools called (in order)", "Result"],
    ["1 Read report, find main finding + top department", str(stats[0][0]), ", ".join(stats[0][1]), "68% weekly use; ECE highest at 81% (correct)"],
    ["2 Cost per student vs Rs. 250 target", str(stats[1][0]), ", ".join(stats[1][1]), "Rs. 200.0, below target (correct)"],
    ["3 CSV statistics + web definition", str(stats[2][0]), ", ".join(stats[2][1]), "Improvement 7.5, mean adoption 64.4% (both correct); definition weakly sourced"],
    ["4 Follow-up using memory only", str(stats[3][0]), "(none needed)", "Recalled Rs. 200.0 from earlier turn"],
], widths=[2.0, 0.6, 2.0, 1.9], size=9.5)
h2("3.7 Code repository / notebook")
body_("Files in project/: agent.py (ReAct loop, LLM client, logging), tools.py (4 tools), classical_agent.py (rule-based baseline), "
      "run_demo.py (runs the demo goals on both agents), make_assets.py and build_report.py (figures and this report), docs/ "
      "(sample report and CSV), logs/ (interaction logs). Run: set OPENROUTER_API_KEY, then python run_demo.py, or python agent.py "
      "for an interactive chat that keeps memory across questions.")
h2("3.8 Agent interaction logs, prompts and output screenshots")
fig("shot_goal1.png", 5.0, "Fig. 3: Goal 1 trace. Two tool calls, then a cited Final Answer.")
fig("shot_goal2.png", 5.0, "Fig. 4: Goal 2 trace. The agent uses the calculator tool instead of doing the division itself.")
fig("shot_goal4.png", 5.0, "Fig. 5: Goal 4. A follow-up answered from short-term memory without any tool call.")
fig("shot_goal3.png", 4.0, "Fig. 6: Goal 3 trace. Five tool calls, including a re-planned web search after an irrelevant result.")
fig("shot_prompt.png", 4.6, "Fig. 7: System prompt given to the LLM.")

# =====================================================================
h1("4. Part C: Analysis and Comparison")
body_("To compare fairly, classical_agent.py implements a simple reflex agent: an ordered list of keyword/pattern rules, the first "
      "matching rule fires, no LLM, no memory. We gave it the same three goals (Fig. 8).")
fig("shot_classical.png", 5.0, "Fig. 8: Classical rule-based agent on the same goals. It can only run a rule that matches a fixed pattern.")
table([
    ["Aspect", "Classical agent (syllabus)", "Modern agent (this activity)", "Evidence from our runs"],
    ["Decision logic", "Rule-based, hard-coded", "LLM-driven", "Classical failed 2 of 3 goals (NO RULE MATCHED); LLM agent completed 3 of 3"],
    ["Planning", "Static logic", "Dynamic planning", "Goal 3: LLM re-planned after a bad search and used 5 tool calls"],
    ["Memory", "None", "Contextual memory", "Goal 4: recalled Rs. 200.0 without re-computing"],
    ["Reasoning depth", "Single step", "Multi-step reasoning", "Classical answers 1 percept with 1 action; LLM chained 1-5 tool calls"],
    ["Input", "Exact patterns only", "Natural language", "Goal 1 triggered only the 'list documents' rule in the classical agent and never read the report"],
    ["Reliability", "Deterministic, always same output", "Probabilistic; can hallucinate", "LLM invented an Observation in our first run (fixed by guardrail)"],
    ["Cost / speed", "Instant, free", "Several API calls per goal", "LLM goals took 1-6 LLM calls each"],
    ["Explainability", "Rule that fired is obvious", "Thought text + logs", "Thought lines make each decision auditable"],
], widths=[1.1, 1.35, 1.45, 2.6], size=9)

h1("5. Discussion and Takeaways")
bullet(" The LLM handled phrasing it was never programmed for, which is the main gain over rule-based agents.", "Flexibility:")
bullet(" the model is right to call a calculator but can still misuse tools. We saw it wrap actions in JSON, drift from the format, "
       "and fabricate an Observation. Parsing tolerance and the guardrail turned these into recoverable events.", "Orchestration matters as much as the model:")
bullet(" in Goal 3 the Wikipedia search returned irrelevant pages (terrorism, Llama) and the final definition of ReAct was only "
       "loosely supported by the search output (it quoted the paper title). A stronger search API (e.g. Tavily/Serper) and a rule that the "
       "agent must say \"not found\" when evidence is missing would fix this. We report it as a limitation rather than hide it.", "Limitation found:")
bullet(" free models can be rate-limited or removed (all three of our original default model names had been retired by the time we ran it), so the "
       "fallback list is necessary.", "Operational lesson:")
bullet(" a deterministic rule-based agent is better for fixed, safety-critical tasks; the LLM agent is better for open-ended tasks. "
       "A hybrid (LLM for planning, rules for validation) is the practical design.", "When to use which:")

h1("6. Conclusion")
body_("We built a working LLM-based ReAct agent with four tools, short-term memory, multi-step planning, error recovery and "
      "full JSONL traces, and compared it with a classical rule-based agent. On three realistic goals the modern agent produced correct, "
      "cited answers (including exact arithmetic through the calculator tool) while the classical agent could solve only the one goal "
      "that matched a hard-coded rule. The project shows that agentic AI extends classical agent ideas (perceive, decide, act) with "
      "dynamic planning and contextual memory, and that reliable behaviour depends on careful tool design and guardrails around the model.")
body_("Future work: a stronger search tool, a Google Calendar tool (OAuth 2.0) for scheduling, long-term memory with a vector store, and an automatic evaluation set.")

h1("7. References")
for n, t in enumerate([
    "S. Yao et al., \"ReAct: Synergizing Reasoning and Acting in Language Models,\" ICLR 2023. arXiv:2210.03629.",
    "S. Russell and P. Norvig, Artificial Intelligence: A Modern Approach, 4th ed., Pearson, 2020 (agent types, PEAS).",
    "OpenRouter API documentation, https://openrouter.ai/docs (OpenAI-compatible chat completions).",
    "MediaWiki Action API, https://www.mediawiki.org/wiki/API:Main_page (web_search tool).",
    "Python ast module documentation, https://docs.python.org/3/library/ast.html (safe calculator).",
], 1):
    p = d.add_paragraph(); p.paragraph_format.space_after = Pt(1)
    r = p.add_run(f"[{n}] {t}"); r.font.size = Pt(10)

d.save(OUT)
print("saved", OUT)
