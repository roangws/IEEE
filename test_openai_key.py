#!/usr/bin/env python3
"""
Quick test to verify OpenAI API key is valid and working.
"""

import os
from openai import OpenAI

# Load from environment
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    print("❌ OPENAI_API_KEY not found in environment")
    exit(1)

print(f"✓ API Key found: {api_key[:15]}...{api_key[-4:]}")

# Test the API key
try:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'API key is valid' if you can read this."}],
        max_tokens=20
    )
    
    result = response.choices[0].message.content
    print(f"✅ API Key is VALID!")
    print(f"✅ OpenAI Response: {result}")
    print(f"✅ Step 3 integration will work correctly")
    
except Exception as e:
    print(f"❌ API Key is INVALID!")
    print(f"❌ Error: {str(e)}")
    exit(1)
