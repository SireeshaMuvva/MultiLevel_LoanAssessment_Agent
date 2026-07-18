# agents/l3_compliance.py
# L3 Agent — Compliance Agent
# The last line of defence before the response reaches the user.
# Cross-checks the final decision against RBI guidelines to ensure
# no regulatory rule was violated anywhere in the pipeline.
# Also assembles the final response that the user sees.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.state import LoanApplicationState
from llm_config import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def compliance_agent(state: LoanApplicationState) -> LoanApplicationState:
    """
    L3 Compliance Agent.

    Responsibilities:
    1. Cross-check the decision against RBI guidelines
    2. Flag any regulatory violations
    3. If violations found — override decision to REJECTED
    4. Assemble the final human-readable response for the user

    Reads from state (everything from all previous agents):
    - decision, decision_reason
    - approved_amount, approved_rate, approved_tenure, best_bank
    - counter_offer_available, counter_offer_explanation
    - cibil_score, foir_percent, monthly_emi
    - rbi_guidelines, rbi_sources
    - validation_notes, risk_level, risk_reasons

    Writes to state:
    - compliance_passed (bool)
    - compliance_notes
    - compliance_violations (list)
    - final_response (complete user-facing response)
    """
    print("\n[L3 Compliance Agent] Running...")

    decision = state.get("decision", "REJECTED")
    cibil_score = state.get("cibil_score", 0)
    foir_percent = state.get("foir_percent", 0.0)
    approved_rate = state.get("approved_rate", 0.0)
    approved_amount = state.get("approved_amount", 0.0)
    loan_type = state["loan_type_requested"]

    # ── Step 1: Rule-based compliance checks ──────────────────────────────
    # These are hard regulatory rules — no LLM needed for these checks
    violations = []

    # Check 1: CIBIL minimum for approved loans
    if decision == "APPROVED":
        cibil_minimums = {
            "Home Loan": 700,
            "Personal Loan": 680,
            "Business Loan": 650,
            "Car Loan": 700
        }
        min_cibil = cibil_minimums.get(loan_type, 650)
        if cibil_score < min_cibil:
            violations.append(
                f"COMPLIANCE VIOLATION: {loan_type} approved with CIBIL {cibil_score} "
                f"below RBI minimum of {min_cibil}"
            )

    # Check 2: FOIR limit for approved loans
    if decision == "APPROVED":
        foir_limit = 50.0 if state["employment_type"] == "Salaried" else 65.0
        if foir_percent > foir_limit:
            violations.append(
                f"COMPLIANCE VIOLATION: FOIR {foir_percent:.1f}% exceeds RBI "
                f"recommended limit of {foir_limit}% for {state['employment_type']} applicants"
            )

    # Check 3: Interest rate sanity check
    if decision == "APPROVED" and approved_rate > 0:
        rate_ranges = {
            "Home Loan": (7.0, 15.0),
            "Personal Loan": (9.0, 24.0),
            "Business Loan": (10.0, 24.0),
            "Car Loan": (7.5, 15.0)
        }
        min_rate, max_rate = rate_ranges.get(loan_type, (7.0, 24.0))
        if not (min_rate <= approved_rate <= max_rate):
            violations.append(
                f"COMPLIANCE VIOLATION: Interest rate {approved_rate}% is outside "
                f"expected range of {min_rate}%-{max_rate}% for {loan_type}"
            )

    # Check 4: Counter-offer must be provided on rejection (RBI requirement)
    if decision == "REJECTED" and not state.get("counter_offer_available"):
        # Not a hard violation but flag it as a compliance note
        violations.append(
            "COMPLIANCE NOTE: No counter-offer was generated for rejected application. "
            "RBI Fair Practices Code recommends offering alternatives where possible."
        )

    compliance_passed = len([v for v in violations if "VIOLATION" in v]) == 0

    # ── Step 2: Override decision if hard violations found ─────────────────
    if not compliance_passed:
        print(f"[L3 Compliance Agent] ❌ Compliance violations found — overriding decision")
        for v in violations:
            print(f"   → {v}")
        # Override to rejected if compliance fails
        decision = "REJECTED"
    else:
        print(f"[L3 Compliance Agent] ✅ Compliance checks passed")

    # ── Step 3: LLM assembles the final user-facing response ──────────────
    llm = get_llm()

    if decision == "APPROVED":
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are a professional loan officer writing an official
                loan sanction communication to a customer.
                Be professional, clear, and include all key details.
                Structure: greeting → approval announcement →
                loan details → next steps → closing."""
            ),
            (
                "human",
                """Write a loan approval communication for:

                Customer      : {name}
                Decision      : APPROVED ✅
                Loan Type     : {loan_type}
                Amount        : ₹{approved_amount:,}
                Interest Rate : {approved_rate}% per annum
                Tenure        : {tenure} years
                Monthly EMI   : ₹{monthly_emi:,.0f}
                Bank          : {best_bank}

                Risk Profile  : {risk_level} Risk
                CIBIL Score   : {cibil_score} ({credit_rating})
                FOIR          : {foir_percent:.1f}%

                RBI Guideline Reference: {rbi_source}

                Include next steps: document submission, processing time (15 working days),
                branch visit for signing. Keep under 250 words."""
            )
        ])

        final_response = (prompt | llm | StrOutputParser()).invoke({
            "name": state["full_name"],
            "loan_type": loan_type,
            "approved_amount": approved_amount or state["loan_amount_requested"],
            "approved_rate": approved_rate,
            "tenure": state.get("approved_tenure") or state["loan_tenure_years"],
            "monthly_emi": state.get("monthly_emi", 0),
            "best_bank": state.get("best_bank", "Our Bank"),
            "risk_level": state.get("risk_level", "Low"),
            "cibil_score": cibil_score,
            "credit_rating": state.get("credit_rating", "Good"),
            "foir_percent": foir_percent,
            "rbi_source": state.get("rbi_sources", [{}])[0].get("source_file", "RBI Guidelines") if state.get("rbi_sources") else "RBI Guidelines"
        })

    else:
        # Rejection — include counter-offer if available
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are a compassionate loan officer writing an official
                loan rejection communication. Be respectful, clear about
                reasons, and constructive about next steps.
                Structure: greeting → rejection → specific reasons →
                counter-offer (if available) → improvement steps → closing."""
            ),
            (
                "human",
                """Write a loan rejection communication for:

                Customer       : {name}
                Decision       : REJECTED ❌
                Loan Requested : {loan_type} of ₹{requested_amount:,}
                Rejection Reason: {decision_reason}

                Risk Profile   : {risk_level} Risk
                CIBIL Score    : {cibil_score} ({credit_rating})
                FOIR           : {foir_percent:.1f}%

                Counter-offer  : {counter_offer}

                Compliance notes: {compliance_notes}

                Keep under 250 words. Be empathetic but factual."""
            )
        ])

        counter_offer_text = (
            state.get("counter_offer_explanation", "No counter-offer available")
            if state.get("counter_offer_available")
            else "No viable counter-offer available at this time."
        )

        final_response = (prompt | llm | StrOutputParser()).invoke({
            "name": state["full_name"],
            "loan_type": loan_type,
            "requested_amount": state["loan_amount_requested"],
            "decision_reason": state.get("decision_reason", "Eligibility criteria not met"),
            "risk_level": state.get("risk_level", "High"),
            "cibil_score": cibil_score,
            "credit_rating": state.get("credit_rating", "Poor"),
            "foir_percent": foir_percent,
            "counter_offer": counter_offer_text,
            "compliance_notes": "; ".join(violations) if violations else "None"
        })

    print(f"[L3 Compliance Agent] ✅ Final response assembled")

    # ── Write results back to state ────────────────────────────────────────
    return {
        **state,
        "decision": decision,
        "compliance_passed": compliance_passed,
        "compliance_notes": "; ".join(violations) if violations else "All checks passed",
        "compliance_violations": violations,
        "final_response": final_response,
        "current_agent": "l3_compliance",
        "next_agent": "END"
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("\n=== TEST A: Approved Application (Rajesh Kumar) ===")
    approved_state: LoanApplicationState = {
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
        "rbi_guidelines": "Min CIBIL 700. FOIR max 50% for salaried.",
        "rbi_sources": [{"source_file": "rbi_home_loan_guidelines.pdf", "page": 1}],
        "cibil_score": 742,
        "credit_rating": "Good",
        "risk_level": "Low",
        "risk_reasons": ["CIBIL 742 is Good", "FOIR 46.2% within limits", "No defaults"],
        "foir_percent": 46.2,
        "monthly_emi": 39204.0,
        "decision": "APPROVED",
        "decision_reason": "Strong CIBIL score and healthy FOIR well within RBI limits.",
        "approved_amount": 4500000.0,
        "approved_rate": 8.5,
        "approved_tenure": 20,
        "best_bank": "State Bank of India",
        "counter_offer_available": False,
        "counter_offer_amount": None,
        "counter_offer_tenure": None,
        "counter_offer_emi": None,
        "counter_offer_explanation": None,
        "compliance_passed": None,
        "compliance_notes": None,
        "compliance_violations": None,
        "final_response": None,
        "current_agent": "l2_counter_offer",
        "errors": None,
        "next_agent": None
    }

    result = compliance_agent(approved_state)
    print(f"\nCompliance Passed : {result['compliance_passed']}")
    print(f"Violations        : {result['compliance_violations']}")
    print(f"\n{'='*60}")
    print("FINAL RESPONSE:")
    print('='*60)
    print(result["final_response"])