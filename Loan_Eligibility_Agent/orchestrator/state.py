# orchestrator/state.py
# Shared state schema — the "memory" that flows between all agents
# Every agent reads from this state and writes its output back to it
# LangGraph passes this state automatically between agent nodes

from typing import TypedDict, Optional, List


class LoanApplicationState(TypedDict):
    """
    Shared state for the entire loan eligibility workflow.
    Each agent reads what it needs and adds its output.
    The Supervisor Orchestrator manages the flow between agents.
    """

    # ── Customer Input (set at the start, never changed) ──────────────────
    customer_id: str
    pan_number: str
    full_name: str
    age: int
    employment_type: str           # "Salaried" or "Self-Employed"
    monthly_income: float
    monthly_expenses: float
    existing_emis: float
    loan_type_requested: str       # "Home Loan", "Personal Loan", etc.
    loan_amount_requested: float
    loan_tenure_years: int
    city: str

    # ── L1: Data Validation Agent Output ──────────────────────────────────
    validation_passed: Optional[bool]
    validation_errors: Optional[List[str]]
    validation_notes: Optional[str]

    # ── L1: RAG Agent Output ───────────────────────────────────────────────
    rbi_guidelines: Optional[str]
    rbi_sources: Optional[List[dict]]

    # ── L1: Risk Scoring Agent Output ─────────────────────────────────────
    cibil_score: Optional[int]
    credit_rating: Optional[str]
    risk_level: Optional[str]          # "Low", "Medium", "High"
    risk_reasons: Optional[List[str]]
    foir_percent: Optional[float]
    monthly_emi: Optional[float]

    # ── L2: Decision Agent Output ──────────────────────────────────────────
    decision: Optional[str]            # "APPROVED" or "REJECTED"
    decision_reason: Optional[str]
    approved_amount: Optional[float]
    approved_rate: Optional[float]
    approved_tenure: Optional[int]
    best_bank: Optional[str]

    # ── L2: Counter-Offer Agent Output ────────────────────────────────────
    counter_offer_available: Optional[bool]
    counter_offer_amount: Optional[float]
    counter_offer_tenure: Optional[int]
    counter_offer_emi: Optional[float]
    counter_offer_explanation: Optional[str]

    # ── L3: Compliance Agent Output ───────────────────────────────────────
    compliance_passed: Optional[bool]
    compliance_notes: Optional[str]
    compliance_violations: Optional[List[str]]

    # ── Final Response ─────────────────────────────────────────────────────
    final_response: Optional[str]

    # ── Workflow Control ───────────────────────────────────────────────────
    current_agent: Optional[str]       # tracks which agent is running
    errors: Optional[List[str]]        # any errors encountered
    next_agent: Optional[str]          # supervisor uses this for routing