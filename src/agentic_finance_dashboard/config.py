import os
from dotenv import load_dotenv

# .env file se API keys load karein
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def check_keys():
    """Check if API keys are set properly"""
    print(" Checking API keys...")
    
    if not GROQ_API_KEY:
        print(" GROQ_API_KEY not found in .env file")
        return False
    else:
        print(f" GROQ_API_KEY found: {GROQ_API_KEY[:10]}...")
    
    if not TAVILY_API_KEY:
        print(" TAVILY_API_KEY not found in .env file")
        return False
    else:
        print(f" TAVILY_API_KEY found: {TAVILY_API_KEY[:10]}...")
    
    print(" All API keys are set correctly!")
    return True

if __name__ == "__main__":
    check_keys()