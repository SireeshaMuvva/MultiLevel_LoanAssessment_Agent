# 🏦 Multi-Level Loan Eligibility & Risk Assessment Agent

A production-grade multi-agent AI system that evaluates loan applications using LLMs, RAG over RBI guidelines, MCP tools, and a LangGraph supervisor architecture.

Built as a GenAI capstone project by Sireesha — transitioning from Pega CDH to GenAI Solutions Engineering.

---

## 🏗️ Architecture

```
User Input (Financial Profile)
        ↓
  [MCP Server] — 5 tools exposed via Model Context Protocol
  get_credit_score · get_rbi_guidelines · get_loan_products · calculate_emi · check_cibil_eligibility
        ↓
  [Supervisor Orchestrator] — LangGraph StateGraph
        ↓
  ┌─────────────────────────────────────────────┐
  │              Multi-Level Agents              │
  ├─────────────────────────────────────────────┤
  │  L1  Data Validation Agent                  │
  │  L1  RAG Agent (RBI guideline retrieval)    │
  │  L1  Risk Scoring Agent (CIBIL + FOIR)      │
  │                                             │
  │  L2  Decision Agent (approve / reject)      │
  │  L2  Counter-Offer Agent (if rejected)      │
  │                                             │
  │  L3  Compliance Agent (RBI final check)     │
  └─────────────────────────────────────────────┘
        ↓
  Final Response + RBI Citations
  Traced via LangSmith · Evaluated via RAGAS
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| LLM Framework | LangChain |
| Agent Orchestration | LangGraph (Supervisor pattern) |
| RAG | ChromaDB + OpenAI Embeddings |
| Tool Protocol | MCP (Model Context Protocol) |
| Evaluation | RAGAS (Faithfulness, Answer Relevancy, Context Precision) |
| Observability | LangSmith |
| UI | Streamlit |
| LLM | OpenAI GPT-4o-mini |

---

## 📁 Project Structure

```
loan_eligibility_agent/
├── data/
│   ├── mock/                    # customers, credit scores, loan products JSON
│   └── documents/rbi_guidelines/ # 3 RBI guideline PDFs for RAG
├── mcp_server/
│   ├── tools.py                 # 5 tool functions
│   └── server.py                # FastMCP server
├── rag/
│   ├── loader.py                # PDF loading & chunking
│   ├── embeddings.py            # ChromaDB vector store
│   └── retriever.py             # RAG chain with citations
├── agents/
│   ├── l1_data_validation.py    # L1: validates input
│   ├── l1_rag_agent.py          # L1: retrieves RBI guidelines
│   ├── l1_risk_scoring.py       # L1: CIBIL + FOIR assessment
│   ├── l2_decision.py           # L2: approve / reject decision
│   ├── l2_counter_offer.py      # L2: alternative offer if rejected
│   └── l3_compliance.py         # L3: final RBI compliance check
├── orchestrator/
│   ├── state.py                 # Shared LangGraph state schema
│   ├── graph.py                 # StateGraph nodes + edges
│   └── supervisor.py            # Main pipeline entry point
├── evaluation/
│   ├── test_dataset.json        # 25 RBI Q&A pairs
│   └── ragas_eval.py            # RAGAS evaluation script
├── observability/
│   └── langsmith_config.py      # LangSmith setup + run metadata
├── ui/
│   └── app.py                   # Streamlit customer-facing UI
├── llm_config.py                # Centralised LLM initialisation
├── test_pipeline.py             # Full end-to-end test (all 5 customers)
└── requirements.txt
```

---

## 🚀 Setup

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/loan-eligibility-agent.git
cd loan-eligibility-agent

# 2. Create virtual environment
uv venv
source .venv/bin/activate

# 3. Install dependencies
uv pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env — add OPENAI_API_KEY and LANGCHAIN_API_KEY

# 5. Build the RAG vector store (one time only)
python -m rag.embeddings

# 6. Run the Streamlit UI
streamlit run ui/app.py
```

---

## 🧪 Testing

```bash
# Test LLM connection
python -m test_llm

# Test mock data
python -m test_data

# Test all 5 MCP tools
python -m mcp_server.test_tools

# Test individual agents
python -m agents.l1_data_validation
python -m agents.l1_rag_agent
python -m agents.l1_risk_scoring
python -m agents.l2_decision
python -m agents.l2_counter_offer
python -m agents.l3_compliance

# Full end-to-end pipeline test
python -m test_pipeline

# RAGAS evaluation
python -m evaluation.ragas_eval
```

---

## 📊 Evaluation Results

| Metric | Score | What it measures |
|---|---|---|
| Faithfulness | TBD | No hallucination — answers grounded in RBI docs |
| Answer Relevancy | TBD | Answers actually address the question asked |
| Context Precision | TBD | Retrieved chunks are relevant to the query |

---

## 🏦 How It Works (Plain English)

1. **You submit your details** — name, income, existing EMIs, loan amount needed
2. **We validate your input** — check age, income, and other basics
3. **We look up RBI rules** — retrieve the regulations for your loan type
4. **We check your credit** — fetch your CIBIL score and calculate your FOIR
5. **We make a decision** — approve or reject based on all the above
6. **If rejected, we offer an alternative** — the maximum you do qualify for
7. **Final compliance check** — ensure the decision follows RBI guidelines
8. **You see the result** — clear, plain-English response with next steps

---

## 👤 Author

Sireesha — Pega CDH Developer transitioning to GenAI Solutions Engineering.
8.5 years in enterprise AI decisioning → building modern LLM-based systems.

---

## ⚠️ Disclaimer

This project is for educational and demonstration purposes only.
All RBI guideline documents are mock/educational content based on publicly known lending principles.
Not intended for actual loan decisioning.