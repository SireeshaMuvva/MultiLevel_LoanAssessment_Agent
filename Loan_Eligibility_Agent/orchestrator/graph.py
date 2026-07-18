# orchestrator/graph.py
# Task 5.1 — LangGraph State Graph
# Defines all agent nodes and the edges between them.
# This is where LangGraph takes over state passing between agents.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from orchestrator.state import LoanApplicationState
from Agents.l1_data_validation import validate_data_agent
from Agents.l1_rag_agent import rag_agent
from Agents.l1_risk_scoring import risk_scoring_agent
from Agents.l2_decision import decision_agent
from Agents.l2_counter_offer import counter_offer_agent
from Agents.l3_compliance import compliance_agent


def route_after_decision(state: LoanApplicationState) -> str:
    """
    Conditional routing function — called by LangGraph after
    the Decision Agent runs.

    If APPROVED  → skip counter-offer, go straight to compliance
    If REJECTED  → go to counter-offer first, then compliance
    """
    if state.get("decision") == "APPROVED":
        print("\n[Router] Decision: APPROVED → routing to L3 Compliance")
        return "l3_compliance"
    else:
        print("\n[Router] Decision: REJECTED → routing to L2 Counter-Offer")
        return "l2_counter_offer"


def build_graph():
    """
    Builds and compiles the full LangGraph workflow.

    Node order:
    l1_validation → l1_rag → l1_risk → l2_decision
                                              ↓
                              (APPROVED) l3_compliance
                              (REJECTED) l2_counter_offer → l3_compliance
                                              ↓
                                             END
    """
    # ── Step 1: Create the graph with our state schema ─────────────────────
    graph = StateGraph(LoanApplicationState)

    # ── Step 2: Add all agent nodes ────────────────────────────────────────
    # Each node is a name + the agent function to call
    graph.add_node("l1_validation",   validate_data_agent)
    graph.add_node("l1_rag",          rag_agent)
    graph.add_node("l1_risk",         risk_scoring_agent)
    graph.add_node("l2_decision",     decision_agent)
    graph.add_node("l2_counter_offer", counter_offer_agent)
    graph.add_node("l3_compliance",   compliance_agent)

    # ── Step 3: Set entry point ────────────────────────────────────────────
    # LangGraph starts here — first agent to run
    graph.set_entry_point("l1_validation")

    # ── Step 4: Add fixed edges (always follow this path) ─────────────────
    # L1 agents always run in sequence
    graph.add_edge("l1_validation", "l1_rag")
    graph.add_edge("l1_rag",        "l1_risk")
    graph.add_edge("l1_risk",       "l2_decision")

    # ── Step 5: Add conditional edge after Decision Agent ─────────────────
    # This is where LangGraph branches based on decision outcome
    graph.add_conditional_edges(
        "l2_decision",          # after this node runs...
        route_after_decision,   # call this function to decide next node
        {
            "l3_compliance":    "l3_compliance",    # APPROVED path
            "l2_counter_offer": "l2_counter_offer"  # REJECTED path
        }
    )

    # ── Step 6: Counter-offer always leads to compliance ──────────────────
    graph.add_edge("l2_counter_offer", "l3_compliance")

    # ── Step 7: Compliance is always the last agent ────────────────────────
    graph.add_edge("l3_compliance", END)

    # ── Step 8: Compile the graph ──────────────────────────────────────────
    app = graph.compile()
    print("✅ LangGraph compiled successfully")
    return app


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = build_graph()
    print("\nGraph nodes:", list(app.nodes))