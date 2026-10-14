"""Tools available to the Research Assistant Agent."""
import ast, csv, json, operator, os, re, urllib.parse, urllib.request

DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

# ---------- Tool 1: calculator (safe AST evaluator, no eval()) ----------
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv, ast.USub: operator.neg, ast.UAdd: operator.pos}


def _ev(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
        return n.value
    if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
        return _OPS[type(n.op)](_ev(n.left), _ev(n.right))
    if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
        return _OPS[type(n.op)](_ev(n.operand))
    raise ValueError("unsupported expression")


def calculator(expression: str) -> str:
    try:
        return str(round(_ev(ast.parse(expression.strip(), mode="eval").body), 6))
    except Exception as e:
        return f"ERROR: {e}"


# ---------- Tool 2: document reader / lister ----------
def list_documents(_: str = "") -> str:
    return ", ".join(sorted(os.listdir(DOCS_DIR))) or "(no documents)"


def read_document(filename: str, max_chars: int = 4000) -> str:
    path = os.path.join(DOCS_DIR, os.path.basename(filename.strip()))
    if not os.path.isfile(path):
        return f"ERROR: '{filename}' not found. Available: {list_documents()}"
    if path.lower().endswith(".pdf"):
        from pypdf import PdfReader
        text = "\n".join(p.extract_text() or "" for p in PdfReader(path).pages)
    else:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    return text[:max_chars] + ("\n...[truncated]" if len(text) > max_chars else "")


# ---------- Tool 3: CSV query (simple database) ----------
def csv_query(args: str) -> str:
    """'file.csv' -> preview rows; 'file.csv | column' -> count/sum/mean/min/max of a numeric column."""
    parts = [p.strip() for p in args.split("|")]
    path = os.path.join(DOCS_DIR, os.path.basename(parts[0]))
    if not os.path.isfile(path):
        return f"ERROR: '{parts[0]}' not found."
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(parts) == 1:
        return f"columns={list(rows[0].keys())}\n" + "\n".join(json.dumps(r) for r in rows[:25])
    col = parts[1]
    try:
        v = [float(r[col]) for r in rows]
    except Exception:
        return f"ERROR: column '{col}' missing or not numeric. Columns: {list(rows[0].keys())}"
    return json.dumps({"count": len(v), "sum": sum(v), "mean": round(sum(v) / len(v), 3),
                       "min": min(v), "max": max(v)})


# ---------- Tool 4: web search (Wikipedia search API; no key needed) ----------
def web_search(query: str) -> str:
    q = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": query,
                                "srlimit": 3, "format": "json"})
    req = urllib.request.Request("https://en.wikipedia.org/w/api.php?" + q,
                                 headers={"User-Agent": "ResearchAgent/1.0 (student project)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            hits = json.load(r)["query"]["search"]
    except Exception as e:
        return f"ERROR: search failed ({e})"
    if not hits:
        return "No results."
    lines = [f"- {h['title']}: {re.sub('<[^>]+>', '', h['snippet'])}" for h in hits]
    try:  # add the intro paragraph of the top hit for a usable definition
        q2 = urllib.parse.urlencode({"action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1,
                                     "titles": hits[0]["title"], "format": "json"})
        req2 = urllib.request.Request("https://en.wikipedia.org/w/api.php?" + q2,
                                      headers={"User-Agent": "ResearchAgent/1.0 (student project)"})
        with urllib.request.urlopen(req2, timeout=15) as r:
            page = next(iter(json.load(r)["query"]["pages"].values()))
        lines.insert(0, f"TOP RESULT INTRO ({hits[0]['title']}): {page.get('extract', '')[:500]}")
    except Exception:
        pass
    return "\n".join(lines)


TOOLS = {
    "calculator": (calculator, "Evaluate an arithmetic expression, e.g. '(120*0.18)+5'. Input: expression string."),
    "list_documents": (list_documents, "List files in the local knowledge folder. Input: empty string."),
    "read_document": (read_document, "Read a .txt/.pdf document. Input: filename."),
    "csv_query": (csv_query, "Query a CSV. Input: 'file.csv' (preview rows) or 'file.csv | column' (count/sum/mean/min/max)."),
    "web_search": (web_search, "Search Wikipedia for general facts. Input: search query."),
}
