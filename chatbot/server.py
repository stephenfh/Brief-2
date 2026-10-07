"""Chatbot backend: Flask + tool-calling agent over an OpenAI-compatible API.

Run: python chatbot/server.py
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from openai import OpenAI

import agent
import loader

load_dotenv(Path(__file__).parent / ".env")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-nano")
# Reads OPENAI_API_KEY (and optionally OPENAI_BASE_URL) from the environment.
client = OpenAI(base_url=os.environ.get("OPENAI_BASE_URL") or None, max_retries=4)
app = Flask(__name__, static_folder="static")


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/roles")
def roles():
    return jsonify([{"id": k, "label": v} for k, v in loader.ROLE_LABELS.items()])


@app.post("/api/chat")
def chat():
    data = request.get_json(force=True)
    role = data.get("role")
    if role not in loader.ROLE_LABELS:
        return jsonify({"error": "unknown role"}), 400
    history = [{"role": m["role"], "content": m["content"]}
               for m in data.get("messages", []) if m.get("role") in ("user", "assistant")]
    try:
        answer, steps, case_view = agent.run(client, MODEL, role, history)
    except Exception as e:  # surface API errors to the UI without leaking the key
        return jsonify({"error": f"{type(e).__name__}: {str(e)[:300]}"}), 502
    return jsonify({"answer": answer, "case_view": case_view, "steps": steps, "model": MODEL})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
