# test_pipeline.py
# Task 5.3 — Full end-to-end pipeline test
# Runs all 5 mock customers through the complete agent pipeline
# and produces a summary report of results.
#
# Run: uv run python3 -m test_pipeline

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from orchestrator.supervisor import run_loan_assessment


# ── All 5 mock customers ───────────────────────────────────────────────────────
CUSTOMERS = [
    {
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
    },
    {
        "customer_id": "CUST002",
        "pan_number": "PQRST5678G",
        "full_name": "Priya Sharma",
        "age": 29,
        "employment_type": "Salaried",
        "monthly_income": 55000,
        "monthly_expenses": 20000,
        "existing_emis": 8000,
        "loan_type_requested": "Personal Loan",
        "loan_amount_requested": 500000,
        "loan_tenure_years": 3,
        "city": "Mumbai"
    },
    {
        "customer_id": "CUST003",
        "pan_number": "LMNOP9012H",
        "full_name": "Suresh Reddy",
        "age": 42,
        "employment_type": "Self-Employed",
        "monthly_income": 120000,
        "monthly_expenses": 50000,
        "existing_emis": 35000,
        "loan_type_requested": "Business Loan",
        "loan_amount_requested": 2000000,
        "loan_tenure_years": 5,
        "city": "Hyderabad"
    },
    {
        "customer_id": "CUST004",
        "pan_number": "FGHIJ3456K",
        "full_name": "Anita Desai",
        "age": 27,
        "employment_type": "Salaried",
        "monthly_income": 45000,
        "monthly_expenses": 18000,
        "existing_emis": 0,
        "loan_type_requested": "Car Loan",
        "loan_amount_requested": 800000,
        "loan_tenure_years": 5,
        "city": "Pune"
    },
    {
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
]


def print_result_card(customer: dict, result: dict, index: int):
    """Prints a clean summary card for each customer's result."""

    decision = result.get("decision", "UNKNOWN")
    icon = "✅" if decision == "APPROVED" else "❌"

    print(f"\n{'='*65}")
    print(f"  {icon}  CUSTOMER {index+1}: {customer['full_name']}")
    print(f"{'='*65}")
    print(f"  Loan Requested : {customer['loan_type_requested']} "
          f"₹{customer['loan_amount_requested']:,}")
    print(f"  Decision       : {decision}")
    print(f"  CIBIL Score    : {result.get('cibil_score')} "
          f"({result.get('credit_rating')})")
    print(f"  Risk Level     : {result.get('risk_level')}")
    print(f"  FOIR           : {result.get('foir_percent')}%")
    print(f"  Monthly EMI    : ₹{result.get('monthly_emi', 0):,.0f}")
    print(f"  Compliance     : "
          f"{'✅ Passed' if result.get('compliance_passed') else '❌ Failed'}")

    if decision == "APPROVED":
        print(f"\n  Approved Amount : ₹{result.get('approved_amount', 0):,}")
        print(f"  Interest Rate   : {result.get('approved_rate')}%")
        print(f"  Best Bank       : {result.get('best_bank')}")
    else:
        if result.get("counter_offer_available"):
            print(f"\n  Counter-Offer   : "
                  f"₹{result.get('counter_offer_amount', 0):,.0f} available")
            print(f"  Counter EMI     : "
                  f"₹{result.get('counter_offer_emi', 0):,.0f}/month")
        else:
            print(f"\n  Counter-Offer   : Not available")

    if result.get("rbi_sources"):
        sources = [s.get("source_file") for s in result["rbi_sources"][:2]]
        print(f"\n  RBI Sources     : {', '.join(set(sources))}")

    print(f"\n  Risk Reasons:")
    for r in (result.get("risk_reasons") or [])[:3]:
        print(f"    → {r}")


def run_full_pipeline_test():
    """
    Runs all 5 customers through the complete agent pipeline
    and prints a summary report.
    """
    print("\n" + "🏦 "*20)
    print("   LOAN ELIGIBILITY AGENT — FULL PIPELINE TEST")
    print("   Testing all 5 customers end-to-end")
    print("🏦 "*20)

    results = []
    approved_count = 0
    rejected_count = 0
    failed_count = 0

    for i, customer in enumerate(CUSTOMERS):
        try:
            print(f"\n\n{'─'*65}")
            print(f"  Processing customer {i+1}/5: {customer['full_name']}...")
            print(f"{'─'*65}")

            result = run_loan_assessment(customer)
            results.append((customer, result))

            if result.get("decision") == "APPROVED":
                approved_count += 1
            else:
                rejected_count += 1

            print_result_card(customer, result, i)

        except Exception as e:
            print(f"\n❌ Error processing {customer['full_name']}: {e}")
            failed_count += 1
            results.append((customer, {"decision": "ERROR", "error": str(e)}))

    # ── Summary Report ─────────────────────────────────────────────────────
    print(f"\n\n{'='*65}")
    print("  📊  PIPELINE TEST SUMMARY REPORT")
    print(f"{'='*65}")
    print(f"  Total Customers Processed : {len(CUSTOMERS)}")
    print(f"  ✅ Approved               : {approved_count}")
    print(f"  ❌ Rejected               : {rejected_count}")
    print(f"  ⚠️  Errors                : {failed_count}")
    print(f"\n  Customer Outcomes:")

    for i, (customer, result) in enumerate(results):
        decision = result.get("decision", "ERROR")
        icon = "✅" if decision == "APPROVED" else ("❌" if decision == "REJECTED" else "⚠️")
        counter = " (counter-offer available)" if result.get("counter_offer_available") else ""
        print(f"    {icon} {customer['full_name']:20s} → {decision}{counter}")

    print(f"\n{'='*65}")
    print("  ✅ Full pipeline test complete!")
    print("  Ready for Week 6 — Evaluation, Observability & UI")
    print(f"{'='*65}\n")

    return results


if __name__ == "__main__":
    run_full_pipeline_test()