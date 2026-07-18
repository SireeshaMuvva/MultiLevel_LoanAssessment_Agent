# llm_config.py
# Central place to initialise the LLM — all agents will import from here

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# Load API keys from .env file
load_dotenv()

def get_llm(temperature: float = 0.0) -> ChatOpenAI:
    """
    Returns a ChatOpenAI instance.
    temperature=0.0 means deterministic responses — important for
    financial decisions where consistency matters.
    """
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY")
    )