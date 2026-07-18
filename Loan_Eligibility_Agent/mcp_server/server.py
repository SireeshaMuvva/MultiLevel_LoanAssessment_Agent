# mcp_server/server.py
# Task 3.3 — MCP Server wrapping all 5 tools
# MCP (Model Context Protocol) is an open standard by Anthropic that lets
# any LLM-compatible client discover and call your tools in a standard way.
#
# Run the server: python -m mcp_server.server
# The server runs locally and agents connect to it via MCP protocol.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from mcp_server.tools import (
    get_credit_score,
    get_rbi_guidelines,
    get_loan_products,
    calculate_emi,
    check_cibil_eligibility
)

# ─── Initialise MCP Server ────────────────────────────────────────────────────
# "loan-eligibility-agent" is the server name — clients use this to identify it
mcp = FastMCP("loan-eligibility-agent")


# ─── Register Tool 1: get_credit_score ───────────────────────────────────────
@mcp.tool()
def tool_get_credit_score(pan_number: str) -> dict:
    """
    Fetch CIBIL credit score and full credit history for a customer
    using their PAN card number.

    Use this tool when you need to assess a customer's creditworthiness
    before making a loan eligibility decision.

    Args:
        pan_number: Customer's PAN card number (e.g. ABCDE1234F)

    Returns:
        CIBIL score, credit rating, defaults, late payments, credit age
    """
    return get_credit_score(pan_number)


# ─── Register Tool 2: get_rbi_guidelines ─────────────────────────────────────
@mcp.tool()
def tool_get_rbi_guidelines(loan_type: str) -> dict:
    """
    Retrieve relevant RBI regulatory guidelines for a specific loan type
    using RAG over official RBI policy documents.

    Use this tool when you need to check regulatory requirements,
    eligibility norms, or compliance rules for any loan type.

    Args:
        loan_type: Type of loan — "Home Loan", "Personal Loan",
                   "Business Loan", or "Car Loan"

    Returns:
        Relevant RBI guideline text with source document citations
    """
    return get_rbi_guidelines(loan_type)


# ─── Register Tool 3: get_loan_products ──────────────────────────────────────
@mcp.tool()
def tool_get_loan_products(loan_type: str, min_cibil_score: int = 0) -> dict:
    """
    Get available bank loan products for a given loan type,
    filtered by the customer's CIBIL score eligibility.

    Use this tool when you need to find which bank products a customer
    qualifies for, and what interest rates apply to them.

    Args:
        loan_type: Type of loan requested
        min_cibil_score: Customer's CIBIL score to filter eligible products
                         (pass 0 to get all products without filtering)

    Returns:
        List of eligible loan products with rates, limits and requirements
    """
    return get_loan_products(loan_type, min_cibil_score)


# ─── Register Tool 4: calculate_emi ──────────────────────────────────────────
@mcp.tool()
def tool_calculate_emi(
    principal: float,
    annual_interest_rate: float,
    tenure_years: int
) -> dict:
    """
    Calculate monthly EMI using the standard reducing balance formula
    used by all Indian banks, as per RBI guidelines.

    Use this tool whenever you need to compute the monthly repayment
    obligation for a loan amount, rate, and tenure combination.

    Args:
        principal: Loan amount in rupees (e.g. 4500000)
        annual_interest_rate: Annual interest rate as percentage (e.g. 8.5)
        tenure_years: Loan repayment period in years (e.g. 20)

    Returns:
        Monthly EMI, total payment amount, and total interest paid
    """
    return calculate_emi(principal, annual_interest_rate, tenure_years)


# ─── Register Tool 5: check_cibil_eligibility ────────────────────────────────
@mcp.tool()
def tool_check_cibil_eligibility(
    cibil_score: int,
    monthly_income: float,
    existing_emis: float,
    requested_loan_amount: float,
    loan_type: str,
    tenure_years: int
) -> dict:
    """
    Perform a comprehensive loan eligibility check based on CIBIL score
    and FOIR (Fixed Obligation to Income Ratio) as per RBI guidelines.

    Use this tool for the final eligibility assessment. It checks:
    - CIBIL score against minimum thresholds
    - FOIR against RBI recommended limits (50% for salaried)
    - Calculates maximum eligible loan amount if rejected

    Args:
        cibil_score: Customer's CIBIL score
        monthly_income: Gross monthly income in rupees
        existing_emis: Total existing monthly EMI obligations in rupees
        requested_loan_amount: Loan amount requested in rupees
        loan_type: Type of loan requested
        tenure_years: Requested loan tenure in years

    Returns:
        Eligibility decision (APPROVED/REJECTED), FOIR details,
        issues found, and maximum eligible loan amount if rejected
    """
    return check_cibil_eligibility(
        cibil_score,
        monthly_income,
        existing_emis,
        requested_loan_amount,
        loan_type,
        tenure_years
    )


# ─── Run Server ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 Starting Loan Eligibility MCP Server...")
    print("   Server name : loan-eligibility-agent")
    print("   Tools       : 5 registered")
    print("   Transport   : stdio (standard MCP transport)")
    print("\n   Tools available:")
    print("   1. tool_get_credit_score")
    print("   2. tool_get_rbi_guidelines")
    print("   3. tool_get_loan_products")
    print("   4. tool_calculate_emi")
    print("   5. tool_check_cibil_eligibility")
    print("\n   Server running... (Ctrl+C to stop)\n")

    mcp.run(transport="stdio")