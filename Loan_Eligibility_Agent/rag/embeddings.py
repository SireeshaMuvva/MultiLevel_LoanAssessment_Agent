# rag/embeddings.py
# Task 2.2 — Build and persist the vector store using ChromaDB

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os

load_dotenv()

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
COLLECTION_NAME = "rbi_guidelines"


def get_embedding_model():
    """
    Returns the embedding model used to convert text chunks into vectors.
    text-embedding-3-small is cost-effective and performs well for this use case.
    """
    return OpenAIEmbeddings(
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=os.getenv("OPENAI_API_KEY")
    )


def build_vector_store(chunks):
    """
    Takes document chunks, generates embeddings, and stores them in ChromaDB.
    This persists to disk so you don't need to re-embed every time you run the app.
    """
    embeddings = get_embedding_model()

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIR
    )

    print(f"✅ Vector store created and persisted to: {PERSIST_DIR}")
    print(f"   Total vectors stored: {len(chunks)}")

    return vector_store


def load_vector_store():
    """
    Loads an existing vector store from disk — use this in your agents
    instead of rebuilding embeddings every time (saves API costs).
    """
    embeddings = get_embedding_model()

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR
    )

    return vector_store


if __name__ == "__main__":
    # Build the vector store from scratch
    try:
        from loader import load_pdf_documents, chunk_documents
    except ImportError:
        from rag.loader import load_pdf_documents, chunk_documents

    DOCS_DIR = "data/documents/rbi_guidelines"

    print("\n📄 Loading and chunking documents...")
    docs = load_pdf_documents(DOCS_DIR)
    chunks = chunk_documents(docs)
    print(f"✅ {len(chunks)} chunks ready for embedding")

    print("\n🔢 Generating embeddings and building vector store...")
    print("   (This calls OpenAI's embedding API - small cost, a few cents)")
    vector_store = build_vector_store(chunks)

    print("\n✅ Vector store build complete! Ready for Task 2.3 - Retrieval Chain")