"""FOI Request Automation System -- Entry Point

Usage:
    python main.py index               Index policy documents into ChromaDB
    python main.py process <path>      Process FOI request(s) at <path>
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from agents import supervisor
from cost_tracker import CostTracker
from indexer import index_policies

# Load environment variables from .env file
load_dotenv()

# Resolve paths relative to this file, not the working directory
BASE_DIR = Path(__file__).resolve().parent
POLICIES_DIR = BASE_DIR / "documents" / "policies"
OUTPUT_DIR = BASE_DIR / "output"


def run_index():
    """Index policy documents into ChromaDB."""
    print(f"Indexing policies from {POLICIES_DIR}")
    count = index_policies(str(POLICIES_DIR))
    print(f"Indexed {count} chunks")


def run_process(target_path: str):
    """Process one or more FOI request files."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY is not set. Agents will return placeholder output.")
        print("Copy .env.example to .env and add your API key to enable LLM calls.\n")
    from langchain_anthropic import ChatAnthropic
    client = ChatAnthropic(model="claude-sonnet-4-5", api_key=api_key or "placeholder")
    tracker = CostTracker()

    target = Path(target_path)
    if target.is_dir():
        request_files = sorted(target.glob("*.txt"))
    elif target.is_file():
        request_files = [target]
    else:
        print(f"Error: {target_path} is not a valid file or directory")
        sys.exit(1)

    if not request_files:
        print(f"No .txt files found in {target_path}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    results = []

    for request_file in request_files:
        print(f"\nProcessing: {request_file.name}")
        request_text = request_file.read_text()

        result = supervisor(request_text, request_file.name, client, tracker)
        results.append(result)

        # Write individual result file
        output_file = OUTPUT_DIR / f"{request_file.stem}-result.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Result written to {output_file}")

    # Print cost summary
    tracker.print_summary()

    print(f"\nProcessed {len(results)} request(s)")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "index":
        run_index()
    elif command == "process":
        if len(sys.argv) < 3:
            print("Usage: python main.py process <path_to_requests>")
            sys.exit(1)
        run_process(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
