# test_llm.py
# Task 1.2 — Test basic LLM calling with prompt templates
# Run this file to verify your OpenAI connection is working

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

# ─── Step 1: Load environment variables ──────────────────────────────────────
load_dotenv()

# ─── Step 2: Initialise the LLM ──────────────────────────────────────────────
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    temperature=0.0,   # 0.0 = consistent, deterministic responses
    api_key=os.getenv("OPENAI_API_KEY")
)

# ─── Step 3: Simple direct call (no template) ────────────────────────────────
def test_simple_call():
    """
    Most basic LLM call — just send a message, get a response.
    This confirms your API key and connection are working.
    """
    print("\n" + "="*60)
    print("TEST 1: Simple Direct Call")
    print("="*60)

    response = llm.invoke("What is a CIBIL score in Indian banking?")
    print(response.content)


# ─── Step 4: Prompt Template call ────────────────────────────────────────────
def test_prompt_template():
    """
    Prompt templates let you create reusable prompts with variables.
    This is how all your agents will structure their prompts.
    {customer_name} and {loan_type} are placeholders filled at runtime.
    """
    print("\n" + "="*60)
    print("TEST 2: Prompt Template Call")
    print("="*60)

    # Define the prompt template with placeholders
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert loan eligibility advisor at an Indian bank.
            Your job is to explain loan eligibility criteria clearly and concisely.
            Always reference RBI guidelines where relevant."""
        ),
        (
            "human",
            """Customer Name: {customer_name}
            Loan Type Requested: {loan_type}
            
            Please explain the key eligibility criteria this customer 
            should be aware of for this loan type."""
        )
    ])

    # Chain: prompt → llm → parse output as string
    # The | symbol is LangChain's way of chaining components together
    chain = prompt | llm | StrOutputParser()

    # Invoke chain with actual values for placeholders
    response = chain.invoke({
        "customer_name": "Sireesha",
        "loan_type": "Home Loan"
    })

    print(response)


# ─── Step 5: Structured output call ──────────────────────────────────────────
def test_structured_prompt():
    """
    This shows how to get structured, consistent responses from the LLM.
    Your agents will use this pattern to pass outputs between each other.
    """
    print("\n" + "="*60)
    print("TEST 3: Structured Output Prompt")
    print("="*60)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a loan risk assessment agent.
            Always respond in this exact format:
            
            RISK_LEVEL: <Low/Medium/High>
            REASON: <one sentence explanation>
            RECOMMENDATION: <one sentence recommendation>"""
        ),
        (
            "human",
            """Assess the risk for this applicant:
            - Monthly Income: ₹{income}
            - Existing EMIs: ₹{existing_emi}
            - CIBIL Score: {cibil_score}
            - Loan Amount Requested: ₹{loan_amount}"""
        )
    ])

    chain = prompt | llm | StrOutputParser()

    response = chain.invoke({
        "income": "85000",
        "existing_emi": "15000",
        "cibil_score": "720",
        "loan_amount": "2500000"
    })

    print(response)


# ─── Run all tests ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🏦 Loan Eligibility Agent — LLM Connection Tests")
    print("Testing OpenAI connection and prompt templates...\n")

    try:
        test_simple_call()
        test_prompt_template()
        test_structured_prompt()
        print("\n✅ All tests passed! LLM connection is working correctly.")
        print("Ready to move to Task 1.3 — Mock Data Creation\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Check your OPENAI_API_KEY in the .env file")