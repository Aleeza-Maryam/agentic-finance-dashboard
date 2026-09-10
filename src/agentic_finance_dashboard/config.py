"""
Configuration Manager for AlphaSignal
Reads API keys from both .env (local) and Streamlit Secrets (deployed)
"""

import os
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

def get_api_key(key_name: str) -> str:
    """
    Get API key from Streamlit Secrets (deployed) or .env (local)
    """
    # Try Streamlit Secrets first (for deployed apps)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    
    # Fallback to environment variables (for local development)
    return os.getenv(key_name)

# Get API keys
GROQ_API_KEY = get_api_key("GROQ_API_KEY")
TAVILY_API_KEY = get_api_key("TAVILY_API_KEY")

def check_keys():
    """Check if API keys are set properly"""
    print(" Checking API keys...")
    
    if not GROQ_API_KEY:
        print(" GROQ_API_KEY not found")
        return False
    else:
        print(f" GROQ_API_KEY found: {GROQ_API_KEY[:10]}...")
    
    if not TAVILY_API_KEY:
        print(" TAVILY_API_KEY not found")
        return False
    else:
        print(f" TAVILY_API_KEY found: {TAVILY_API_KEY[:10]}...")
    
    print("All API keys are set correctly!")
    return True

if __name__ == "__main__":
    check_keys()