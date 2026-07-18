# agents/l2_decision.py
# L2 Agent 1 — Decision Agent
# The most important agent in the pipeline.
# Reads ALL L1 outputs from state and makes the final approve/reject decision.
# This agent synthesises everything — profile, RBI guidelines, risk score —
# into one clear, justified decision.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.state import LoanApplicationState
from mcp_server.tools import get_loan_products
from llm_config import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def decision_agent(state: LoanApplicationState) -> LoanApplicationState:
    """
    L2 Decision Agent.

    Responsibilities:
    1. Skip if validation failed
    2. Read all L1 outputs — profile summary, RBI guidelines, risk score
    3. Fetch matching loan products for the customer's CIBIL score
    4. Use LLM to synthesise everything into a justified decision
    5. Output APPROVED or REJECTED with full reasoning

    Reads from state (all L1 outputs):
    - validation_passed, validation_notes
    - rbi_guidelines, rbi_sources
    - cibil_score, credit_rating, risk_level, risk_reasons
    - foir_percent, monthly_emi
    - loan_type_requested, loan_amount_requested, loan_tenure_years
    - monthly_income, existing_emis

    Writes to state:
    - decision (APPROVED / REJECTED)
    - decision_reason
    - approved_amount, approved_rate, approved_tenure, best_bank
    """
    print("\n[L2 Decision Agent] Running...")

    # ── Skip if validation failed ──────────────────────────────────────────
    if not state.get("validation_passed"):
        print("[L2 Decision Agent] ⏭️  Skipping — validation did not pass")
        return {
            **state,
            "decision": "REJECTED",
            "decision_reason": "Application rejected at validation stage. Please check your inputs.",
            "current_agent": "l2_decision"
        }

    # ── Step 1: Fetch eligible loan products for this customer ─────────────
    print(f"[L2 Decision Agent] Fetching loan products for CIBIL: {state.get('cibil_score')}")
    products_result = get_loan_products(
        state["loan_type_requested"],
        min_cibil_score=state.get("cibil_score", 0)
    )

    if products_result["success"] and products_result["eligible_products"] > 0:
        products = products_result["products"]
        best_product = products[0]
        products_summary = "\n".join([
            f"- {p['bank_name']}: {p['interest_rate_percent']}% | "
            f"Max ₹{p['max_amount']:,} | "
            f"Min CIBIL {p['eligibility']['min_cibil_score']}"
            for p in products
        ])
    else:
        products = []
        best_product = None
        products_summary = "No eligible products found for this CIBIL score and loan type."

    # ── Step 2: LLM synthesises all L1 outputs into a decision ────────────
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are the Chief Credit Officer at an Indian bank.
            You have received a complete loan assessment from your specialist team.
            Make a final loan decision based on ALL the information provided.

            Your decision must be:
            1. Clearly APPROVED or REJECTED
            2. Backed by specific numbers (CIBIL score, FOIR percentage, EMI amount)
            3. Referenced to RBI guidelines where relevant
            4. Professional and respectful in tone

            Respond in EXACTLY this format:
            DECISION: <APPROVED or REJECTED>
            REASON: <2-3 sentences explaining the decision with specific numbers>
            APPROVED_AMOUNT: <amount in rupees, or 0 if rejected>
            APPROVED_RATE: <interest rate %, or 0 if rejected>
            APPROVED_TENURE: <tenure in years, or 0 if rejected>
            BEST_BANK: <bank name, or None if rejected>"""
        ),
        (
            "human",
            """=== LOAN APPLICATION ASSESSMENT ===

            CUSTOMER PROFILE:
            {validation_notes}

            LOAN REQUESTED:
            Type    : {loan_type}
            Amount  : ₹{loan_amount:,}
            Tenure  : {tenure} years

            RBI GUIDELINES SUMMARY:
            {rbi_guidelines}

            RISK ASSESSMENT:
            CIBIL Score  : {cibil_score} ({credit_rating})
            Risk Level   : {risk_level}
            FOIR         : {foir_percent:.1f}% (RBI limit: 50% for salaried)
            Monthly EMI  : ₹{monthly_emi:,.0f}
            Risk Reasons : {risk_reasons}

            ELIGIBLE LOAN PRODUCTS:
            {products_summary}

            Based on all the above, make your final credit decision."""
        )
    ])

    chain = prompt | llm | StrOutputParser()

    decision_response = chain.invoke({
        "validation_notes": state.get("validation_notes", "Not available"),
        "loan_type": state["loan_type_requested"],
        "loan_amount": state["loan_amount_requested"],
        "tenure": state["loan_tenure_years"],
        "rbi_guidelines": state.get("rbi_guidelines", "Not available"),
        "cibil_score": state.get("cibil_score", 0),
        "credit_rating": state.get("credit_rating", "Unknown"),
        "risk_level": state.get("risk_level", "Unknown"),
        "foir_percent": state.get("foir_percent", 0.0),
        "monthly_emi": state.get("monthly_emi", 0.0),
        "risk_reasons": ", ".join(state.get("risk_reasons", [])),
        "products_summary": products_summary
    })

    # ── Step 3: Parse LLM decision response ───────────────────────────────
    lines = decision_response.strip().split("\n")
    decision = "REJECTED"
    decision_reason = ""
    approved_amount = 0.0
    approved_rate = 0.0
    approved_tenure = 0
    best_bank = None

    for line in lines:
        if line.startswith("DECISION:"):
            val = line.replace("DECISION:", "").strip()
            decision = "APPROVED" if "APPROVED" in val.upper() else "REJECTED"
        elif line.startswith("REASON:"):
            decision_reason = line.replace("REASON:", "").strip()
        elif line.startswith("APPROVED_AMOUNT:"):
            try:
                approved_amount = float(
                    line.replace("APPROVED_AMOUNT:", "").strip()
                    .replace(",", "").replace("₹", "")
                )
            except ValueError:
                approved_amount = state["loan_amount_requested"] if decision == "APPROVED" else 0.0
        elif line.startswith("APPROVED_RATE:"):
            try:
                approved_rate = float(line.replace("APPROVED_RATE:", "").strip().replace("%", ""))
            except ValueError:
                approved_rate = best_product["interest_rate_percent"] if best_product else 0.0
        elif line.startswith("APPROVED_TENURE:"):
            try:
                approved_tenure = int(line.replace("APPROVED_TENURE:", "").strip())
            except ValueError:
                approved_tenure = state["loan_tenure_years"] if decision == "APPROVED" else 0
        elif line.startswith("BEST_BANK:"):
            val = line.replace("BEST_BANK:", "").strip()
            best_bank = None if val.lower() in ["none", "n/a", ""] else val

    print(f"[L2 Decision Agent] ✅ Decision: {decision}")
    print(f"   Reason: {decision_reason[:100]}...")

    # ── Write results back to state ────────────────────────────────────────
    return {
        **state,
        "decision": decision,
        "decision_reason": decision_reason,
        "approved_amount": approved_amount if decision == "APPROVED" else state.get("approved_amount"),
        "approved_rate": approved_rate if decision == "APPROVED" else state.get("approved_rate"),
        "approved_tenure": approved_tenure if decision == "APPROVED" else state.get("loan_tenure_years"),
        "best_bank": best_bank if decision == "APPROVED" else state.get("best_bank"),
        "current_agent": "l2_decision",
        "next_agent": "l2_counter_offer" if decision == "REJECTED" else "l3_compliance"
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Simulate full state after all L1 agents have run
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
        # L1 Data Validation outputs
        "validation_passed": True,
        "validation_errors": [],
        "validation_notes": "Rajesh Kumar is a 35-year-old salaried employee at Infosys, earning ₹85,000/month with ₹12,000 in existing EMIs. He is applying for a ₹45L Home Loan for 20 years.",
        # L1 RAG outputs
        "rbi_guidelines": "Min CIBIL 700 for home loan. FOIR max 50% for salaried. LTV max 80% for loans above ₹30L. Age 21-70.",
        "rbi_sources": [{"source_file": "rbi_home_loan_guidelines.pdf", "page": 1}],
        # L1 Risk Scoring outputs
        "cibil_score": 742,
        "credit_rating": "Good",
        "risk_level": "Low",
        "risk_reasons": [
            "CIBIL score 742 is Good — above minimum threshold of 700",
            "FOIR at 46.2% is within RBI recommended limit of 50%",
            "No defaults in last 7 years — clean repayment history"
        ],
        "foir_percent": 46.2,
        "monthly_emi": 39204.0,
        # Not yet filled
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
        "current_agent": "l1_risk_scoring",
        "errors": None,
        "next_agent": None
    }

    result = decision_agent(test_state)

    print("\n--- Decision Agent Result ---")
    print(f"Decision         : {result['decision']}")
    print(f"Reason           : {result['decision_reason']}")
    print(f"Approved Amount  : ₹{result['approved_amount']:,}" if result['approved_amount'] else "Approved Amount  : N/A")
    print(f"Approved Rate    : {result['approved_rate']}%" if result['approved_rate'] else "Approved Rate    : N/A")
    print(f"Best Bank        : {result['best_bank']}")
    print(f"Next Agent       : {result['next_agent']}")