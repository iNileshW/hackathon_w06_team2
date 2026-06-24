"""Document indexing and retrieval using ChromaDB.

Indexes policy documents into a ChromaDB collection for RAG retrieval, via
LangChain's Chroma vector store wrapper.
"""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

COLLECTION_NAME = "foi_policies"

embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(collection_name=COLLECTION_NAME, embedding_function=embedder)


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
        1. Clear out any existing collection: call vectorstore.delete_collection()
           wrapped in a try/except Exception, then reassign the module-level
           `vectorstore` to a fresh
           Chroma(collection_name=COLLECTION_NAME, embedding_function=embedder).
           You'll need `global vectorstore` since you're reassigning it.
        2. Iterate over all .txt files in policies_dir.
        3. For each file, read the text and chunk it with chunk_text(). For each
           chunk, build a langchain_core.documents.Document with
           page_content=chunk and metadata={"file": filename, "chunk_index": i}.
        4. Once you've collected all Documents, call
           vectorstore.add_documents(documents, ids=[...]) with one unique
           string id per chunk (e.g. "policy_0", "policy_1", ...).
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
        Returns an empty list if the collection has no results.

    TODO:
        1. Call vectorstore.similarity_search(query, k=n_results).
        2. Build and return a list of
           {"text": doc.page_content, "source": doc.metadata["file"]}
           for each returned Document.
    """
    return []
