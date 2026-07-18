# evaluation/ragas_eval.py
# Task 6.1 — RAGAS Evaluation
# Evaluates the RAG pipeline quality using 3 key metrics:
#
# 1. Faithfulness    — Does the answer stick to retrieved context?
#                      (prevents hallucination)
# 2. Answer Relevancy — Is the answer relevant to the question asked?
#                      (prevents off-topic responses)
# 3. Context Precision — Are the retrieved chunks actually useful?
#                      (evaluates retrieval quality)
#
# Run: uv run python3 -m evaluation.ragas_eval

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from dotenv import load_dotenv
load_dotenv()

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from rag.embeddings import load_vector_store
from rag.retriever import get_retriever, build_rag_chain, retrieve_with_sources
from llm_config import get_llm


def load_test_dataset(filepath: str) -> list:
    """Loads the Q&A test dataset."""
    with open(filepath, "r") as f:
        return json.load(f)


def build_ragas_dataset(test_data: list, retriever, rag_chain) -> Dataset:
    """
    Runs each question through the RAG pipeline and builds
    the dataset structure RAGAS expects for evaluation.

    RAGAS needs 4 columns:
    - question      : the input question
    - answer        : what the RAG pipeline answered
    - contexts      : the retrieved chunks used to answer
    - ground_truth  : the correct expected answer
    """
    questions = []
    answers = []
    contexts = []
    ground_truths = []

    total = len(test_data)

    for i, item in enumerate(test_data):
        question = item["question"]
        ground_truth = item["ground_truth"]

        print(f"   [{i+1}/{total}] {question[:60]}...")

        try:
            # Get RAG answer
            answer = rag_chain.invoke(question)

            # Get retrieved context chunks
            docs, _ = retrieve_with_sources(retriever, question)
            context_texts = [doc.page_content for doc in docs]

            questions.append(question)
            answers.append(answer)
            contexts.append(context_texts)
            ground_truths.append(ground_truth)

        except Exception as e:
            print(f"   ⚠️  Skipping question {i+1} due to error: {e}")
            continue

    return Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    })


def run_ragas_evaluation():
    """
    Full RAGAS evaluation pipeline:
    1. Load test dataset
    2. Run each question through RAG pipeline
    3. Evaluate with RAGAS metrics
    4. Print and save results
    """
    print("\n" + "="*60)
    print("📊 RAGAS EVALUATION — Loan Eligibility RAG Pipeline")
    print("="*60)

    # ── Step 1: Load components ────────────────────────────────────────────
    print("\n⚙️  Loading RAG pipeline components...")
    vector_store = load_vector_store()
    retriever = get_retriever(vector_store, k=4)
    llm = get_llm()
    rag_chain = build_rag_chain(retriever, llm)
    print("✅ RAG pipeline loaded")

    # ── Step 2: Load test dataset ──────────────────────────────────────────
    dataset_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "test_dataset.json"
    )
    test_data = load_test_dataset(dataset_path)
    print(f"✅ Test dataset loaded: {len(test_data)} questions")

    # ── Step 3: Run all questions through RAG pipeline ─────────────────────
    print(f"\n🔍 Running {len(test_data)} questions through RAG pipeline...")
    print("   (This will make LLM API calls — may take 2-3 minutes)\n")

    ragas_dataset = build_ragas_dataset(test_data, retriever, rag_chain)
    print(f"\n✅ Dataset built: {len(ragas_dataset)} valid Q&A pairs")

    # ── Step 4: Run RAGAS evaluation ──────────────────────────────────────
    print("\n📏 Running RAGAS metrics evaluation...")
    print("   Metrics: Faithfulness, Answer Relevancy, Context Precision\n")

    # RAGAS uses its own LLM and embeddings for evaluation
    # We use the same OpenAI models we've been using throughout
    result = evaluate(
        dataset=ragas_dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision
        ],
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
        embeddings=OpenAIEmbeddings(model="text-embedding-3-small")
    )

    # ── Step 5: Print results ──────────────────────────────────────────────
    print("\n" + "="*60)
    print("📊 RAGAS EVALUATION RESULTS")
    print("="*60)

    try:
        df = result.to_pandas()
    except AttributeError:
        import pandas as pd
        df = pd.DataFrame(result.scores)

    scores = {
    "faithfulness": round(df["faithfulness"].mean(), 4),
    "answer_relevancy": round(df["answer_relevancy"].mean(), 4),
    "context_precision": round(df["context_precision"].mean(), 4)
}

    print(f"\n  Faithfulness      : {scores['faithfulness']:.4f}  "
          f"{'✅ Good' if scores['faithfulness'] >= 0.7 else '⚠️  Needs improvement'}")
    print(f"  Answer Relevancy  : {scores['answer_relevancy']:.4f}  "
          f"{'✅ Good' if scores['answer_relevancy'] >= 0.7 else '⚠️  Needs improvement'}")
    print(f"  Context Precision : {scores['context_precision']:.4f}  "
          f"{'✅ Good' if scores['context_precision'] >= 0.7 else '⚠️  Needs improvement'}")

    overall = sum(scores.values()) / len(scores)
    print(f"\n  Overall Score     : {overall:.4f}  "
          f"{'✅ Good' if overall >= 0.7 else '⚠️  Needs improvement'}")

    print("\n" + "="*60)
    print("📖 METRIC EXPLANATIONS (for interview)")
    print("="*60)
    print("""
  Faithfulness (%.4f):
    Measures whether every claim in the answer is supported
    by the retrieved context. Score = 1.0 means no hallucination.
    Score < 0.7 means the LLM is adding information not in the docs.

  Answer Relevancy (%.4f):
    Measures whether the answer actually addresses the question.
    Score = 1.0 means perfectly on-topic.
    Score < 0.7 means answers are drifting off-topic.

  Context Precision (%.4f):
    Measures whether the retrieved chunks were actually useful
    for answering the question. Score = 1.0 means all retrieved
    chunks were relevant. Score < 0.7 means retrieval is noisy.
    """ % (
        scores['faithfulness'],
        scores['answer_relevancy'],
        scores['context_precision']
    ))

    # ── Step 6: Save results to file ───────────────────────────────────────
    results_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "ragas_results.json"
    )

    with open(results_path, "w") as f:
        json.dump({
            "scores": scores,
            "overall": round(overall, 4),
            "total_questions": len(test_data),
            "evaluated_questions": len(ragas_dataset)
        }, f, indent=2)

    print(f"\n✅ Results saved to: evaluation/ragas_results.json")
    print("\n✅ RAGAS evaluation complete! Ready for Task 6.2 — LangSmith\n")

    return scores


if __name__ == "__main__":
    run_ragas_evaluation()