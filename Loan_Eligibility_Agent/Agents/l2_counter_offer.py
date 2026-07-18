# agents/l2_counter_offer.py
# L2 Agent 2 — Counter-Offer Agent
# Only runs when the Decision Agent rejects the application.
# Generates a constructive alternative offer — as required by
# RBI Fair Practices Code Section 4 (counter-offer practices).
# This is what separates a good bank from a bad one —
# don't just reject, help the customer understand what they CAN get.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.state import LoanApplicationState
from mcp_server.tools import calculate_emi, get_loan_products
from llm_config import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def counter_offer_agent(state: LoanApplicationState) -> LoanApplicationState:
    """
    L2 Counter-Offer Agent.

    Responsibilities:
    1. Only runs when decision == REJECTED
    2. Reads max_eligible_loan_amount from Risk Scoring Agent's output
    3. Calculates EMI for the counter-offer amount
    4. Uses LLM to generate a clear, empathetic explanation
       of what the customer can do to qualify

    Reads from state:
    - decision (must be REJECTED to proceed)
    - decision_reason
    - approved_amount (max eligible — set by Risk Scoring Agent)
    - approved_rate, approved_tenure, best_bank
    - foir_percent, monthly_income, existing_emis
    - rbi_guidelines (to cite RBI backing for the counter-offer)
    - loan_amount_requested, loan_type_requested

    Writes to state:
    - counter_offer_available (bool)
    - counter_offer_amount
    - counter_offer_tenure
    - counter_offer_emi
    - counter_offer_explanation
    """
    print("\n[L2 Counter-Offer Agent] Running...")

    # ── Only runs if decision is REJECTED ─────────────────────────────────
    if state.get("decision") != "REJECTED":
        print("[L2 Counter-Offer Agent] ⏭️  Skipping — application was approved")
        return {
            **state,
            "counter_offer_available": False,
            "counter_offer_amount": None,
            "counter_offer_tenure": None,
            "counter_offer_emi": None,
            "counter_offer_explanation": None,
            "current_agent": "l2_counter_offer"
        }

    print(f"[L2 Counter-Offer Agent] Generating counter-offer for {state['full_name']}...")

    # ── Step 1: Get max eligible loan amount from Risk Scoring output ──────
    # Risk Scoring Agent already calculated this — we just read it from state
    max_eligible_amount = state.get("approved_amount")
    interest_rate = state.get("approved_rate", 12.0)
    tenure_years = state.get("loan_tenure_years", 20)
    best_bank = state.get("best_bank", "Standard Bank")

    # ── Step 2: Try extended tenure if amount is still insufficient ────────
    # If max eligible amount is very low, try extending tenure to
    # reduce EMI burden and potentially allow a higher loan amount
    extended_tenure = min(tenure_years + 5, 30)  # extend by 5 years, max 30

    # Calculate EMI for counter-offer amount
    if max_eligible_amount and max_eligible_amount > 0:
        emi_result = calculate_emi(
            principal=max_eligible_amount,
            annual_interest_rate=interest_rate,
            tenure_years=tenure_years
        )
        counter_offer_emi = emi_result["monthly_emi"] if emi_result["success"] else 0

        # Also calculate with extended tenure
        extended_emi_result = calculate_emi(
            principal=max_eligible_amount,
            annual_interest_rate=interest_rate,
            tenure_years=extended_tenure
        )
        extended_emi = extended_emi_result["monthly_emi"] if extended_emi_result["success"] else 0

        counter_offer_available = True
    else:
        # No viable counter-offer possible
        counter_offer_emi = 0
        extended_emi = 0
        counter_offer_available = False

    # ── Step 3: Check eligible products for counter-offer ─────────────────
    products_result = get_loan_products(
        state["loan_type_requested"],
        min_cibil_score=state.get("cibil_score", 0)
    )
    has_eligible_products = (
        products_result["success"] and
        products_result["eligible_products"] > 0
    )

    # ── Step 4: LLM generates empathetic, helpful explanation ─────────────
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a compassionate loan advisor at an Indian bank.
            A customer's loan application has been rejected, and your job
            is to explain the situation clearly and offer constructive alternatives.

            Your tone must be:
            - Empathetic and respectful — this is disappointing news
            - Constructive — focus on what they CAN do, not just what failed
            - Specific — use actual numbers, not vague suggestions
            - RBI-backed — reference the Fair Practices Code where relevant

            Structure your response as:
            1. Brief acknowledgement of rejection (1 sentence)
            2. What specifically caused the rejection (1-2 sentences with numbers)
            3. Counter-offer details (what they qualify for right now)
            4. Two specific steps they can take to qualify for the full amount
            5. Encouraging closing sentence

            Keep total response under 200 words."""
        ),
        (
            "human",
            """Customer: {name}
            Loan Requested: {loan_type} of ₹{requested_amount:,} for {tenure} years
            Rejection Reason: {decision_reason}

            Financial Profile:
            - Monthly Income   : ₹{monthly_income:,}
            - Existing EMIs    : ₹{existing_emis:,}
            - CIBIL Score      : {cibil_score} ({credit_rating})
            - Current FOIR     : {foir_percent:.1f}%

            Counter-Offer Available:
            - Max Eligible Amount : ₹{counter_offer_amount:,}
            - Interest Rate       : {interest_rate}%
            - Tenure Option 1     : {tenure} years → EMI ₹{counter_emi:,.0f}/month
            - Tenure Option 2     : {extended_tenure} years → EMI ₹{extended_emi:,.0f}/month
            - Best Bank           : {best_bank}

            RBI Guideline Reference:
            {rbi_guidelines}

            Generate a helpful, empathetic counter-offer message."""
        )
    ])

    chain = prompt | llm | StrOutputParser()

    if counter_offer_available:
        explanation = chain.invoke({
            "name": state["full_name"],
            "loan_type": state["loan_type_requested"],
            "requested_amount": state["loan_amount_requested"],
            "tenure": tenure_years,
            "decision_reason": state.get("decision_reason", "Eligibility criteria not met"),
            "monthly_income": state["monthly_income"],
            "existing_emis": state["existing_emis"],
            "cibil_score": state.get("cibil_score", 0),
            "credit_rating": state.get("credit_rating", "Unknown"),
            "foir_percent": state.get("foir_percent", 0.0),
            "counter_offer_amount": max_eligible_amount,
            "interest_rate": interest_rate,
            "counter_emi": counter_offer_emi,
            "extended_tenure": extended_tenure,
            "extended_emi": extended_emi,
            "best_bank": best_bank,
            "rbi_guidelines": state.get("rbi_guidelines", "RBI Fair Practices Code requires banks to offer alternatives where possible.")
        })
    else:
        explanation = (
            f"We regret that we are unable to approve your {state['loan_type_requested']} "
            f"application at this time. Based on your current CIBIL score of "
            f"{state.get('cibil_score', 0)} and FOIR of {state.get('foir_percent', 0):.1f}%, "
            f"we are unable to offer a viable alternative loan amount. We recommend "
            f"improving your CIBIL score and reducing existing EMI obligations before "
            f"reapplying. Please visit your nearest branch for personalised guidance."
        )

    print(f"[L2 Counter-Offer Agent] ✅ Counter-offer: "
          f"{'₹' + str(f'{max_eligible_amount:,.0f}') if counter_offer_available else 'Not available'}")

    # ── Write results back to state ────────────────────────────────────────
    return {
        **state,
        "counter_offer_available": counter_offer_available,
        "counter_offer_amount": max_eligible_amount if counter_offer_available else None,
        "counter_offer_tenure": tenure_years,
        "counter_offer_emi": counter_offer_emi if counter_offer_available else None,
        "counter_offer_explanation": explanation,
        "current_agent": "l2_counter_offer",
        "next_agent": "l3_compliance"
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Test with Mohammed Irfan — poor CIBIL, high FOIR, should be rejected
    test_state: LoanApplicationState = {
        "customer_id": "CUST005",
        "pan_number": "UVWXY7890L",
        "full_name": "Mohammed Irfan",
        "age": 38,
        "employment_type": "Self-Employed",
        "monthly_income": 40000,
        "monthly_expenses": 22000,
        "existing_emis": 15000,
        "loan_type_requested": "Home Loan",
        "loan_amount_requested": 3000000,
        "loan_tenure_years": 15,
        "city": "Chennai",
        # L1 outputs
        "validation_passed": True,
        "validation_errors": [],
        "validation_notes": "Mohammed Irfan is a 38-year-old self-employed individual earning ₹40,000/month with ₹15,000 in existing EMIs.",
        "rbi_guidelines": "Min CIBIL 700 for home loan. FOIR max 50% for salaried, 60% for self-employed. Counter-offers must be provided where possible per RBI Fair Practices Code.",
        "rbi_sources": [],
        "cibil_score": 580,
        "credit_rating": "Poor",
        "risk_level": "High",
        "risk_reasons": [
            "CIBIL score 580 is Poor — below minimum threshold of 650",
            "FOIR exceeds RBI limit — existing obligations too high",
            "2 defaults in last 7 years — high repayment risk"
        ],
        "foir_percent": 87.5,
        "monthly_emi": 20000.0,
        # L2 Decision already ran — REJECTED
        "decision": "REJECTED",
        "decision_reason": "CIBIL score of 580 is below the minimum threshold of 650 required for home loans, and FOIR of 87.5% significantly exceeds RBI recommended limit of 60% for self-employed applicants.",
        "approved_amount": 800000.0,   # max eligible — set by Risk Scoring Agent
        "approved_rate": 14.25,
        "approved_tenure": 15,
        "best_bank": "Axis Bank",
        # Not yet filled
        "counter_offer_available": None,
        "counter_offer_amount": None,
        "counter_offer_tenure": None,
        "counter_offer_emi": None,
        "counter_offer_explanation": None,
        "compliance_passed": None,
        "compliance_notes": None,
        "compliance_violations": None,
        "final_response": None,
        "current_agent": "l2_decision",
        "errors": None,
        "next_agent": None
    }

    result = counter_offer_agent(test_state)

    print("\n--- Counter-Offer Agent Result ---")
    print(f"Counter-offer Available : {result['counter_offer_available']}")
    print(f"Counter-offer Amount    : ₹{result['counter_offer_amount']:,}" if result['counter_offer_amount'] else "Counter-offer Amount: N/A")
    print(f"Counter-offer EMI       : ₹{result['counter_offer_emi']:,.0f}" if result['counter_offer_emi'] else "Counter-offer EMI: N/A")
    print(f"\nExplanation:\n{result['counter_offer_explanation']}")
    print(f"\nNext Agent: {result['next_agent']}")