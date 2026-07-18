# mcp_server/tools.py
# Task 3.1 — All 5 tools your agents will use
# Each tool is a plain Python function first — MCP wrapping comes in Task 3.3

import json
import os
from datetime import datetime


# ─── Helper: Load mock data files ────────────────────────────────────────────

def _load_json(filename: str) -> dict:
    """Loads a mock data JSON file from the data/mock directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = os.path.join(base_dir, "data", "mock", filename)
    with open(filepath, "r") as f:
        return json.load(f)


# ─── Tool 1: get_credit_score ─────────────────────────────────────────────────

def get_credit_score(pan_number: str) -> dict:
    """
    Fetches the CIBIL credit score and credit history for a customer
    based on their PAN number.

    In production: this would call a real CIBIL/Experian API.
    In our project: reads from mock credit_scores.json.

    Args:
        pan_number: Customer's PAN card number (e.g. "ABCDE1234F")

    Returns:
        dict with cibil_score, credit_rating, defaults, late payments etc.
    """
    data = _load_json("credit_scores.json")
    scores = data["credit_scores"]

    record = next(
        (s for s in scores if s["pan_number"].upper() == pan_number.upper()),
        None
    )

    if not record:
        return {
            "success": False,
            "error": f"No credit record found for PAN: {pan_number}",
            "pan_number": pan_number
        }

    return {
        "success": True,
        "pan_number": pan_number,
        "customer_name": record["customer_name"],
        "cibil_score": record["cibil_score"],
        "credit_rating": record["credit_rating"],
        "credit_utilization_percent": record["credit_utilization_percent"],
        "active_loans": record["active_loans"],
        "loan_repayment_history": record["loan_repayment_history"],
        "defaults_last_7_years": record["defaults_last_7_years"],
        "late_payments_last_12_months": record["late_payments_last_12_months"],
        "credit_age_years": record["credit_age_years"],
        "last_updated": record["last_updated"]
    }


# ─── Tool 2: get_rbi_guidelines ───────────────────────────────────────────────

def get_rbi_guidelines(loan_type: str) -> dict:
    """
    Retrieves relevant RBI guidelines for a specific loan type
    using the RAG pipeline built in Week 2.

    Args:
        loan_type: Type of loan (e.g. "Home Loan", "Personal Loan",
                   "Business Loan", "Car Loan")

    Returns:
        dict with relevant guideline text and source citations
    """
    try:
        # Import RAG components — built in Week 2
        import sys
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, base_dir)

        from rag.embeddings import load_vector_store
        from rag.retriever import get_retriever, build_rag_chain, retrieve_with_sources
        from llm_config import get_llm

        vector_store = load_vector_store()
        retriever = get_retriever(vector_store)
        llm = get_llm()
        rag_chain = build_rag_chain(retriever, llm)

        query = f"What are the RBI eligibility guidelines and requirements for {loan_type}?"
        answer = rag_chain.invoke(query)
        _, sources = retrieve_with_sources(retriever, query)

        return {
            "success": True,
            "loan_type": loan_type,
            "guidelines": answer,
            "sources": sources
        }

    except Exception as e:
        return {
            "success": False,
            "loan_type": loan_type,
            "error": str(e)
        }


# ─── Tool 3: get_loan_products ────────────────────────────────────────────────

def get_loan_products(loan_type: str, min_cibil_score: int = 0) -> dict:
    """
    Returns available loan products for a given loan type,
    optionally filtered by the customer's CIBIL score.

    Args:
        loan_type: Type of loan requested (e.g. "Home Loan")
        min_cibil_score: Customer's CIBIL score to filter eligible products

    Returns:
        dict with list of matching loan products and their terms
    """
    data = _load_json("loan_products.json")
    products = data["loan_products"]

    # Filter by loan type
    matching = [
        p for p in products
        if p["loan_type"].lower() == loan_type.lower()
    ]

    if not matching:
        return {
            "success": False,
            "loan_type": loan_type,
            "error": f"No products found for loan type: {loan_type}"
        }

    # Filter by CIBIL score if provided
    if min_cibil_score > 0:
        eligible = [
            p for p in matching
            if p["eligibility"]["min_cibil_score"] <= min_cibil_score
        ]
    else:
        eligible = matching

    return {
        "success": True,
        "loan_type": loan_type,
        "total_products_found": len(matching),
        "eligible_products": len(eligible),
        "products": eligible,
        "note": f"Filtered for CIBIL score: {min_cibil_score}" if min_cibil_score > 0 else "No CIBIL filter applied"
    }


# ─── Tool 4: calculate_emi ────────────────────────────────────────────────────

def calculate_emi(
    principal: float,
    annual_interest_rate: float,
    tenure_years: int
) -> dict:
    """
    Calculates the monthly EMI using the standard reducing balance formula.
    This is the same formula all Indian banks use.

    Formula: EMI = P × r × (1+r)^n / ((1+r)^n - 1)
    Where:
        P = Principal loan amount
        r = Monthly interest rate (annual rate / 12 / 100)
        n = Total number of months

    Args:
        principal: Loan amount in rupees (e.g. 4500000)
        annual_interest_rate: Interest rate per year in % (e.g. 8.5)
        tenure_years: Loan tenure in years (e.g. 20)

    Returns:
        dict with monthly EMI, total payment, total interest
    """
    if principal <= 0 or annual_interest_rate <= 0 or tenure_years <= 0:
        return {
            "success": False,
            "error": "Principal, interest rate and tenure must all be positive values"
        }

    monthly_rate = annual_interest_rate / 12 / 100
    n_months = tenure_years * 12

    # EMI formula
    emi = principal * monthly_rate * (1 + monthly_rate) ** n_months / \
          ((1 + monthly_rate) ** n_months - 1)

    total_payment = emi * n_months
    total_interest = total_payment - principal

    return {
        "success": True,
        "principal": round(principal, 2),
        "annual_interest_rate_percent": annual_interest_rate,
        "tenure_years": tenure_years,
        "tenure_months": n_months,
        "monthly_emi": round(emi, 2),
        "total_payment": round(total_payment, 2),
        "total_interest_paid": round(total_interest, 2),
        "interest_to_principal_ratio": round(total_interest / principal, 2)
    }


# ─── Tool 5: check_cibil_eligibility ─────────────────────────────────────────

def check_cibil_eligibility(
    cibil_score: int,
    monthly_income: float,
    existing_emis: float,
    requested_loan_amount: float,
    loan_type: str,
    tenure_years: int
) -> dict:
    """
    Checks whether a customer is eligible based on CIBIL score and FOIR.

    FOIR (Fixed Obligation to Income Ratio) = 
        (existing EMIs + new EMI) / monthly income × 100

    RBI recommends FOIR should not exceed:
    - 50% for salaried borrowers
    - 60% for self-employed borrowers

    Args:
        cibil_score: Customer's CIBIL score
        monthly_income: Gross monthly income in rupees
        existing_emis: Total existing monthly EMI obligations
        requested_loan_amount: Loan amount requested in rupees
        loan_type: Type of loan (for fetching interest rate)
        tenure_years: Requested loan tenure

    Returns:
        dict with eligibility decision, FOIR calculation, and reasons
    """
    issues = []
    passed_checks = []

    # ── Step 1: CIBIL score check ──
    if cibil_score >= 750:
        cibil_status = "Excellent"
        passed_checks.append(f"CIBIL score {cibil_score} is Excellent (750+)")
    elif cibil_score >= 700:
        cibil_status = "Good"
        passed_checks.append(f"CIBIL score {cibil_score} is Good (700-749)")
    elif cibil_score >= 650:
        cibil_status = "Fair"
        passed_checks.append(f"CIBIL score {cibil_score} is Fair (650-699) — higher rate may apply")
    elif cibil_score >= 600:
        cibil_status = "Average"
        issues.append(f"CIBIL score {cibil_score} is Average (600-649) — additional scrutiny required")
    else:
        cibil_status = "Poor"
        issues.append(f"CIBIL score {cibil_score} is Poor (below 600) — high rejection risk")

    # ── Step 2: Get product interest rate for EMI calculation ──
    products_result = get_loan_products(loan_type, cibil_score)

    if products_result["success"] and products_result["eligible_products"] > 0:
        # Use the best available rate from eligible products
        best_product = products_result["products"][0]
        interest_rate = best_product["interest_rate_percent"]
        bank_name = best_product["bank_name"]
    else:
        # Default rate if no specific product found
        interest_rate = 12.0
        bank_name = "Standard Rate"

    # ── Step 3: Calculate new EMI ──
    emi_result = calculate_emi(requested_loan_amount, interest_rate, tenure_years)

    if not emi_result["success"]:
        return {"success": False, "error": "Could not calculate EMI"}

    new_emi = emi_result["monthly_emi"]

    # ── Step 4: FOIR calculation ──
    total_obligations = existing_emis + new_emi
    foir = (total_obligations / monthly_income) * 100
    foir_limit = 50.0  # RBI recommended limit for salaried

    if foir <= foir_limit:
        passed_checks.append(
            f"FOIR is {foir:.1f}% — within RBI recommended limit of {foir_limit}%"
        )
    else:
        issues.append(
            f"FOIR is {foir:.1f}% — exceeds RBI recommended limit of {foir_limit}%. "
            f"Max affordable EMI at {foir_limit}% FOIR: ₹{(monthly_income * foir_limit/100) - existing_emis:,.0f}"
        )

    # ── Step 5: Final eligibility decision ──
    is_eligible = len(issues) == 0

    # Calculate max eligible loan amount if rejected
    max_affordable_emi = (monthly_income * foir_limit / 100) - existing_emis
    max_loan_result = None
    if not is_eligible and max_affordable_emi > 0:
        # Back-calculate max principal from affordable EMI
        monthly_rate = interest_rate / 12 / 100
        n = tenure_years * 12
        if monthly_rate > 0:
            max_principal = max_affordable_emi * \
                ((1 + monthly_rate) ** n - 1) / \
                (monthly_rate * (1 + monthly_rate) ** n)
            max_loan_result = round(max_principal, 0)

    return {
        "success": True,
        "is_eligible": is_eligible,
        "decision": "APPROVED" if is_eligible else "REJECTED",
        "cibil_score": cibil_score,
        "cibil_status": cibil_status,
        "monthly_income": monthly_income,
        "existing_emis": existing_emis,
        "new_emi": round(new_emi, 2),
        "total_obligations": round(total_obligations, 2),
        "foir_percent": round(foir, 2),
        "foir_limit_percent": foir_limit,
        "interest_rate_used": interest_rate,
        "best_bank": bank_name,
        "passed_checks": passed_checks,
        "issues_found": issues,
        "max_eligible_loan_amount": max_loan_result,
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }