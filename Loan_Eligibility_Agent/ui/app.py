# ui/app.py
# Task 6.3 — Streamlit UI (Customer-facing, clean version)
# Run: streamlit run ui/app.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from orchestrator.supervisor import run_loan_assessment

st.set_page_config(
    page_title="LoanEligibility - Assessment",
    page_icon="🏦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background: #f7f8fa; }
    .bank-header { text-align:center; padding:2.5rem 1rem 1.5rem; border-bottom:1px solid #e5e7eb; margin-bottom:2rem; }
    .bank-logo { font-size:2rem; margin-bottom:0.5rem; }
    .bank-name { font-size:1.4rem; font-weight:600; color:#111827; letter-spacing:-0.02em; }
    .bank-tagline { font-size:0.85rem; color:#6b7280; margin-top:0.25rem; }
    .form-section { font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:0.1em; color:#9ca3af; margin:1.5rem 0 0.75rem; }
    .result-approved { background:#ecfdf5; border:1.5px solid #059669; border-radius:14px; padding:1.75rem; text-align:center; margin-bottom:1.5rem; }
    .result-approved .result-icon { font-size:2.5rem; }
    .result-approved .result-title { font-size:1.4rem; font-weight:600; color:#065f46; margin:0.5rem 0 0.25rem; }
    .result-approved .result-sub { font-size:0.9rem; color:#047857; }
    .result-rejected { background:#fff7ed; border:1.5px solid #d97706; border-radius:14px; padding:1.75rem; text-align:center; margin-bottom:1.5rem; }
    .result-rejected .result-icon { font-size:2.5rem; }
    .result-rejected .result-title { font-size:1.4rem; font-weight:600; color:#92400e; margin:0.5rem 0 0.25rem; }
    .result-rejected .result-sub { font-size:0.9rem; color:#b45309; }
    .stat-box { background:white; border:1px solid #e5e7eb; border-radius:12px; padding:1rem; text-align:center; }
    .stat-value { font-size:1.4rem; font-weight:600; color:#111827; line-height:1.2; }
    .stat-label { font-size:0.72rem; color:#9ca3af; margin-top:0.2rem; text-transform:uppercase; letter-spacing:0.05em; }
    .offer-card { background:white; border:1px solid #e5e7eb; border-radius:14px; padding:1.5rem; margin:1rem 0; }
    .offer-title { font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; color:#6b7280; margin-bottom:1rem; }
    .counter-card { background:#fffbeb; border:1.5px solid #fcd34d; border-radius:14px; padding:1.5rem; margin:1rem 0; }
    .counter-title { font-size:0.85rem; font-weight:600; color:#92400e; margin-bottom:0.5rem; }
    .counter-body { font-size:0.85rem; color:#78350f; line-height:1.6; }
    .letter-box { background:#f9fafb; border:1px solid #e5e7eb; border-radius:12px; padding:1.5rem; font-size:0.88rem; line-height:1.75; color:#374151; white-space:pre-wrap; }
    .rbi-note { font-size:0.75rem; color:#9ca3af; text-align:center; margin-top:1rem; padding-top:1rem; border-top:1px solid #f3f4f6; }
    .stButton > button { background:#111827 !important; color:white !important; border:none !important; border-radius:10px !important; padding:0.7rem 2rem !important; font-size:0.95rem !important; font-weight:500 !important; width:100% !important; margin-top:1rem; }
    .stButton > button:hover { opacity:0.85 !important; }
    #MainMenu, footer, .stDeployButton { display:none !important; }
    header { visibility:hidden !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="bank-header">
    <div class="bank-logo">🏦</div>
    <div class="bank-name">Loan Eligibity</div>
    <div class="bank-tagline">Check your loan eligibility in seconds</div>
</div>
""", unsafe_allow_html=True)

SAMPLES = {
    "— Try a sample application —": None,
    "Rajesh Kumar · Home Loan · ₹45,00,000": {
        "customer_id":"CUST001","pan_number":"ABCDE1234F","full_name":"Rajesh Kumar",
        "age":35,"employment_type":"Salaried","monthly_income":85000,
        "monthly_expenses":30000,"existing_emis":12000,
        "loan_type_requested":"Home Loan","loan_amount_requested":4500000,
        "loan_tenure_years":20,"city":"Bengaluru"
    },
    "Anita Desai · Car Loan · ₹8,00,000": {
        "customer_id":"CUST004","pan_number":"FGHIJ3456K","full_name":"Anita Desai",
        "age":27,"employment_type":"Salaried","monthly_income":45000,
        "monthly_expenses":18000,"existing_emis":0,
        "loan_type_requested":"Car Loan","loan_amount_requested":800000,
        "loan_tenure_years":5,"city":"Pune"
    },
    "Mohammed Irfan · Home Loan · ₹30,00,000": {
        "customer_id":"CUST005","pan_number":"UVWXY7890L","full_name":"Mohammed Irfan",
        "age":38,"employment_type":"Self-Employed","monthly_income":40000,
        "monthly_expenses":22000,"existing_emis":15000,
        "loan_type_requested":"Home Loan","loan_amount_requested":3000000,
        "loan_tenure_years":15,"city":"Chennai"
    }
}

sample_choice = st.selectbox("Load a sample", list(SAMPLES.keys()), label_visibility="collapsed")
sample = SAMPLES[sample_choice]

st.markdown('<div class="form-section">Your details</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    full_name = st.text_input("Full name", value=sample["full_name"] if sample else "", placeholder="e.g. Priya Sharma")
with c2:
    pan = st.text_input("PAN number", value=sample["pan_number"] if sample else "", placeholder="e.g. ABCDE1234F")

c3, c4 = st.columns(2)
with c3:
    age = st.number_input("Age", min_value=18, max_value=75, value=sample["age"] if sample else 30)
with c4:
    city = st.text_input("City", value=sample["city"] if sample else "", placeholder="e.g. Mumbai")

employment = st.selectbox("Employment type", ["Salaried", "Self-Employed"],
    index=0 if not sample else (0 if sample["employment_type"] == "Salaried" else 1))

st.markdown('<div class="form-section">Your income</div>', unsafe_allow_html=True)
c5, c6 = st.columns(2)
with c5:
    income = st.number_input("Monthly income (₹)", min_value=0, step=1000, value=sample["monthly_income"] if sample else 50000)
    expenses = st.number_input("Monthly expenses (₹)", min_value=0, step=500, value=sample["monthly_expenses"] if sample else 20000)
with c6:
    emis = st.number_input("Existing loan EMIs (₹)", min_value=0, step=500, value=sample["existing_emis"] if sample else 0)
    st.caption("Total monthly repayments on any existing loans")

st.markdown('<div class="form-section">Loan you need</div>', unsafe_allow_html=True)
loan_types = ["Home Loan", "Car Loan", "Personal Loan", "Business Loan"]
loan_type = st.selectbox("Type of loan", loan_types,
    index=loan_types.index(sample["loan_type_requested"]) if sample else 0)

c7, c8 = st.columns(2)
with c7:
    amount = st.number_input("Amount needed (₹)", min_value=50000, step=50000, value=sample["loan_amount_requested"] if sample else 1000000)
with c8:
    tenure = st.number_input("Repayment period (years)", min_value=1, max_value=30, value=sample["loan_tenure_years"] if sample else 5)

submitted = st.button("Check my eligibility →")

if submitted:
    if not full_name or not pan:
        st.warning("Please enter your name and PAN number to continue.")
        st.stop()

    customer = {
        "customer_id": f"CUST-{pan[-4:]}",
        "pan_number": pan, "full_name": full_name, "age": int(age),
        "employment_type": employment, "monthly_income": float(income),
        "monthly_expenses": float(expenses), "existing_emis": float(emis),
        "loan_type_requested": loan_type, "loan_amount_requested": float(amount),
        "loan_tenure_years": int(tenure), "city": city
    }

    with st.spinner("Checking your eligibility — this takes about 30 seconds..."):
        try:
            result = run_loan_assessment(customer)
        except Exception as e:
            st.error(f"Something went wrong. Please try again. ({str(e)})")
            st.stop()

    decision = result.get("decision", "REJECTED")
    st.divider()

    if decision == "APPROVED":
        st.markdown(f"""
        <div class="result-approved">
            <div class="result-icon">✅</div>
            <div class="result-title">You're eligible!</div>
            <div class="result-sub">Great news, {full_name.split()[0]}. Your {loan_type} application looks good.</div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="offer-card"><div class="offer-title">Your loan offer</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="stat-box"><div class="stat-value">₹{result.get("approved_amount", amount):,.0f}</div><div class="stat-label">Loan amount</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="stat-box"><div class="stat-value">{result.get("approved_rate", 0)}%</div><div class="stat-label">Interest rate / year</div></div>', unsafe_allow_html=True)
        with col3:
            emi = result.get("monthly_emi", 0)
            st.markdown(f'<div class="stat-box"><div class="stat-value">₹{emi:,.0f}</div><div class="stat-label">Monthly repayment</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if result.get("best_bank"):
            st.markdown(f"Recommended bank: **{result['best_bank']}**")
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown(f"""
        <div class="result-rejected">
            <div class="result-icon">📋</div>
            <div class="result-title">Not eligible right now</div>
            <div class="result-sub">We couldn't approve this application today, but here's what you can do.</div>
        </div>""", unsafe_allow_html=True)

        if result.get("counter_offer_available") and result.get("counter_offer_amount"):
            co_amount = result["counter_offer_amount"]
            co_emi = result.get("counter_offer_emi", 0)
            st.markdown(f"""
            <div class="counter-card">
                <div class="counter-title">💡 You may qualify for a smaller amount</div>
                <div class="counter-body">
                    Based on your income and existing commitments, you could be eligible for up to
                    <strong>₹{co_amount:,.0f}</strong> with a monthly repayment of
                    <strong>₹{co_emi:,.0f}</strong>.<br><br>
                    Interested? Visit your nearest branch or call us at <strong>1800-XXX-XXXX</strong>.
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Read your full assessment letter"):
        st.markdown(f'<div class="letter-box">{result.get("final_response", "")}</div>', unsafe_allow_html=True)

    rbi_sources = result.get("rbi_sources", [])
    sources = list({s.get("source_file", "") for s in rbi_sources if s.get("source_file")})
    source_text = f"Assessment references: {', '.join(sources)}" if sources else ""

    st.markdown(f"""
    <div class="rbi-note">
        This assessment is indicative only. Final approval is subject to bank verification and documentation.<br>
        {source_text}
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**What happens next?**")
    if decision == "APPROVED":
        st.markdown("""
1. Visit your nearest IndiaFirst Bank branch with your documents
2. Submit PAN, Aadhaar, salary slips, and 6 months' bank statements
3. Our team processes your application within 15 working days
4. Loan amount is credited directly to your account
        """)
    else:
        st.markdown("""
1. Read the assessment letter for specific reasons
2. Work on improving your credit score if it's below 700
3. Try to reduce existing EMIs before reapplying
4. Speak to an advisor at any branch for personalised guidance
        """)

    st.markdown("<br><center style='color:#9ca3af; font-size:0.75rem'>IndiaFirst Bank · For demonstration purposes only</center>", unsafe_allow_html=True)