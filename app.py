"""JevAI: a small Flask demo of LangChain + langchain-typesafe routing and agent gating."""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_typesafe import Choice, NoulCriteria, TypeSafeClassifier
from langchain_typesafe.experimental.middleware import AutoModeMiddleware

load_dotenv()

app = Flask(__name__)
llm = ChatAnthropic(model=os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5"))
classifier = TypeSafeClassifier()

# In-memory store so the agent's delete tool has no real filesystem access.
_files = {"notes.txt": "Baseline app notes."}


@tool
def read_file(path: str) -> str:
    """Read the contents of a file."""
    return _files.get(path, f"{path} not found")


@tool
def delete_file(path: str) -> str:
    """Delete a file."""
    if path in _files:
        del _files[path]
        return f"Deleted {path}"
    return f"{path} not found"


auto_mode = AutoModeMiddleware(
    tools=[delete_file],
    criteria=NoulCriteria(
        true="The call writes, deletes, publishes, or changes access.",
        false="The call only reads public or user-provided data.",
    ),
)

agent = create_agent(llm, tools=[read_file, delete_file], middleware=[auto_mode])


@app.route("/")
def index():
    return {"message": "Hello, world!"}


@app.route("/ui")
def ui():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "prompt is required"}), 400

    response = llm.invoke(prompt)
    return jsonify({"response": response.text})


@app.route("/classify", methods=["POST"])
def classify():
    data = request.get_json(silent=True) or {}
    state = data.get("state")
    if not state:
        return jsonify({"error": "state is required"}), 400

    result = classifier.invoke(
        {
            "state": state,
            "questions": {
                "department": Choice(
                    instructions="Which team should handle this?",
                    criteria={
                        "AutoResponse": "FAQ Ingested type questions",
                        "Support": "Complex questions where person needs to verify or assist",
                    },
                ),
            },
        }
    )
    department = result.choices["department"].choice
    if department == "AutoResponse":
        response = llm.invoke(state)
        return jsonify({"department": department, "response": response.text})
    else:
        return jsonify({"department": department})


@app.route("/agent", methods=["POST"])
def run_agent():
    data = request.get_json(silent=True) or {}
    task = data.get("task")
    if not task:
        return jsonify({"error": "task is required"}), 400

    result = agent.invoke({"messages": [{"role": "user", "content": task}]})
    last_message = result["messages"][-1]
    return jsonify({"response": last_message.text})


if __name__ == "__main__":
    # Debug mode exposes an interactive debugger; opt in explicitly via FLASK_DEBUG=1.
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
