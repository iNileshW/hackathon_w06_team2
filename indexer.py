"""Document indexing and retrieval using ChromaDB.

Indexes policy documents into a ChromaDB collection for RAG retrieval.
"""

from pathlib import Path
import chromadb

db = chromadb.Client()

COLLECTION_NAME = "foi_policies"


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list:
    """Split text into overlapping chunks.

    Args:
        text: The full document text.
        chunk_size: Maximum characters per chunk.
        overlap: Number of characters to overlap between consecutive chunks.

    Returns:
        A list of text chunks.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [c for c in chunks if c.strip()]


def index_policies(policies_dir: str) -> int:
    """Index all .txt files in the policies directory into ChromaDB.

    Args:
        policies_dir: Path to the directory containing policy text files.

    Returns:
        The number of chunks indexed.

    TODO:
        1. Delete the existing collection if it exists (use db.delete_collection
           wrapped in a try/except Exception).
        2. Create a new collection named COLLECTION_NAME.
        3. Iterate over all .txt files in policies_dir.
        4. For each file, read the text, chunk it with chunk_text(), and add
           each chunk to the collection. Include metadata: {"file": filename, "chunk_index": i}.
        5. Return the total number of chunks indexed.
    """
    return 0


def search_policies(query: str, n_results: int = 3) -> list:
    """Search the policy collection for chunks relevant to the query.

    Args:
        query: The search query text.
        n_results: Number of results to return.

    Returns:
        A list of dictionaries with keys "text" and "source".
        Returns an empty list if the collection does not exist or has no results.

    TODO:
        1. Get the collection (handle Exception if it does not exist).
        2. Query with query_texts=[query] and n_results.
        3. Build and return a list of {"text": chunk_text, "source": filename}.
    """
    return []
