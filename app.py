"""FastAPI app: classify a pasted snippet, and serve the evaluation numbers.

Usage: uvicorn app:app --reload    then open http://127.0.0.1:8000
"""
import json
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from llm_classify import classify
from prompt import MODEL

app = FastAPI(title="Leadenhall news event classifier")


class Snippet(BaseModel):
    text: str


@app.post("/api/classify")
def classify_snippet(payload: Snippet):
    """Classify one snippet with the same prompt used for the batch evaluation."""
    text = payload.text.strip()
    if not text:
        return {"error": "empty snippet"}
    try:
        result = classify(text)
    except Exception as e:
        # A missing key or a dead API should surface in the UI, not as a 500.
        return {"error": str(e)}
    result["model"] = MODEL
    return result


class Batch(BaseModel):
    rows: list[dict]


# Cap the batch so a mis-pasted file cannot fire thousands of paid API calls by accident.
MAX_BATCH = 50


@app.post("/api/classify_batch")
def classify_batch(payload: Batch):
    """Classify many snippets at once. The browser parses the CSV and posts rows as JSON,
    which keeps the server free of a file-upload dependency."""
    rows = payload.rows[:MAX_BATCH]
    if not rows:
        return {"error": "no rows found - the CSV needs id and snippet columns"}
    results = []
    for r in rows:
        text = str(r.get("snippet", "")).strip()
        if not text:
            continue
        try:
            out = classify(text)
        except Exception as e:
            return {"error": str(e), "results": results}
        out["id"] = r.get("id", "")
        out["snippet"] = text
        results.append(out)
    return {
        "results": results,
        "truncated": len(payload.rows) > MAX_BATCH,
        "yes": sum(1 for r in results if r["label"] == "YES"),
        "no": sum(1 for r in results if r["label"] == "NO"),
    }


@app.get("/api/metrics")
def metrics():
    """Serve the numbers produced by evaluate.py. Never computed on the fly."""
    if not os.path.exists("metrics.json"):
        return {"error": "run python evaluate.py first"}
    return json.load(open("metrics.json", encoding="utf-8"))


@app.get("/")
def index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
