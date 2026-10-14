"""Classical rule-based (simple reflex) agent: fixed keyword -> action rules, no LLM, no memory.
Used only for the Part C comparison against the LLM-driven ReAct agent.
"""
import re
from tools import calculator, list_documents, read_document, csv_query

RULES = [  # (condition on percept, action) - evaluated in fixed order, first match wins
    (lambda q: re.fullmatch(r"[\d\s+\-*/().]+", q.strip()), lambda q: calculator(q)),
    (lambda q: "list" in q.lower() and "document" in q.lower(), lambda q: list_documents()),
    (lambda q: q.lower().startswith("read "), lambda q: read_document(q[5:])),
    (lambda q: q.lower().startswith("csv "), lambda q: csv_query(q[4:])),
]


def classical_agent(percept: str) -> str:
    for cond, act in RULES:
        if cond(percept):
            return act(percept)
    return "NO RULE MATCHED - I don't know how to handle this request."


if __name__ == "__main__":
    import sys
    print(classical_agent(" ".join(sys.argv[1:])))
