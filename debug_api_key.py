#!/usr/bin/env python3
"""
Debug API key loading
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Check API keys
openai_key = os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

print("API Key Debug:")
print("="*50)
print(f"OPENAI_API_KEY exists: {bool(openai_key)}")
print(f"OPENAI_API_KEY length: {len(openai_key) if openai_key else 0}")
print(f"OPENAI_API_KEY starts with 'sk-': {openai_key.startswith('sk-') if openai_key else False}")
print()
print(f"ANTHROPIC_API_KEY exists: {bool(anthropic_key)}")
print(f"ANTHROPIC_API_KEY length: {len(anthropic_key) if anthropic_key else 0}")

# Test OpenAI API
if openai_key:
    print("\nTesting OpenAI API...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        models = client.models.list()
        print(f"✅ OpenAI API working! Found {len(models.data)} models")
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
