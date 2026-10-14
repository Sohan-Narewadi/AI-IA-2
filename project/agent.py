"""ReAct Research Assistant Agent (LLM via OpenRouter, tools in tools.py).

Usage:  python agent.py "your question"     one-shot goal
        python agent.py                     interactive chat (short-term memory kept across turns)
Needs the OPENROUTER_API_KEY environment variable.
"""
import datetime, json, os, re, sys, time
from tools import TOOLS

MODELS = os.environ.get(
    "AGENT_MODELS",
    "nvidia/nemotron-3-super-120b-a12b:free,google/gemma-4-31b-it:free,nvidia/nemotron-3-ultra-550b-a55b:free").split(",")
MAX_STEPS = 10
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

SYSTEM = """You are a Research Assistant Agent. You solve the user's goal by reasoning step by step and calling tools.
Available tools:
{tools}

Respond in EXACTLY this format, one step at a time:
Thought: <your reasoning about what to do next>
Action: <tool name>
Action Input: <input string for the tool>

After each Action you will receive an Observation. When you have enough information reply with:
Thought: <final reasoning>
Final Answer: <complete answer; cite which documents/tools the facts came from>

Rules: never invent facts; use calculator for any arithmetic; use list_documents/read_document for questions about local files; call ONE tool per step."""


def openrouter_llm():
    """Returns llm_fn(messages) -> (model_name, text), with retry and model fallback."""
    from openai import OpenAI
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"])

    def call(messages):
        last = None
        for model in MODELS:
            for _ in range(2):
                try:
                    r = client.chat.completions.create(model=model, messages=messages,
                                                       temperature=0.1, stop=["Observation:"])
                    if r.choices and r.choices[0].message.content:
                        return model, r.choices[0].message.content
                except Exception as e:
                    last = e
                    time.sleep(2)
        raise RuntimeError(f"all models failed: {last}")
    return call


def parse(text):
    if "Final Answer:" in text:
        return "final", text.split("Final Answer:", 1)[1].strip(), None
    try:  # tolerate models that drift into JSON-style actions
        j = json.loads(text[text.index("{"): text.rindex("}") + 1])
        if "Action" in j:
            return "action", str(j["Action"]).strip(), str(j.get("Action Input", "")).strip()
    except ValueError:
        pass
    m = re.search(r"Action:\s*(.+?)\s*\n\s*Action Input:\s*(.*)", text, re.S)
    if m:
        return "action", m.group(1).strip(), m.group(2).strip().strip("\"'`")
    return "invalid", text, None


def run(goal, llm_fn=None, memory=None, log_name=None, verbose=True):
    """memory: message list reused across calls = short-term conversational memory."""
    llm_fn = llm_fn or openrouter_llm()
    tools_desc = "\n".join(f"- {n}: {d}" for n, (_, d) in TOOLS.items())
    messages = memory if memory is not None else []
    if not messages:
        messages.append({"role": "system", "content": SYSTEM.format(tools=tools_desc)})
    messages.append({"role": "user", "content": f"Goal: {goal}"})
    os.makedirs(LOG_DIR, exist_ok=True)
    log_name = log_name or datetime.datetime.now().strftime("run_%Y%m%d_%H%M%S")
    jl = open(os.path.join(LOG_DIR, log_name + ".jsonl"), "w", encoding="utf-8")

    def emit(kind, **kw):
        jl.write(json.dumps({"t": datetime.datetime.now().isoformat(timespec="seconds"),
                             "kind": kind, **kw}) + "\n")
        jl.flush()

    def say(s):
        if verbose:
            print(s)

    say(f"\n=== GOAL: {goal}")
    emit("goal", text=goal)
    answer = "(stopped: step limit reached)"
    for step in range(1, MAX_STEPS + 1):
        model, out = llm_fn(messages)
        # Guardrail: some models ignore the `stop` param and hallucinate their own Observation.
        # Cut everything from the first "Observation:" so only REAL tool output is ever used.
        out = re.split(r"\n?\s*Observation:", out, maxsplit=1)[0].strip()
        kind, a, b = parse(out)
        say(f"\n[Step {step}] model={model}\n{out}")
        emit("llm", step=step, model=model, text=out)
        messages.append({"role": "assistant", "content": out})
        if kind == "final":
            answer = a
            break
        if kind == "invalid":
            obs = "ERROR: reply must contain 'Action:' and 'Action Input:' or 'Final Answer:'."
        elif a not in TOOLS:
            obs = f"ERROR: unknown tool '{a}'. Tools: {', '.join(TOOLS)}"
        else:
            obs = TOOLS[a][0](b)
        say(f"Observation: {obs}")
        emit("tool", step=step, tool=a, input=b, observation=obs)
        messages.append({"role": "user", "content": f"Observation: {obs}"})
    say(f"\n>>> FINAL ANSWER: {answer}")
    emit("final", text=answer)
    jl.close()
    return answer


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run(" ".join(sys.argv[1:]))
    else:
        mem = []
        while (q := input("\nYou> ").strip()) not in ("", "exit", "quit"):
            run(q, memory=mem)
