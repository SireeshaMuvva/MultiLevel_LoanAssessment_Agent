# orchestrator/supervisor.py
# Task 5.2 — Supervisor Orchestrator
# The main entry point for the entire pipeline.
# Takes raw customer data, builds the initial state,
# runs the LangGraph workflow, and returns the final result.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from orchestrator.state import LoanApplicationState
from orchestrator.graph import build_graph
from observability.langsmith_config import get_run_metadata


def run_loan_assessment(customer_data: dict) -> dict:
    """
    Main entry point for the loan eligibility pipeline.

    Takes raw customer data (from UI form or API),
    builds the initial state, runs all agents via LangGraph,
    and returns a clean result summary.

    Args:
        customer_data: dict with customer's loan application details

    Returns:
        dict with decision, final response, and key metrics
    """
    print("\n" + "="*60)
    print("🏦 LOAN ELIGIBILITY ASSESSMENT STARTED")
    print("="*60)
    print(f"Customer : {customer_data.get('full_name')}")
    print(f"Loan     : {customer_data.get('loan_type_requested')} "
          f"₹{customer_data.get('loan_amount_requested', 0):,}")

    # ── Step 1: Build initial LangGraph state from customer data ──────────
    initial_state: LoanApplicationState = {
        # Customer input fields
        "customer_id":          customer_data.get("customer_id", "CUST000"),
        "pan_number":           customer_data.get("pan_number", ""),
        "full_name":            customer_data.get("full_name", ""),
        "age":                  customer_data.get("age", 0),
        "employment_type":      customer_data.get("employment_type", "Salaried"),
        "monthly_income":       customer_data.get("monthly_income", 0),
        "monthly_expenses":     customer_data.get("monthly_expenses", 0),
        "existing_emis":        customer_data.get("existing_emis", 0),
        "loan_type_requested":  customer_data.get("loan_type_requested", "Home Loan"),
        "loan_amount_requested": customer_data.get("loan_amount_requested", 0),
        "loan_tenure_years":    customer_data.get("loan_tenure_years", 20),
        "city":                 customer_data.get("city", ""),

        # All agent output fields initialised to None
        "validation_passed":        None,
        "validation_errors":        None,
        "validation_notes":         None,
        "rbi_guidelines":           None,
        "rbi_sources":              None,
        "cibil_score":              None,
        "credit_rating":            None,
        "risk_level":               None,
        "risk_reasons":             None,
        "foir_percent":             None,
        "monthly_emi":              None,
        "decision":                 None,
        "decision_reason":          None,
        "approved_amount":          None,
        "approved_rate":            None,
        "approved_tenure":          None,
        "best_bank":                None,
        "counter_offer_available":  None,
        "counter_offer_amount":     None,
        "counter_offer_tenure":     None,
        "counter_offer_emi":        None,
        "counter_offer_explanation": None,
        "compliance_passed":        None,
        "compliance_notes":         None,
        "compliance_violations":    None,
        "final_response":           None,
        "current_agent":            None,
        "errors":                   None,
        "next_agent":               None
    }

    # ── Step 2: Build and run the LangGraph pipeline ───────────────────────
    app = build_graph()

    print("\n[Supervisor] Starting agent pipeline...\n")

    # LangSmith run config — tags each trace with customer + loan type
    # Visible in smith.langchain.com under your project

    run_config = {
        "run_name": f"loan-assessment-{customer_data.get('full_name', 'unknown').replace(' ', '-').lower()}",
        **get_run_metadata(
            customer_name=customer_data.get("full_name", "Unknown"),
            loan_type=customer_data.get("loan_type_requested", "Unknown")
        )
    }

    final_state = app.invoke(initial_state,config=run_config)

    # ── Step 3: Extract and return clean result ────────────────────────────
    print("\n" + "="*60)
    print("🏦 ASSESSMENT COMPLETE")
    print("="*60)

    result = {
        "customer_name":        final_state.get("full_name"),
        "decision":             final_state.get("decision"),
        "compliance_passed":    final_state.get("compliance_passed"),
        "cibil_score":          final_state.get("cibil_score"),
        "credit_rating":        final_state.get("credit_rating"),
        "risk_level":           final_state.get("risk_level"),
        "foir_percent":         final_state.get("foir_percent"),
        "monthly_emi":          final_state.get("monthly_emi"),
        "approved_amount":      final_state.get("approved_amount"),
        "approved_rate":        final_state.get("approved_rate"),
        "approved_tenure":      final_state.get("approved_tenure"),
        "best_bank":            final_state.get("best_bank"),
        "counter_offer_available": final_state.get("counter_offer_available"),
        "counter_offer_amount": final_state.get("counter_offer_amount"),
        "counter_offer_emi":    final_state.get("counter_offer_emi"),
        "rbi_sources":          final_state.get("rbi_sources"),
        "final_response":       final_state.get("final_response"),
        "compliance_notes":     final_state.get("compliance_notes"),
        "risk_reasons":         final_state.get("risk_reasons")
    }

    return result


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    # ── Test A: Rajesh Kumar — should APPROVE ─────────────────────────────
    print("\n" + "🔵 "*20)
    print("TEST A: Rajesh Kumar (Expected: APPROVE)")
    print("🔵 "*20)

    rajesh = {
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
        "city": "Bengaluru"
    }

    result_a = run_loan_assessment(rajesh)

    print(f"\n✅ Decision         : {result_a['decision']}")
    print(f"   CIBIL Score     : {result_a['cibil_score']} ({result_a['credit_rating']})")
    print(f"   Risk Level      : {result_a['risk_level']}")
    print(f"   FOIR            : {result_a['foir_percent']}%")
    print(f"   Monthly EMI     : ₹{result_a['monthly_emi']:,.0f}")
    print(f"   Compliance      : {'✅ Passed' if result_a['compliance_passed'] else '❌ Failed'}")
    print(f"\n--- FINAL RESPONSE ---")
    print(result_a["final_response"])

    # ── Test B: Mohammed Irfan — should REJECT with counter-offer ─────────
    print("\n" + "🔴 "*20)
    print("TEST B: Mohammed Irfan (Expected: REJECT + Counter-offer)")
    print("🔴 "*20)

    irfan = {
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
        "city": "Chennai"
    }

    result_b = run_loan_assessment(irfan)

    print(f"\n❌ Decision              : {result_b['decision']}")
    print(f"   CIBIL Score          : {result_b['cibil_score']} ({result_b['credit_rating']})")
    print(f"   Risk Level           : {result_b['risk_level']}")
    print(f"   FOIR                 : {result_b['foir_percent']}%")
    print(f"   Counter-offer        : {'Available' if result_b['counter_offer_available'] else 'Not available'}")
    if result_b['counter_offer_amount']:
        print(f"   Counter-offer Amount : ₹{result_b['counter_offer_amount']:,.0f}")
        print(f"   Counter-offer EMI    : ₹{result_b['counter_offer_emi']:,.0f}")
    print(f"\n--- FINAL RESPONSE ---")
    print(result_b["final_response"])