# observability/langsmith_config.py
# Task 6.2 — LangSmith Observability
# Configures LangSmith tracing for the entire pipeline.
# LangSmith traces every LLM call, tool call, and agent step
# giving you a full audit trail of every loan assessment.
#
# Setup:
# 1. Go to smith.langchain.com → sign up free
# 2. Create a project called "loan-eligibility-agent"
# 3. Get your API key → add to .env as LANGCHAIN_API_KEY
# 4. Make sure .env has:
#    LANGCHAIN_TRACING_V2=true
#    LANGCHAIN_PROJECT=loan-eligibility-agent

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def setup_langsmith():
    """
    Verifies LangSmith environment variables are correctly set.
    LangSmith tracing is automatic once these are in .env —
    no code changes needed in agents or pipeline.
    """
    required_vars = {
        "LANGCHAIN_TRACING_V2": "true",
        "LANGCHAIN_API_KEY": None,
        "LANGCHAIN_PROJECT": "loan-eligibility-agent",
        "LANGCHAIN_ENDPOINT": "https://api.smith.langchain.com"
    }

    print("\n" + "="*60)
    print("🔍 LangSmith Observability Setup Check")
    print("="*60)

    all_good = True

    for var, expected in required_vars.items():
        value = os.getenv(var)
        if not value:
            print(f"  ❌ {var} — NOT SET in .env")
            all_good = False
        elif expected and value != expected:
            print(f"  ⚠️  {var} = '{value}' (expected '{expected}')")
        else:
            # Mask API key for security
            display = value[:8] + "..." if "KEY" in var else value
            print(f"  ✅ {var} = {display}")

    if all_good:
        print("\n✅ LangSmith is configured correctly!")
        print("   Every LLM call and agent step will be traced automatically.")
        print(f"   View traces at: https://smith.langchain.com")
        print(f"   Project: {os.getenv('LANGCHAIN_PROJECT')}")
    else:
        print("\n⚠️  Some variables are missing. Add them to your .env file.")
        print("   Get your API key from: https://smith.langchain.com")

    return all_good


def get_run_metadata(customer_name: str, loan_type: str) -> dict:
    """
    Returns metadata tags for each pipeline run.
    LangSmith attaches these to traces so you can filter
    and search runs by customer, loan type, etc.

    Usage: pass this to run_config in supervisor.py
    """
    return {
        "tags": ["loan-eligibility", loan_type.lower().replace(" ", "-")],
        "metadata": {
            "customer_name": customer_name,
            "loan_type": loan_type,
            "pipeline_version": "1.0"
        }
    }


if __name__ == "__main__":
    setup_langsmith()