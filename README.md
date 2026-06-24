# FOI Request Automation -- Starter

## Setup

### Online install

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### Offline install (from vendored wheels)

If pip cannot reach PyPI (proxy block, air-gapped network):

```bash
python -m venv .venv
source .venv/bin/activate
make install-offline
cp .env.example .env
```

**Offline install:** Run `./fetch-vendor.sh` first to populate `vendor/wheels/`, then run `make install-offline`. The script must be run on a machine with internet access before the hackathon session begins.

The `vendor/wheels/` directory contains pre-built wheels for all dependencies. If it is missing or incomplete, ask the facilitator for the vendor archive.

### Smoke test

Run `make smoke` before the hackathon begins. It verifies that chromadb and sentence-transformers import correctly and warns if `OPENAI_API_KEY` is unset (the key is only needed for the OpenAI embedding fallback).

```bash
make smoke
```

If smoke fails, work through the troubleshooting steps below before raising a ticket.

## Usage

Index policy documents (run once before processing):

```bash
python main.py index
```

Process all FOI requests in the sample directory:

```bash
python main.py process documents/foi_requests/
```

Process a single request file:

```bash
python main.py process documents/foi_requests/request-001.txt
```

## What to build

The scaffold runs out of the box but produces placeholder output. Implement the agent functions in `agents.py`, the RAG indexing/search in `indexer.py`, and complete the cost tracking in `cost_tracker.py`. See the lab README for acceptance criteria.

## HuggingFace-blocked troubleshooting

If `sentence-transformers` fails to download the embedding model (403, timeout, or `HfHubHTTPError`), the HuggingFace Hub is blocked on your network. Set the fallback provider:

1. Edit `.env` and set `EMBEDDING_PROVIDER=openai`
2. Ensure `OPENAI_API_KEY` is set to a valid key
3. Re-run `make smoke`

With `EMBEDDING_PROVIDER=openai`, ChromaDB uses the OpenAI embeddings API instead of the local sentence-transformers model. This requires network access to `api.openai.com` and consumes API credits.

Do not set `HF_HUB_DISABLE_SSL_VERIFY=1` or bypass TLS verification. If both HuggingFace and OpenAI are blocked, contact your instructor before the session.
