"""Document indexing and retrieval using ChromaDB.

Indexes policy documents into a ChromaDB collection for RAG retrieval, via
LangChain's Chroma vector store wrapper.
"""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

COLLECTION_NAME = "foi_policies"
# Persist on disk so `index` and `process` (separate processes) share the store.
PERSIST_DIR = str(Path(__file__).resolve().parent / "chroma_db")

embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embedder,
    persist_directory=PERSIST_DIR,
)


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

    """
    global vectorstore
    # Start from a clean collection so re-indexing never double-counts chunks.
    try:
        vectorstore.delete_collection()
    except Exception as exc:
        print(f"  [index] no existing collection to clear: {exc}")
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedder,
        persist_directory=PERSIST_DIR,
    )

    documents = []
    ids = []
    for path in sorted(Path(policies_dir).glob("*.txt")):
        filename = path.name
        for i, chunk in enumerate(chunk_text(path.read_text())):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={"file": filename, "chunk_index": i},
                )
            )
            ids.append(f"{filename}-{i}")

    if documents:
        vectorstore.add_documents(documents, ids=ids)
    return len(documents)


def search_policies(query: str, n_results: int = 3) -> list:
    """Search the policy collection for chunks relevant to the query.

    Args:
        query: The search query text.
        n_results: Number of results to return.

    Returns:
        A list of dictionaries with keys "text" and "source".
        Returns an empty list if the collection has no results.

    """
    try:
        docs = vectorstore.similarity_search(query, k=n_results)
    except Exception as exc:
        print(f"  [search] retrieval failed: {exc}")
        return []
    return [
        {"text": doc.page_content, "source": doc.metadata.get("file", "unknown")}
        for doc in docs
    ]
