# Research Assistant Agent (AI IA-II, Agentic AI)

ReAct LLM agent (OpenRouter free models) with 4 tools: calculator, document reader, CSV query, web search.

    pip install openai pypdf
    $env:OPENROUTER_API_KEY="your-key"     # PowerShell
    python run_demo.py                      # demo goals on LLM agent + classical agent -> logs/
    python agent.py "your question"         # one goal
    python agent.py                         # interactive chat with short-term memory
    python make_assets.py; python build_report.py   # regenerate figures and report

Files: agent.py, tools.py, classical_agent.py, run_demo.py, docs/ (sample data), logs/ (JSONL traces + transcript), figures/.
