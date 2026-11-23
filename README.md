# JevAI

> Most AI work in an app is a decision, not an essay.

A small Flask demo of a **two-tier AI architecture**: a fast, cheap *decision layer* (TypeSafe's Jev, via [`langchain-typesafe`](https://pypi.org/project/langchain-typesafe/)) triages every request, and a frontier LLM (Claude, via LangChain) is only called when language or reasoning is actually needed.

It accompanies the essay [Most AI work is a decision, not an essay](https://www.linkedin.com/pulse/most-ai-work-decision-essay-jamel-de-la-fuente-gwjhe/).

## The idea

An LLM produces tokens: text, code, media. A decision model like Jev returns a **typed decision** with a confidence: it holds up a card instead of telling a story. Three kinds of cards:

| Card | Example | Output |
| --- | --- | --- |
| Yes / No | "Is this email spam?" | Yes, 92% sure |
| Pick one | "Cat, dog or bird?" | Dog, 75% sure |
| A number from 0 to 1 | "How happy is this customer?" | 0.3 |

Because decisions are typed, they are easy to route on and easy to test. Because they are fast and cheap, you can make them everywhere: before every LLM call, on every tool call, on every log line.

### Worked example: the customer mailbox

A company receives a flood of customer letters. A "helper" reads each one and asks a single question: **easy or tricky?**

- **Easy** ("How do I reset my password?") → `AutoResponse`: the frontier LLM writes a reply immediately.
- **Tricky** ("I was charged twice and I'm upset") → `Support`: no LLM answer; it goes to a human (Teams, Slack, wherever they work).

Sorting is cheap and fast, writing a careful answer is not, so the LLM is only used where language is needed.

## The architecture ladder

The essay walks through four levels of building this. It recommends choosing the lowest level that serves your purpose, and not defaulting to level 4. The same department classifier sits at the front of every level.

| Level | What it adds on the `AutoResponse` side | In this repo |
| --- | --- | --- |
| 1. RAG | Look the ticket up in a knowledge base and ground the single LLM call in the matching chunks | Triage + single LLM call (`/classify`); retrieval is not implemented |
| 2. Skills | A second, finer decision picks a skill template (billing, password reset, refund), each with its own prompt and context | Not implemented |
| 3. Agentic | The model loops with tools; a guardrail classifies each tool call as safe or risky before it runs | `/agent` |
| 4. Harness | Queues, per-ticket state, a human-approval queue and an eval loop for production volume | Not implemented |

## What's in this repo

| Route | Description |
| --- | --- |
| `GET /` | Hello world |
| `GET /ui` | Simple chat frontend for `/classify` |
| `POST /chat` | `{"prompt": "..."}` → `{"response": "..."}`. A plain Claude call with no decision layer, as the baseline |
| `POST /classify` | `{"state": "..."}` → `{"department": "AutoResponse" \| "Support"}`. `AutoResponse` tickets also get a Claude `response`; `Support` tickets are only routed |
| `POST /agent` | `{"task": "..."}` runs a small agent with `read_file` / `delete_file` tools over an in-memory file store. `AutoModeMiddleware` classifies each `delete_file` call as risky (writes, deletes, publishes, changes access) or safe (reads only) before it runs |

Try it:

```
curl -X POST localhost:5000/classify -H 'Content-Type: application/json' \
  -d '{"state": "How do I reset my password?"}'

curl -X POST localhost:5000/classify -H 'Content-Type: application/json' \
  -d '{"state": "I was charged twice and I am really upset, please fix it."}'
```

## Setup

Requires Python 3.10+ (for `langchain-typesafe`).

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your keys
python app.py
```

Visit http://127.0.0.1:5000/ui

`.env` is loaded automatically (via `python-dotenv`) and is gitignored. Never commit it.

Optional environment variables:

- `ANTHROPIC_MODEL`: model ID to use (default `claude-opus-5-5`)
- `FLASK_DEBUG=1`: enable Flask debug mode (off by default; do not use in production)

## Why a two-tier system

1. **Most AI work in an app is a decision.** Agents spend much of their time on small calls: which tool, is this document relevant, how urgent is this ticket, should we escalate. A decision model answers these directly, and the LLM is reserved for language.
2. **AI can sit where it couldn't before.** When a decision costs a fraction of a cent and takes milliseconds, it can run on every transaction, log line or sensor reading without becoming a bottleneck.
3. **The architecture of AI apps changes.** A fast decision layer handles high-volume triage and routing; a frontier LLM is called only for reasoning or writing. This cuts cost and latency together, and typed outputs make the system testable.

## Caveat on numbers

Pricing and speed figures for Jev (for example, roughly 70 to 500 ms responses and large cost reductions versus frontier LLMs) are TypeSafe's own launch claims as reported in the essay, with the best cases at the upper end of real-world gains. They are not measured by this repo. Check current pricing and benchmark on your own workload.

## Alternatives

Jev is not the only decision model: Microsoft has released Microsoft-Decision-1, and there are open-source options. See DataCamp's [Top 7 Open-Source TypeSafe Jev Alternatives](https://www.datacamp.com/blog/top-open-source-jev-alternatives).

## License

MIT. See [LICENSE](LICENSE).
