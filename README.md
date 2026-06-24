# FOI Request Automation -- Starter

## Setup

### Online install

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your Anthropic API key
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

Run `make smoke` before the hackathon begins. It verifies that chromadb and sentence-transformers import correctly and warns if `ANTHROPIC_API_KEY` is unset.

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

If `sentence-transformers` fails to download the embedding model (403, timeout, or `HfHubHTTPError`), the HuggingFace Hub is blocked on your network.

**Note:** this section previously described an `EMBEDDING_PROVIDER=openai` fallback. That no longer applies now that the lab runs on an Anthropic key -- Anthropic has no public embeddings API to fall back to. If you hit this, contact your instructor before the session; do not set `HF_HUB_DISABLE_SSL_VERIFY=1` or bypass TLS verification.
