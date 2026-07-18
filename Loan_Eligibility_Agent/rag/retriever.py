# rag/retriever.py
# Task 2.3 — Retrieval Chain: query RBI documents using natural language

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
import os

load_dotenv()


def get_retriever(vector_store, k: int = 4):
    """
    Creates a retriever from the vector store.
    k=4 means we fetch the top 4 most relevant chunks for each query.
    More chunks = more context but also more noise — 4 is a good balance
    for focused regulatory documents like RBI guidelines.
    """
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )


def format_retrieved_docs(docs):
    """
    Joins retrieved chunks into a single string for the LLM prompt.
    Also preserves source metadata so we can show citations in the UI.
    """
    formatted = []
    for i, doc in enumerate(docs):
        source = doc.metadata.get("source_file", "Unknown")
        page = doc.metadata.get("page", "N/A")
        formatted.append(
            f"[Source {i+1}: {source}, Page {page}]\n{doc.page_content}"
        )
    return "\n\n---\n\n".join(formatted)


def build_rag_chain(retriever, llm):
    """
    Builds the full RAG chain:
    1. User query → retriever fetches relevant chunks
    2. Chunks + query → prompt → LLM
    3. LLM generates answer grounded in retrieved content

    This is the core pattern your RAG Agent will use in Week 4.
    """
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert RBI regulatory advisor for an Indian bank.
            Answer questions about loan eligibility, CIBIL scores, FOIR limits,
            and lending practices ONLY based on the provided context.

            If the answer is not found in the context, say:
            "This information is not available in the current RBI guidelines provided."

            Always cite the source document when giving an answer.

            Context from RBI Guidelines:
            {context}"""
        ),
        (
            "human",
            "{question}"
        )
    ])

    # Full RAG chain:
    # - RunnablePassthrough() passes the question through unchanged to the prompt
    # - retriever fetches relevant chunks, format_retrieved_docs formats them
    # - prompt fills in context + question, llm generates answer
    rag_chain = (
        {
            "context": retriever | format_retrieved_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def retrieve_with_sources(retriever, query: str):
    """
    Returns both the answer AND the source documents used.
    Your RAG Agent will use this so it can show which RBI guidelines
    backed its response — important for compliance and explainability.
    """
    docs = retriever.invoke(query)
    sources = []
    for doc in docs:
        sources.append({
            "source_file": doc.metadata.get("source_file", "Unknown"),
            "page": doc.metadata.get("page", "N/A"),
            "content_preview": doc.page_content[:200] + "..."
        })
    return docs, sources


if __name__ == "__main__":
    from rag.embeddings import load_vector_store
    from llm_config import get_llm

    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from llm_config import get_llm

    print("\n🔍 RAG Retrieval Chain — Test Queries")
    print("Loading vector store and LLM...\n")

    # Load existing vector store (already built in Task 2.2)
    vector_store = load_vector_store()
    retriever = get_retriever(vector_store)
    llm = get_llm()
    rag_chain = build_rag_chain(retriever, llm)

    # Test queries — these simulate what your agents will ask
    test_queries = [
        "What is the minimum CIBIL score required for a home loan?",
        "What is FOIR and what are the RBI recommended limits?",
        "What should a bank do when rejecting a loan application?",
        "What counter-offer options should a bank provide if a loan is rejected?"
    ]

    for query in test_queries:
        print("=" * 60)
        print(f"Query: {query}")
        print("-" * 60)

        # Get answer
        answer = rag_chain.invoke(query)
        print(f"Answer:\n{answer}")

        # Show sources
        _, sources = retrieve_with_sources(retriever, query)
        print(f"\nSources used:")
        for s in sources:
            print(f"  → {s['source_file']} (Page {s['page']})")

        print()

    print("✅ RAG chain working correctly! Ready for Week 3 — MCP Tools\n")