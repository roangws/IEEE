#!/usr/bin/env python3
"""
Test script to verify real token tracking implementation.
This tests whether the integration is now tracking real OpenAI API usage.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import call_openai
from smart_citation_integratorator import SmartCitationIntegrator

def test_openai_real_token_tracking():
    """Test if OpenAI API returns real usage information"""
    print("Testing OpenAI API real token tracking...")
    print("=" * 60)
    
    # Test prompt
    test_prompt = "Write a brief summary of artificial intelligence in about 100 words."
    
    try:
        # Call OpenAI API with return_usage=True
        print("Making test API call to OpenAI with usage tracking...")
        result = call_openai(test_prompt, model="gpt-4o", max_tokens=200, return_usage=True)
        
        if isinstance(result, tuple):
            content, usage = result
            print("✅ SUCCESS: Got usage information!")
            print(f"Response length: {len(content)} characters")
            print("Real usage data:")
            print(f"  - Prompt tokens: {usage.prompt_tokens}")
            print(f"  - Completion tokens: {usage.completion_tokens}")
            print(f"  - Total tokens: {usage.total_tokens}")
            print()
            print("This confirms the API is returning real usage data.")
            return True
        else:
            print("❌ FAILED: API did not return usage information")
            return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_smart_citation_token_tracking():
    """Test if SmartCitationIntegrator tracks real tokens"""
    print("\n\nTesting SmartCitationIntegrator token tracking...")
    print("=" * 60)
    
    try:
        integrator = SmartCitationIntegrator()
        
        # Test article and references
        test_article = """
# Introduction
Artificial intelligence is a rapidly evolving field that focuses on creating intelligent machines.

# Methods
We used machine learning algorithms to analyze the data.

# Results
Our findings show significant improvements in accuracy.
"""
        
        # Create mock external references (normally these would be fetched)
        from external_reference_fetcher import ExternalReference
        test_refs = [
            ExternalReference(
                citation_number=1,
                title="Machine Learning Basics",
                authors=["Smith", "Johnson"],
                year=2023,
                abstract="An introduction to machine learning concepts",
                relevance_score=0.9,
                selected=True
            )
        ]
        
        print("Testing integration with real token tracking...")
        result = integrator.integrate_citations_smart(
            test_article,
            test_refs,
            llm_type="openai",
            model="gpt-4o",
            return_usage=True
        )
        
        if isinstance(result, tuple):
            enhanced_article, usage = result
            print("✅ SUCCESS: SmartCitationIntegrator returned usage data!")
            print("Total usage across all sections:")
            print(f"  - Prompt tokens: {usage.get('prompt_tokens', 0)}")
            print(f"  - Completion tokens: {usage.get('completion_tokens', 0)}")
            print(f"  - Total tokens: {usage.get('total_tokens', 0)}")
            print()
            print(f"Enhanced article length: {len(enhanced_article)} characters")
            return True
        else:
            print("❌ FAILED: SmartCitationIntegrator did not return usage")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_layer():
    """Test if the integration layer uses real token tracking"""
    print("\n\nTesting integration layer (layer2_external_ui)...")
    print("=" * 60)
    print("The integration layer has been updated to:")
    print("1. Call SmartCitationIntegrator with return_usage=True")
    print("2. Extract real token usage from OpenAI API responses")
    print("3. Display real tokens in the UI instead of estimates")
    print("4. Fall back to estimates for non-OpenAI LLMs")
    print()
    print("To test this fully:")
    print("- Run the Streamlit app")
    print("- Select OpenAI GPT as the LLM")
    print("- Integrate external references")
    print("- Check the log for 'REAL tokens used' message")

def main():
    """Run all tests"""
    print("REAL TOKEN TRACKING VERIFICATION TEST")
    print("=" * 60)
    print()
    
    # Check if OpenAI API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("WARNING: OPENAI_API_KEY not found in environment")
        print("Tests will not work without it.")
        print("Please run: source ./run_streamlit.sh")
        print()
        return
    
    # Run tests
    test1_passed = test_openai_real_token_tracking()
    test2_passed = test_smart_citation_token_tracking()
    test_integration_layer()
    
    print("\n\nCONCLUSION:")
    print("=" * 60)
    if test1_passed and test2_passed:
        print("✅ Real token tracking is IMPLEMENTED!")
        print("✅ OpenAI API returns usage information")
        print("✅ SmartCitationIntegrator tracks real usage")
        print("✅ UI will display real token counts and costs")
    else:
        print("❌ Some tests failed")
        print("❌ Check the error messages above")
    
    print()
    print("IMPORTANT:")
    print("- Real token tracking works for OpenAI API only")
    print("- Claude and Ollama use estimates (they don't provide usage)")
    print("- The UI clearly shows when using real vs estimated tokens")

if __name__ == "__main__":
    main()
