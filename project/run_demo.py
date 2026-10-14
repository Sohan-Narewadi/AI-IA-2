"""Runs the demo goals through BOTH agents and saves logs (logs/*.jsonl, logs/demo_transcript.txt)."""
import contextlib, io, os, sys
from agent import run, openrouter_llm
from classical_agent import classical_agent

GOALS = [
    "List the local documents, read the campus AI report, and tell me the main finding about adoption "
    "and which department had the highest adoption rate.",
    "From the report, the AI licence budget is Rs. 2,50,000 and there are 1,250 users. Compute the cost per "
    "student and tell me whether it stays below the Rs. 250 target.",
    "Using department_scores.csv, find the average score improvement (after minus before) for the Electronics & "
    "Computer department, and the average adoption_pct across all departments. Then use web search to give a "
    "one-line definition of 'ReAct prompting'.",
]

if __name__ == "__main__":
    llm = openrouter_llm()
    buf = io.StringIO()

    class Tee:
        def write(self, s): sys.__stdout__.write(s); buf.write(s)
        def flush(self): sys.__stdout__.flush()

    with contextlib.redirect_stdout(Tee()):
        mem = []  # shared short-term memory across the three goals
        for i, g in enumerate(GOALS, 1):
            run(g, llm_fn=llm, memory=mem, log_name=f"demo_goal{i}")
        print("\n\n##### CLASSICAL RULE-BASED AGENT ON THE SAME GOALS #####")
        for g in GOALS:
            print(f"\nPercept: {g}\nResponse: {classical_agent(g)}")
        print("\nPercept: 2+3*4\nResponse:", classical_agent("2+3*4"))
        # follow-up that needs memory of the earlier turns
        run("Which of the numbers you computed earlier was the cost per student?", llm_fn=llm, memory=mem,
            log_name="demo_goal4_memory")
    with open(os.path.join("logs", "demo_transcript.txt"), "w", encoding="utf-8") as f:
        f.write(buf.getvalue())
