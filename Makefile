.PHONY: smoke install-offline install-online

install-online:
	pip install -r requirements.txt

install-offline:
	pip install --no-index --find-links vendor/wheels -r requirements.txt

smoke:
	@echo "Running W06H smoke test..."
	python -c "import chromadb; print('chromadb OK')"
	python -c "from sentence_transformers import SentenceTransformer; print('sentence-transformers OK')"
	@if [ -z "$$OPENAI_API_KEY" ]; then echo "WARNING: OPENAI_API_KEY not set (fallback embedding unavailable)"; fi
	@echo "Smoke test passed."
