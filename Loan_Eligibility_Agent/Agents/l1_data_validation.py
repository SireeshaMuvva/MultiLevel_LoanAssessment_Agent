# agents/l1_data_validation.py
# L1 Agent 1 — Data Validation Agent
# First agent in the pipeline — validates customer input before
# any expensive LLM or API calls are made downstream.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.state import LoanApplicationState
from llm_config import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def validate_data_agent(state: LoanApplicationState) -> LoanApplicationState:
    """
    L1 Data Validation Agent.

    Responsibilities:
    1. Check all required fields are present and valid
    2. Run rule-based checks (age, income thresholds)
    3. Use LLM to summarise the customer profile clearly
       for downstream agents to use

    Writes to state:
    - validation_passed (bool)
    - validation_errors (list)
    - validation_notes (plain English profile summary)
    """
    print("\n[L1 Data Validation Agent] Running...")

    errors = []

    # ── Rule-based checks (no LLM needed — fast and cheap) ────────────────

    # Age check
    if not (21 <= state["age"] <= 70):
        errors.append(f"Age {state['age']} is outside eligible range (21-70 years)")

    # Income check
    if state["monthly_income"] <= 0:
        errors.append("Monthly income must be greater than 0")
    elif state["monthly_income"] < 15000:
        errors.append(f"Monthly income ₹{state['monthly_income']:,} is below minimum threshold of ₹15,000")

    # Loan amount check
    if state["loan_amount_requested"] <= 0:
        errors.append("Loan amount requested must be greater than 0")

    # Tenure check
    if not (1 <= state["loan_tenure_years"] <= 30):
        errors.append(f"Loan tenure {state['loan_tenure_years']} years is outside allowed range (1-30 years)")

    # Existing EMI sanity check
    if state["existing_emis"] >= state["monthly_income"]:
        errors.append(
            f"Existing EMIs ₹{state['existing_emis']:,} already exceed monthly income "
            f"₹{state['monthly_income']:,} — application cannot proceed"
        )

    # Employment type check
    valid_employment = ["Salaried", "Self-Employed"]
    if state["employment_type"] not in valid_employment:
        errors.append(f"Employment type '{state['employment_type']}' is not valid. Must be one of: {valid_employment}")

    # Loan type check
    valid_loan_types = ["Home Loan", "Personal Loan", "Business Loan", "Car Loan"]
    if state["loan_type_requested"] not in valid_loan_types:
        errors.append(f"Loan type '{state['loan_type_requested']}' is not supported. Must be one of: {valid_loan_types}")

    # ── LLM: Generate a clean profile summary for downstream agents ────────
    # Even if validation fails, we generate the summary so other agents
    # have a clear picture of the customer

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a bank's customer profile analyst.
            Summarise the loan applicant's profile in 3-4 clear sentences.
            Be factual, concise, and highlight key financial indicators.
            Do not make any eligibility judgement — just describe the profile."""
        ),
        (
            "human",
            """Customer Profile:
            Name           : {full_name}
            Age            : {age} years
            Employment     : {employment_type}
            Monthly Income : ₹{monthly_income:,}
            Monthly Expenses: ₹{monthly_expenses:,}
            Existing EMIs  : ₹{existing_emis:,}
            Loan Requested : {loan_type} of ₹{loan_amount:,} for {tenure} years
            City           : {city}

            Provide a brief, factual profile summary."""
        )
    ])

    chain = prompt | llm | StrOutputParser()

    profile_summary = chain.invoke({
        "full_name": state["full_name"],
        "age": state["age"],
        "employment_type": state["employment_type"],
        "monthly_income": state["monthly_income"],
        "monthly_expenses": state["monthly_expenses"],
        "existing_emis": state["existing_emis"],
        "loan_type": state["loan_type_requested"],
        "loan_amount": state["loan_amount_requested"],
        "tenure": state["loan_tenure_years"],
        "city": state["city"]
    })

    validation_passed = len(errors) == 0

    if validation_passed:
        print(f"[L1 Data Validation Agent] ✅ Validation passed for {state['full_name']}")
    else:
        print(f"[L1 Data Validation Agent] ❌ Validation failed — {len(errors)} error(s)")
        for e in errors:
            print(f"   → {e}")

    # ── Write results back to state ────────────────────────────────────────
    return {
        **state,
        "validation_passed": validation_passed,
        "validation_errors": errors,
        "validation_notes": profile_summary,
        "current_agent": "l1_data_validation"
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Test with Rajesh Kumar's profile
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
        "validation_passed": None,
        "validation_errors": None,
        "validation_notes": None,
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
        "current_agent": None,
        "errors": None,
        "next_agent": None
    }

    result = validate_data_agent(test_state)

    print("\n--- Validation Result ---")
    print(f"Passed  : {result['validation_passed']}")
    print(f"Errors  : {result['validation_errors']}")
    print(f"\nProfile Summary:\n{result['validation_notes']}")