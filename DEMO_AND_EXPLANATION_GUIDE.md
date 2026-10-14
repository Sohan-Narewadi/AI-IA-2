# AI IA-II: Demo and Explanation Guide (for the group)

Project: **Research Assistant Agent** (ReAct LLM agent with tools)
Group: Sheersh Nagaich (16015024046), Radhesh Nair (16015024047), Sohan Narewadi (16015024048)

---

## 1. The project in 60 seconds (say this first)

> "Normal programs follow fixed rules. An **agentic AI** is different: we give it a **goal in plain English**, and an
> LLM (the 'brain') decides **what steps to take**, **which tool to use**, looks at the **result**, and repeats until it
> can answer. We built a **Research Assistant Agent**. It can read documents, query a CSV file, search the web and use a
> calculator. We also built a **classical rule-based agent** and compared the two."

Key words to remember: **Goal → Thought → Action → Observation → … → Final Answer** (this loop is called **ReAct** = Reason + Act).

---

## 2. How to run it (before the evaluator arrives)

You need Python and internet. Open **PowerShell** and run:

```powershell
cd C:\Users\sohan\OneDrive\Desktop\AI-IA-2\project
pip install openai pypdf
$env:OPENROUTER_API_KEY="PASTE-YOUR-NEW-KEY-HERE"
```

(Get a key free at openrouter.ai -> Keys. Create a **new** key; delete the old one that was pasted in chat.
The key only lasts for that PowerShell window, so set it again if you open a new one.)

