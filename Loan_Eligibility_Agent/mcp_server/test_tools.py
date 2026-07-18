# test_tools.py
# Task 3.2 — Test all 5 tools independently
# Run: python -m mcp_server.test_tools  (from project root)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server.tools import (
    get_credit_score,
    get_rbi_guidelines,
    get_loan_products,
    calculate_emi,
    check_cibil_eligibility
)


def test_get_credit_score():
    print("\n" + "="*60)
    print("TOOL 1: get_credit_score")
    print("="*60)

    # Test valid PAN
    result = get_credit_score("ABCDE1234F")
    print(f"✅ Found: {result['customer_name']}")
    print(f"   CIBIL Score : {result['cibil_score']}")
    print(f"   Rating      : {result['credit_rating']}")
    print(f"   Defaults    : {result['defaults_last_7_years']}")
    print(f"   Late payments: {result['late_payments_last_12_months']}")

    # Test invalid PAN
    result2 = get_credit_score("INVALID123")
    print(f"\n❌ Invalid PAN test: {result2['error']}")


def test_get_loan_products():
    print("\n" + "="*60)
    print("TOOL 3: get_loan_products")
    print("="*60)

    result = get_loan_products("Home Loan", min_cibil_score=742)
    print(f"✅ Loan Type: {result['loan_type']}")
    print(f"   Total products available : {result['total_products_found']}")
    print(f"   Eligible for CIBIL 742  : {result['eligible_products']}")
    for p in result["products"]:
        print(f"   → {p['bank_name']} | Rate: {p['interest_rate_percent']}% | "
              f"Max: ₹{p['max_amount']:,}")


def test_calculate_emi():
    print("\n" + "="*60)
    print("TOOL 4: calculate_emi")
    print("="*60)

    result = calculate_emi(
        principal=4500000,
        annual_interest_rate=8.5,
        tenure_years=20
    )
    print(f"✅ Loan Amount  : ₹{result['principal']:,.2f}")
    print(f"   Interest Rate: {result['annual_interest_rate_percent']}%")
    print(f"   Tenure       : {result['tenure_years']} years")
    print(f"   Monthly EMI  : ₹{result['monthly_emi']:,.2f}")
    print(f"   Total Payment: ₹{result['total_payment']:,.2f}")
    print(f"   Total Interest: ₹{result['total_interest_paid']:,.2f}")


def test_check_cibil_eligibility():
    print("\n" + "="*60)
    print("TOOL 5: check_cibil_eligibility")
    print("="*60)

    # Test 1: Should be approved (Rajesh Kumar)
    print("\n--- Test A: Rajesh Kumar (should APPROVE) ---")
    result = check_cibil_eligibility(
        cibil_score=742,
        monthly_income=85000,
        existing_emis=12000,
        requested_loan_amount=4500000,
        loan_type="Home Loan",
        tenure_years=20
    )
    print(f"Decision : {result['decision']}")
    print(f"FOIR     : {result['foir_percent']}% (limit: {result['foir_limit_percent']}%)")
    print(f"New EMI  : ₹{result['new_emi']:,}")
    for check in result["passed_checks"]:
        print(f"  ✅ {check}")
    for issue in result["issues_found"]:
        print(f"  ❌ {issue}")

    # Test 2: Should be rejected (Mohammed Irfan — poor CIBIL + high FOIR)
    print("\n--- Test B: Mohammed Irfan (should REJECT) ---")
    result2 = check_cibil_eligibility(
        cibil_score=580,
        monthly_income=40000,
        existing_emis=15000,
        requested_loan_amount=3000000,
        loan_type="Home Loan",
        tenure_years=15
    )
    print(f"Decision : {result2['decision']}")
    print(f"FOIR     : {result2['foir_percent']}% (limit: {result2['foir_limit_percent']}%)")
    print(f"New EMI  : ₹{result2['new_emi']:,}")
    for issue in result2["issues_found"]:
        print(f"  ❌ {issue}")
    if result2["max_eligible_loan_amount"]:
        print(f"  💡 Max eligible loan: ₹{result2['max_eligible_loan_amount']:,.0f}")


def test_get_rbi_guidelines():
    # Run this last as it makes an LLM call
    print("\n" + "="*60)
    print("TOOL 2: get_rbi_guidelines (RAG + LLM call)")
    print("="*60)
    result = get_rbi_guidelines("Home Loan")
    if result["success"]:
        print(f"✅ Guidelines retrieved for: {result['loan_type']}")
        print(f"\n{result['guidelines'][:500]}...")
        print(f"\nSources:")
        for s in result["sources"][:2]:
            print(f"  → {s['source_file']} (Page {s['page']})")
    else:
        print(f"❌ Error: {result['error']}")


if __name__ == "__main__":
    print("\n🏦 Testing All 5 MCP Tools")
    print("="*60)

    test_get_credit_score()
    test_get_loan_products()
    test_calculate_emi()
    test_check_cibil_eligibility()
    test_get_rbi_guidelines()   # Last — makes LLM call

    print("\n✅ All tool tests complete! Ready for Task 3.3 — MCP Server\n")