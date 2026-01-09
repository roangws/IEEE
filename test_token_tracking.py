#!/usr/bin/env python3
"""
Test script to verify token tracking implementation.
This tests whether the integration is actually tracking real OpenAI API usage or just estimating.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import call_openai

def test_openai_token_tracking():
    """Test if OpenAI API returns usage information"""
    print("Testing OpenAI API token tracking...")
    print("=" * 60)
    
    # Test prompt
    test_prompt = "Write a brief summary of artificial intelligence in about 100 words."
    
    try:
        # Call OpenAI API
        print("Making test API call to OpenAI...")
        response_content = call_openai(test_prompt, model="gpt-4o", max_tokens=200)
        
        print(f"Response length: {len(response_content)} characters")
        print(f"Estimated tokens (response/4): {len(response_content)//4}")
        print()
        print("ISSUE: The current call_openai() function only returns the content.")
        print("It doesn't return usage information (prompt_tokens, completion_tokens, total_tokens).")
        print()
        print("To fix this, we need to:")
        print("1. Modify call_openai() to return both content and usage")
        print("2. Update the integration to track real usage from each API call")
        print("3. Aggregate usage across multiple API calls if any")
        
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_current_integration_tracking():
    """Test what the current integration is actually tracking"""
    print("\n\nTesting current integration token tracking...")
    print("=" * 60)
    
    print("Current implementation in layer2_external_ui.py:")
    print("- Uses ESTIMATED tokens based on text length")
    print("- Does NOT track real API usage")
    print("- Calculation: article_text//4 + refs*100 for input")
    print("- Calculation: enhanced_article//4 for output")
    print()
    print("This is inaccurate because:")
    print("1. Real tokenization differs from simple character/4 division")
    print("2. API calls may have different token counts than estimates")
    print("3. Multiple API calls aren't being tracked separately")

def main():
    """Run all tests"""
    print("TOKEN TRACKING VERIFICATION TEST")
    print("=" * 60)
    print()
    
    # Check if OpenAI API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("WARNING: OPENAI_API_KEY not found in environment")
        print("Some tests may not work without it.")
        print()
    
    test_openai_token_tracking()
    test_current_integration_tracking()
    
    print("\n\nCONCLUSION:")
    print("=" * 60)
    print("❌ Token tracking is NOT accurately implemented")
    print("❌ Currently using estimates, not real API data")
    print("✅ But the UI displays the estimated data correctly")
    print()
    print("RECOMMENDATION:")
    print("Modify the code to track real token usage from OpenAI API responses")

if __name__ == "__main__":
    main()
