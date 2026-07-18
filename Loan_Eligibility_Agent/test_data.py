# test_data.py
# Quick script to verify all mock data loads correctly
# Run: python test_data.py

import json
import os

def load_json(filepath: str) -> dict:
    with open(filepath, "r") as f:
        return json.load(f)

def test_customers():
    print("\n" + "="*60)
    print("TEST 1: Customers Data")
    print("="*60)
    data = load_json("data/mock/customers.json")
    customers = data["customers"]
    print(f"✅ Total customers loaded: {len(customers)}")
    for c in customers:
        print(f"   → {c['full_name']} | {c['loan_type_requested']} | ₹{c['loan_amount_requested']:,} | CIBIL: {c['credit_score']}")

def test_credit_scores():
    print("\n" + "="*60)
    print("TEST 2: Credit Scores Data")
    print("="*60)
    data = load_json("data/mock/credit_scores.json")
    scores = data["credit_scores"]
    print(f"✅ Total credit records loaded: {len(scores)}")
    for s in scores:
        print(f"   → {s['customer_name']} | Score: {s['cibil_score']} | Rating: {s['credit_rating']}")

def test_loan_products():
    print("\n" + "="*60)
    print("TEST 3: Loan Products Data")
    print("="*60)
    data = load_json("data/mock/loan_products.json")
    products = data["loan_products"]
    print(f"✅ Total loan products loaded: {len(products)}")
    for p in products:
        print(f"   → {p['bank_name']} | {p['loan_type']} | Rate: {p['interest_rate_percent']}% | Min CIBIL: {p['eligibility']['min_cibil_score']}")

def test_lookup():
    """
    Simulates what the MCP tools will do in Week 3 —
    look up a customer's credit score by PAN number
    """
    print("\n" + "="*60)
    print("TEST 4: Simulated Tool Lookup (PAN → Credit Score)")
    print("="*60)
    pan_to_lookup = "ABCDE1234F"
    data = load_json("data/mock/credit_scores.json")
    scores = data["credit_scores"]

    result = next((s for s in scores if s["pan_number"] == pan_to_lookup), None)

    if result:
        print(f"✅ Found credit record for PAN: {pan_to_lookup}")
        print(f"   Name    : {result['customer_name']}")
        print(f"   Score   : {result['cibil_score']}")
        print(f"   Rating  : {result['credit_rating']}")
        print(f"   Defaults: {result['defaults_last_7_years']}")
    else:
        print(f"❌ No record found for PAN: {pan_to_lookup}")

if __name__ == "__main__":
    print("\n🏦 Loan Eligibility Agent — Mock Data Tests")
    test_customers()
    test_credit_scores()
    test_loan_products()
    test_lookup()
    print("\n✅ All data loaded successfully! Ready for Task 2.1\n")