### Option A: full demo (recommended, ~1-2 minutes)
```powershell
python run_demo.py
```
Runs 3 goals through the LLM agent, then the same goals through the classical agent, then a memory follow-up.
Logs are saved in `project\logs\`.

### Option B: live demo with the evaluator's own question
```powershell
python agent.py "Read the campus AI report and tell me which department had the highest adoption"
```
Or a chat that **remembers** earlier questions:
```powershell
python agent.py
You> What is the cost per student if the budget is 250000 and users are 1250?
You> And is that below the target in the report?
You> exit
```

### Option C: classical agent alone
```powershell
python classical_agent.py "2+3*4"          # works (matches a rule)
python classical_agent.py "compute cost per student from the report"   # NO RULE MATCHED
```

### If something goes wrong
| Problem | Fix |
|---|---|
| `KeyError: OPENROUTER_API_KEY` | You forgot to set the key in this PowerShell window. |
| `all models failed ... 404` or rate-limit | Free models change. Pick another from openrouter.ai/models (filter "free") and run `$env:AGENT_MODELS="model-id-1,model-id-2"` then retry. |
| Slow or timeout | Free tier is busy. Wait 30 s and run again. |
| No internet | The web_search tool fails but the others still work; show the saved logs instead (see section 5). |

**Backup plan:** if the live run fails, open `project\logs\demo_transcript.txt` and the screenshots in the report. They are real outputs from our runs.

---

## 3. Suggested demo script (5 minutes)

1. **Show the problem (30 s):** "Goal in English, agent figures out the steps." Open the report's architecture diagram (Fig. 1).
2. **Run Goal 1 live** (`python agent.py "..."` or `run_demo.py`). Point at the printed trace:
   - `Thought:` = the LLM reasoning
   - `Action:` = which tool it picked
   - `Observation:` = the real result from the tool
   - `Final Answer:` = the cited answer
3. **Show the calculator step (Goal 2):** "The LLM does not do the maths itself. It calls the calculator tool, so the answer is exact (250000/1250 = 200)."
4. **Show multi-step (Goal 3):** the agent used 5 tool calls, noticed the first web search was irrelevant, and searched again.
5. **Show memory:** ask "Which number was the cost per student?" and it answers from earlier conversation without calling a tool.
6. **Show the classical agent failing:** `python classical_agent.py "<a complex goal>"` gives `NO RULE MATCHED`.
7. **Show logs:** open `project\logs\demo_goal3.jsonl` (every step with timestamp).
8. **Be honest about a limitation** (evaluators like this): web search is weak (Wikipedia only) and the model once invented its own tool result; we fixed it with a guardrail.

---

## 4. Explain every file simply

| File | What it is | Simple explanation |
|---|---|---|
| `agent.py` | The agent | Runs the loop: send conversation to the LLM, read its Thought/Action, run the tool, feed the Observation back. Stops at Final Answer or after 10 steps. Writes the log. |
| `tools.py` | The 4 tools | calculator (safe maths), read_document (reads txt/pdf), csv_query (like a small database), web_search (Wikipedia). |
| `classical_agent.py` | Old-style agent | A list of fixed "if the text looks like X, do Y" rules. No AI, no memory. |
| `run_demo.py` | Demo runner | Runs the 3 goals + memory test + classical agent, saves everything to `logs/`. |
| `docs/` | Data the agent reads | `campus_ai_report.txt` and `department_scores.csv` (sample data we wrote). |
| `logs/` | Observable behaviour | `.jsonl` = one line per event (goal, LLM reply, tool result, final answer). `demo_transcript.txt` = everything as text. |
| `figures/` | Diagrams and screenshots | Used in the report. |
| `make_assets.py`, `diagrams.py`, `build_report.py` | Report generators | Only for making the report. Not needed for the demo. |

### The three important design ideas
1. **ReAct loop:** the LLM must reply in the format `Thought / Action / Action Input`. Our code reads that, runs the tool and sends back `Observation`. The LLM then decides the next step. *The order of steps is chosen by the LLM, not by our code.*
2. **Memory:** we keep the whole message list (goal, thoughts, observations) and resend it every step. That is **short-term / context memory**. It is why the follow-up question works.
3. **Guardrails:** (a) cut the LLM text at the first "Observation:" so it cannot invent tool results, (b) check the tool name is valid, (c) return an ERROR observation so the LLM can correct itself, (d) 10-step limit.

---

## 5. Which LLM and why

- Model: **NVIDIA Nemotron-3-Super 120B** through **OpenRouter** (free tier). Fallbacks: Gemma-4-31B, Nemotron-3-Ultra.
- Why: free, big enough to follow the strict format, and OpenRouter uses the same API style as OpenAI so the model can be swapped by changing one string.
- Framework: we wrote the ReAct loop ourselves (no LangChain) so every step is visible and we can explain it.

---

## 6. Modern agent vs classical agent (Part C in simple words)

| | Classical (rule-based) | Modern (our LLM agent) |
|---|---|---|
| Decides using | Fixed if-then rules | LLM reasoning |
| Planning | None, one step | Plans multiple steps dynamically |
| Memory | None | Remembers the conversation |
| Input | Exact patterns only | Normal English |
| In our test | Solved 1 trivial case, failed 2 of 3 goals | Solved 3 of 3 correctly |
| Downside of modern | Can make mistakes / hallucinate, uses API calls, slower | |
| Advantage of classical | Fast, free, always the same answer, easy to trust | |

---

## 7. Likely evaluator questions and answers

**Q1. What is an agent? What makes yours "agentic"?**
A program that perceives, decides and acts toward a goal. Ours is agentic because the LLM chooses the steps and tools by itself and loops until the goal is done, instead of following a fixed script.

**Q2. What is ReAct?**
Reason + Act. The model writes a Thought, takes an Action (tool call), reads the Observation, and repeats. (Paper: Yao et al., ICLR 2023.)

**Q3. Why do you need tools? Can't the LLM just answer?**
LLMs are bad at exact arithmetic, don't know our private documents, and can hallucinate. Tools give exact, up-to-date or private information.

**Q4. Which tools did you use and why?**
Calculator (exact maths), document reader (private knowledge), CSV query (simple database), web search (outside facts). Each shows a different kind of tool: compute, files, data, web.

**Q5. What type of memory does the agent have?**
Short-term / context memory: the message history is resent at each step and kept across questions in one session. No long-term memory (future work: vector database).

**Q6. What is your planning strategy?**
ReAct step-by-step planning: plan one step at a time based on the latest observation, not a full plan upfront.

**Q7. Did the LLM ever make a mistake?**
Yes. In our first run it ignored the stop signal and **made up a fake tool result** (a CSV with wrong numbers) and answered from it. We fixed it by cutting its output at "Observation:" so only real tool output is used. We also saw a weak web-search result in Goal 3, reported as a limitation.

**Q8. How is the calculator safe?**
It uses Python's `ast` module with only allowed operators. It never uses `eval()`, so it cannot run harmful code.

**Q9. How do you know what the agent did? (observability)**
Every step is printed live and saved in `logs/*.jsonl` with timestamps: goal, LLM reply, tool name/input/observation, final answer.

**Q10. What happens if the agent loops forever or picks a wrong tool?**
Step limit of 10; unknown tool or bad format returns an ERROR observation and the LLM corrects itself.

**Q11. Why is the classical agent worse here? When is it better?**
It only works for patterns someone coded in advance, so it failed on open-ended goals. It is better for fixed, safety-critical tasks because it is deterministic, instant and free.

**Q12. How would you improve it?**
Better search API (Tavily/Serper), Google Calendar tool via OAuth, long-term memory with a vector store, automatic evaluation tests, a rule to say "not found" when evidence is missing.

**Q13. Why OpenRouter / why this model?**
Free, OpenAI-compatible, easy model switching with fallback. We needed zero cost for a student project.

**Q14. Who did what?** (decide before the demo; suggestion)
- Person 1: agent design + ReAct loop (`agent.py`)
- Person 2: tools + classical agent (`tools.py`, `classical_agent.py`)
- Person 3: demo, logs, analysis and report

Each member should be able to explain the loop (section 4) and run `python run_demo.py`.

---

## 8. Checklist before the lab
- [ ] New OpenRouter key created, old key deleted
- [ ] `pip install openai pypdf` done
- [ ] `python run_demo.py` runs once successfully on the lab/home machine
- [ ] Report PDF printed or ready (`AI_IA2_Report.pdf`)
- [ ] Everyone has read sections 1, 4 and 7
