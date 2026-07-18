# rag/loader.py
# Task 2.2 — Load and chunk RBI guideline PDFs

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os


def load_pdf_documents(directory: str):
    """
    Loads all PDFs from a directory and returns a list of Document objects.
    Each PDF page becomes a separate Document with metadata (source filename, page number).
    """
    all_documents = []

    pdf_files = [f for f in os.listdir(directory) if f.endswith(".pdf")]

    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {directory}")

    for pdf_file in pdf_files:
        filepath = os.path.join(directory, pdf_file)
        loader = PyPDFLoader(filepath)
        documents = loader.load()

        # Tag each document with a clean source name for citations later
        for doc in documents:
            doc.metadata["source_file"] = pdf_file

        all_documents.extend(documents)
        print(f"   Loaded: {pdf_file} ({len(documents)} pages)")

    return all_documents


def chunk_documents(documents, chunk_size: int = 800, chunk_overlap: int = 150):
    """
    Splits documents into smaller chunks for embedding.

    chunk_size=800: roughly 150-200 words per chunk — small enough for precise
                    retrieval, large enough to keep context coherent.
    chunk_overlap=150: chunks overlap by 150 characters so we don't lose context
                        at chunk boundaries (e.g. a sentence split across two chunks).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]  # tries paragraph breaks first, then sentences
    )

    chunks = splitter.split_documents(documents)
    return chunks


if __name__ == "__main__":
    # Quick test — run this file directly to verify loading works
    DOCS_DIR = "data/documents/rbi_guidelines"

    print("\n📄 Loading RBI guideline PDFs...")
    docs = load_pdf_documents(DOCS_DIR)
    print(f"\n✅ Total pages loaded: {len(docs)}")

    print("\n✂️  Chunking documents...")
    chunks = chunk_documents(docs)
    print(f"✅ Total chunks created: {len(chunks)}")

    print("\n--- Sample Chunk ---")
    print(f"Source: {chunks[0].metadata.get('source_file')}")
    print(f"Page: {chunks[0].metadata.get('page')}")
    print(f"Content preview:\n{chunks[0].page_content[:300]}...")