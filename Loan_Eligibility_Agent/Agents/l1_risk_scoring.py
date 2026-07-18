# agents/l1_risk_scoring.py
# L1 Agent 3 — Risk Scoring Agent
# Fetches CIBIL score, calculates FOIR, determines risk level.
# This is the most data-heavy L1 agent — it calls two MCP tools
# and produces the core numbers that drive the Decision Agent.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.state import LoanApplicationState
from mcp_server.tools import get_credit_score, check_cibil_eligibility
from llm_config import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def risk_scoring_agent(state: LoanApplicationState) -> LoanApplicationState:
    """
    L1 Risk Scoring Agent.

    Responsibilities:
    1. Skip if validation failed
    2. Fetch CIBIL score via get_credit_score() tool
    3. Run full eligibility check via check_cibil_eligibility() tool
       (calculates FOIR, EMI, max eligible amount)
    4. Use LLM to reason over the numbers and assign a risk level
       with clear justification for the Decision Agent

    Reads from state:
    - validation_passed
    - pan_number, monthly_income, existing_emis
    - loan_amount_requested, loan_type_requested, loan_tenure_years

    Writes to state:
    - cibil_score, credit_rating
    - risk_level (Low / Medium / High)
    - risk_reasons (list of reasons)
    - foir_percent, monthly_emi
    """
    print("\n[L1 Risk Scoring Agent] Running...")

    # ── Skip if validation failed ──────────────────────────────────────────
    if not state.get("validation_passed"):
        print("[L1 Risk Scoring Agent] ⏭️  Skipping — validation did not pass")
        return {
            **state,
            "cibil_score": 0,
            "credit_rating": "Unknown",
            "risk_level": "High",
            "risk_reasons": ["Validation failed — risk assessment skipped"],
            "foir_percent": 0.0,
            "monthly_emi": 0.0,
            "current_agent": "l1_risk_scoring"
        }

    # ── Step 1: Fetch CIBIL score ──────────────────────────────────────────
    print(f"[L1 Risk Scoring Agent] Fetching credit score for PAN: {state['pan_number']}")
    credit_result = get_credit_score(state["pan_number"])

    if not credit_result["success"]:
        print(f"[L1 Risk Scoring Agent] ❌ Credit score fetch failed: {credit_result['error']}")
        return {
            **state,
            "cibil_score": 0,
            "credit_rating": "Unknown",
            "risk_level": "High",
            "risk_reasons": [f"Could not fetch credit score: {credit_result['error']}"],
            "foir_percent": 0.0,
            "monthly_emi": 0.0,
            "current_agent": "l1_risk_scoring"
        }

    cibil_score = credit_result["cibil_score"]
    credit_rating = credit_result["credit_rating"]
    defaults = credit_result["defaults_last_7_years"]
    late_payments = credit_result["late_payments_last_12_months"]
    credit_utilization = credit_result["credit_utilization_percent"]

    print(f"[L1 Risk Scoring Agent] CIBIL Score: {cibil_score} ({credit_rating})")

    # ── Step 2: Run full eligibility check (FOIR + EMI calculation) ────────
    print(f"[L1 Risk Scoring Agent] Running eligibility check...")
    eligibility_result = check_cibil_eligibility(
        cibil_score=cibil_score,
        monthly_income=state["monthly_income"],
        existing_emis=state["existing_emis"],
        requested_loan_amount=state["loan_amount_requested"],
        loan_type=state["loan_type_requested"],
        tenure_years=state["loan_tenure_years"]
    )

    foir_percent = eligibility_result.get("foir_percent", 0.0)
    monthly_emi = eligibility_result.get("new_emi", 0.0)
    max_eligible_loan = eligibility_result.get("max_eligible_loan_amount")
    eligibility_issues = eligibility_result.get("issues_found", [])
    eligibility_passed = eligibility_result.get("passed_checks", [])
    interest_rate = eligibility_result.get("interest_rate_used", 0.0)
    best_bank = eligibility_result.get("best_bank", "")

    print(f"[L1 Risk Scoring Agent] FOIR: {foir_percent:.1f}% | EMI: ₹{monthly_emi:,.0f}")

    # ── Step 3: LLM reasons over numbers and assigns risk level ───────────
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a senior credit risk analyst at an Indian bank.
            Based on the financial data provided, assess the overall risk level
            of this loan application.

            Risk levels:
            - Low: CIBIL 720+, FOIR under 45%, no defaults, stable employment
            - Medium: CIBIL 650-719, FOIR 45-55%, minor issues, some late payments
            - High: CIBIL below 650, FOIR over 55%, defaults present

            Respond in EXACTLY this format:
            RISK_LEVEL: <Low/Medium/High>
            REASONS:
            - <reason 1>
            - <reason 2>
            - <reason 3>

            Be specific with numbers. Max 3 reasons."""
        ),
        (
            "human",
            """Applicant: {name}
            Loan Type: {loan_type} of ₹{loan_amount:,}

            Credit Profile:
            - CIBIL Score         : {cibil_score} ({credit_rating})
            - Credit Utilization  : {credit_utilization}%
            - Defaults (7 years)  : {defaults}
            - Late Payments (12mo): {late_payments}

            Income & Obligations:
            - Monthly Income      : ₹{monthly_income:,}
            - Existing EMIs       : ₹{existing_emis:,}
            - New EMI             : ₹{monthly_emi:,}
            - FOIR                : {foir_percent:.1f}% (RBI limit: 50% for salaried)

            Eligibility checks passed : {passed}
            Eligibility issues found  : {issues}"""
        )
    ])

    chain = prompt | llm | StrOutputParser()

    risk_assessment = chain.invoke({
        "name": state["full_name"],
        "loan_type": state["loan_type_requested"],
        "loan_amount": state["loan_amount_requested"],
        "cibil_score": cibil_score,
        "credit_rating": credit_rating,
        "credit_utilization": credit_utilization,
        "defaults": defaults,
        "late_payments": late_payments,
        "monthly_income": state["monthly_income"],
        "existing_emis": state["existing_emis"],
        "monthly_emi": monthly_emi,
        "foir_percent": foir_percent,
        "passed": ", ".join(eligibility_passed) if eligibility_passed else "None",
        "issues": ", ".join(eligibility_issues) if eligibility_issues else "None"
    })

    # ── Parse LLM response ─────────────────────────────────────────────────
    lines = risk_assessment.strip().split("\n")
    risk_level = "Medium"
    risk_reasons = []

    for line in lines:
        if line.startswith("RISK_LEVEL:"):
            risk_level = line.replace("RISK_LEVEL:", "").strip()
        elif line.strip().startswith("- "):
            risk_reasons.append(line.strip()[2:])

    print(f"[L1 Risk Scoring Agent] ✅ Risk Level: {risk_level}")
    for r in risk_reasons:
        print(f"   → {r}")

    # ── Write results back to state ────────────────────────────────────────
    return {
        **state,
        "cibil_score": cibil_score,
        "credit_rating": credit_rating,
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
        "foir_percent": foir_percent,
        "monthly_emi": monthly_emi,
        # Pass max eligible loan forward for Counter-Offer Agent
        "approved_amount": max_eligible_loan,
        "approved_rate": interest_rate,
        "best_bank": best_bank,
        "current_agent": "l1_risk_scoring"
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Test with Rajesh Kumar — should be Low risk
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
        "validation_passed": True,
        "validation_errors": [],
        "validation_notes": "Rajesh Kumar is a 35-year-old salaried Infosys employee earning ₹85,000/month.",
        "rbi_guidelines": "Min CIBIL 700 for home loan. FOIR max 50% for salaried.",
        "rbi_sources": [],
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
        "current_agent": "l1_rag_agent",
        "errors": None,
        "next_agent": None
    }

    result = risk_scoring_agent(test_state)

    print("\n--- Risk Scoring Result ---")
    print(f"CIBIL Score  : {result['cibil_score']} ({result['credit_rating']})")
    print(f"Risk Level   : {result['risk_level']}")
    print(f"FOIR         : {result['foir_percent']}%")
    print(f"Monthly EMI  : ₹{result['monthly_emi']:,.2f}")
    print(f"Risk Reasons :")
    for r in (result["risk_reasons"] or []):
        print(f"  → {r}")