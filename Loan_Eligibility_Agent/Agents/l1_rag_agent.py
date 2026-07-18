# agents/l1_rag_agent.py
# L1 Agent 2 — RAG Agent
# Retrieves relevant RBI guidelines for the loan type requested.
# Downstream agents (Decision, Compliance) will use these guidelines
# to make grounded, regulation-backed decisions.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.state import LoanApplicationState
from mcp_server.tools import get_rbi_guidelines
from llm_config import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def rag_agent(state: LoanApplicationState) -> LoanApplicationState:
    """
    L1 RAG Agent.

    Responsibilities:
    1. Check if validation passed — skip if not
    2. Call get_rbi_guidelines() tool to retrieve relevant RBI policy
    3. Summarise the guidelines into a focused, agent-friendly format
       so downstream agents don't need to read the full policy text

    Reads from state:
    - validation_passed
    - loan_type_requested
    - employment_type

    Writes to state:
    - rbi_guidelines (summarised policy text)
    - rbi_sources (source document citations)
    """
    print("\n[L1 RAG Agent] Running...")

    # ── Skip if validation failed ──────────────────────────────────────────
    if not state.get("validation_passed"):
        print("[L1 RAG Agent] ⏭️  Skipping — validation did not pass")
        return {
            **state,
            "rbi_guidelines": "Skipped — validation failed",
            "rbi_sources": [],
            "current_agent": "l1_rag_agent"
        }

    loan_type = state["loan_type_requested"]
    employment_type = state["employment_type"]

    # ── Step 1: Retrieve RBI guidelines via RAG tool ───────────────────────
    print(f"[L1 RAG Agent] Retrieving RBI guidelines for: {loan_type}")
    guidelines_result = get_rbi_guidelines(loan_type)

    if not guidelines_result["success"]:
        print(f"[L1 RAG Agent] ❌ RAG retrieval failed: {guidelines_result['error']}")
        return {
            **state,
            "rbi_guidelines": f"Could not retrieve guidelines: {guidelines_result['error']}",
            "rbi_sources": [],
            "current_agent": "l1_rag_agent"
        }

    raw_guidelines = guidelines_result["guidelines"]
    sources = guidelines_result["sources"]

    # ── Step 2: Summarise into a focused format for downstream agents ──────
    # The raw RAG output can be long — we condense it to the key points
    # relevant to this specific customer's situation
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an RBI regulatory expert at an Indian bank.
            Your job is to extract and summarise the key eligibility rules
            from RBI guidelines that are MOST RELEVANT to evaluating
            a specific loan application.

            Focus only on:
            - Minimum CIBIL score requirements
            - FOIR limits for the applicant's employment type
            - Age and income requirements
            - Any specific rules for this loan type
            - Counter-offer or rejection communication requirements

            Be concise — 5-7 bullet points maximum.
            Each point should be a specific, actionable rule."""
        ),
        (
            "human",
            """Loan Type     : {loan_type}
            Employment Type: {employment_type}

            RBI Guidelines Retrieved:
            {raw_guidelines}

            Extract the most relevant eligibility rules for this
            specific loan type and employment type combination."""
        )
    ])

    chain = prompt | llm | StrOutputParser()

    summarised_guidelines = chain.invoke({
        "loan_type": loan_type,
        "employment_type": employment_type,
        "raw_guidelines": raw_guidelines
    })

    print(f"[L1 RAG Agent] ✅ Guidelines retrieved and summarised")
    print(f"   Sources: {[s['source_file'] for s in sources[:2]]}")

    # ── Write results back to state ────────────────────────────────────────
    return {
        **state,
        "rbi_guidelines": summarised_guidelines,
        "rbi_sources": sources,
        "current_agent": "l1_rag_agent"
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Simulate state after L1 Data Validation passed
    test_state: LoanApplicationState = {
        "customer_id": "CUST001",
        "pan_number": "ABCDE1234F",
        "full_name": "Rajesh Kumar",
        "age": 35,
        "employment_type": "Salaried",
        "monthly_income": 85000,
        "monthly_expenses": 30000,
        "existing_emis": 12000,
        "loan_type_requested": "Home Loan",
        "loan_amount_requested": 4500000,
        "loan_tenure_years": 20,
        "city": "Bengaluru",
        "validation_passed": True,        # ← simulating L1 validation passed
        "validation_errors": [],
        "validation_notes": "Rajesh Kumar is a 35-year-old salaried employee at Infosys with a monthly income of ₹85,000.",
        "rbi_guidelines": None,
        "rbi_sources": None,
        "cibil_score": None,
        "credit_rating": None,
        "risk_level": None,
        "risk_reasons": None,
        "foir_percent": None,
        "monthly_emi": None,
        "decision": None,
        "decision_reason": None,
        "approved_amount": None,
        "approved_rate": None,
        "approved_tenure": None,
        "best_bank": None,
        "counter_offer_available": None,
        "counter_offer_amount": None,
        "counter_offer_tenure": None,
        "counter_offer_emi": None,
        "counter_offer_explanation": None,
        "compliance_passed": None,
        "compliance_notes": None,
        "compliance_violations": None,
        "final_response": None,
        "current_agent": "l1_data_validation",
        "errors": None,
        "next_agent": None
    }

    result = rag_agent(test_state)

    print("\n--- RAG Agent Result ---")
    print(f"Guidelines Retrieved:\n{result['rbi_guidelines']}")
    print(f"\nSources Used:")
    for s in (result["rbi_sources"] or [])[:3]:
        print(f"  → {s['source_file']} (Page {s['page']})")