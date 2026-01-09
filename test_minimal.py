#!/usr/bin/env python3
"""
Minimal test to check if integration works
"""

import subprocess
import json
import re

def test_ollama_integration():
    """Test basic integration with Ollama."""
    
    print("Testing Ollama integration...")
    
    # Simple test section
    test_section = """Deep learning has transformed medical image analysis. CNNs can learn features automatically [6]. Recent advances include attention mechanisms [7]."""
    
    # Build prompt
    prompt = f"""Add citation [13] to this text after the word CNNs:
{test_section}

Return only the enhanced text."""
    
    # Call Ollama
    cmd = ["curl", "http://localhost:11434/api/generate", 
           "-H", "Content-Type: application/json",
           "-d", json.dumps({
               "model": "gemma3:27b",
               "prompt": prompt,
               "stream": False
           })]
    
    print("Calling Ollama...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return
    
    response = json.loads(result.stdout)
    enhanced = response.get("response", "")
    
    print("\nOriginal:", test_section)
    print("\nEnhanced:", enhanced)
    
    # Check if citation was added
    if "[13]" in enhanced:
        print("\n✅ SUCCESS: External citation [13] was added!")
    else:
        print("\n❌ FAILED: External citation [13] was not added")

if __name__ == "__main__":
    test_ollama_integration()
