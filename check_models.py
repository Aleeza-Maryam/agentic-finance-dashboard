# check_models.py
from groq import Groq
from src.agentic_finance_dashboard.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

print("="*50)
print("Available Models on Groq")
print("="*50)

models = client.models.list()
for model in models.data:
    print(f"  - {model.id}")