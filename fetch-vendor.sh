#!/usr/bin/env bash
# fetch-vendor.sh — FB-X-001-W6 vendored-wheel + model fetch script
# Downloads platform-specific wheels and the sentence-transformers model
# so W06 hackathon runs without live internet during the session.
#
# Run this BEFORE Day 1 on a machine with internet access.
# The fetched artifacts are cached in vendor/ and vendor/models/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENDOR_DIR="${SCRIPT_DIR}/vendor"
WHEELS_DIR="${VENDOR_DIR}/wheels"
MODELS_DIR="${VENDOR_DIR}/models"

PYTHON="${PYTHON:-python3}"
PIP="${PIP:-pip3}"

MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"
MODEL_DIR="${MODELS_DIR}/all-MiniLM-L6-v2"

echo "=== W06 Vendor Fetch ==="
echo ""

# --- Step 1: Create directories ---
mkdir -p "${WHEELS_DIR}" "${MODELS_DIR}"

# --- Step 2: Download Python wheels ---
echo "--- Downloading Python wheels ---"
${PIP} download \
  --dest "${WHEELS_DIR}" \
  --no-deps \
  "openai>=1.0.0" \
  "chromadb>=1.0.0" \
  "python-dotenv>=1.0.0" \
  "sentence-transformers>=2.0.0" \
  "onnxruntime>=1.16.0" \
  2>&1 | tail -5

echo "  Wheels cached in ${WHEELS_DIR}"
echo ""

# --- Step 3: Download sentence-transformers model ---
echo "--- Downloading embedding model: ${MODEL_NAME} ---"
${PYTHON} -c "
from sentence_transformers import SentenceTransformer
import os
model = SentenceTransformer('${MODEL_NAME}')
cache_dir = os.path.expanduser('~/.cache/torch/sentence_transformers')
print(f'  Model cached at: {cache_dir}')
# Also save a local copy for offline use
model.save('${MODEL_DIR}')
print(f'  Model saved to: ${MODEL_DIR}')
"

echo ""

# --- Step 4: Verify ---
echo "--- Verifying vendor cache ---"
wheel_count=$(find "${WHEELS_DIR}" -name "*.whl" | wc -l)
echo "  Wheels: ${wheel_count} .whl files"

if [[ -d "${MODEL_DIR}" ]] && [[ -f "${MODEL_DIR}/config.json" ]]; then
  echo "  Model: all-MiniLM-L6-v2 present"
else
  echo "  WARN: Model directory missing or incomplete"
fi

echo ""
echo "=== Vendor fetch complete ==="
echo ""
echo "To install from vendored wheels (offline):"
echo "  pip install --no-index --find-links ${WHEELS_DIR} -r requirements.txt"
echo ""
echo "To use the vendored model (offline):"
echo "  export SENTENCE_TRANSFORMERS_HOME=${MODELS_DIR}"
echo ""

# --- Personal laptop note ---
cat <<'ASIDE'
Note for personal laptops / post-programme use:
  If you are behind a corporate proxy, set HTTPS_PROXY before running
  this script. If HuggingFace Hub is blocked, set EMBEDDING_PROVIDER=openai
  in your .env file and skip the model download (Steps 3-4).
ASIDE
