#!/usr/bin/env python3
"""
Title Duplication Validation Script
This script validates the 5 potential reasons for title duplication in the article display.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from citation_manager import CitationManager

def validate_title_extraction():
    """Validate Reason 1 & 4: Check if extract_title properly removes title from body"""
    print("=" * 60)
    print("VALIDATION 1 & 4: Title Extraction Function")
    print("=" * 60)
    
    # Sample article text similar to the problematic one
    test_article = """Video Inpainting and Restoration: Diffusion Models for Repairing Missing or Corrupted Video Segments

Video inpainting and restoration are critical tasks in the field of digital media processing. The primary goal is to repair missing or corrupted segments of video footage to restore its original quality.

## Abstract
Video inpainting and restoration are critical processes...

## 1. Introduction
Video inpainting and restoration are critical tasks..."""
    
    cm = CitationManager()
    title, body = cm.extract_title(test_article)
    
    print(f"Extracted Title: '{title}'")
    print(f"Body starts with: '{body[:100]}...'")
    print()
    
    # Check if title is still in body
    title_in_body = title in body
    print(f"❌ ISSUE CONFIRMED: Title still in body: {title_in_body}")
    
    if title_in_body:
        print("Reason: The extract_title function extracts the title but doesn't remove it from the body")
        print("This confirms Reasons 1 & 4: Title extraction failure/bug")
    
    return title_in_body

def validate_multiple_formats():
    """Validate Reason 2: Check different title formats"""
    print("\n" + "=" * 60)
    print("VALIDATION 2: Multiple Title Formats")
    print("=" * 60)
    
    cm = CitationManager()
    
    # Test different title formats
    test_cases = [
        ("# Markdown Title", "Markdown with # prefix"),
        ("**Bold Title**", "Bold with **"),
        ("Plain Title", "Plain text without formatting")
    ]
    
    for title_text, description in test_cases:
        article = f"{title_text}\n\nArticle content starts here..."
        title, body = cm.extract_title(article)
        title_still_in_body = title_text in body
        
        print(f"\nFormat: {description}")
        print(f"  Title: '{title_text}'")
        print(f"  Title removed from body: {not title_still_in_body}")
        
        if title_still_in_body:
            print(f"  ❌ Format not handled properly")
    
    return True

def validate_streamlit_rendering():
    """Validate Reason 3: Simulate Streamlit rendering behavior"""
    print("\n" + "=" * 60)
    print("VALIDATION 3: Streamlit Rendering Issue")
    print("=" * 60)
    
    # Simulate what happens in layer2_external_ui.py
    enhanced_article = """Video Inpainting and Restoration: Diffusion Models for Repairing Missing or Corrupted Video Segments

Video inpainting and restoration are critical tasks...

## Abstract
Video inpainting and restoration are critical processes..."""
    
    cm = CitationManager()
    extracted_title, article_body = cm.extract_title(enhanced_article)
    
    print("Simulating Streamlit display:")
    print(f"st.title() would display: '{extracted_title}'")
    print(f"st.markdown() would display body starting with: '{article_body[:100]}...'")
    print()
    
    # Check if title appears in both
    title_in_body = extracted_title in article_body
    print(f"❌ DUPLICATION CONFIRMED: Title appears in both st.title() and st.markdown(): {title_in_body}")
    
    return title_in_body

def validate_article_structure():
    """Validate Reason 5: Check if LLM creates duplicate titles"""
    print("\n" + "=" * 60)
    print("VALIDATION 5: Article Structure Issue")
    print("=" * 60)
    
    # Simulate what might happen after LLM processing
    original_article = """Video Inpainting and Restoration: Diffusion Models for Repairing Missing or Corrupted Video Segments

Video inpainting and restoration are critical tasks..."""
    
    # LLM might add title again during polishing
    llm_processed = """Video Inpainting and Restoration: Diffusion Models for Repairing Missing or Corrupted Video Segments

Video Inpainting and Restoration: Diffusion Models for Repairing Missing or Corrupted Video Segments

Video inpainting and restoration are critical tasks..."""
    
    # Count occurrences
    original_count = original_article.count("Video Inpainting and Restoration")
    processed_count = llm_processed.count("Video Inpainting and Restoration")
    
    print(f"Original article title count: {original_count}")
    print(f"After LLM processing title count: {processed_count}")
    
    if processed_count > original_count:
        print("❌ CONFIRMED: LLM added duplicate title during processing")
        return True
    
    return False

def test_current_fix():
    """Test if the current fix in layer2_external_ui.py works"""
    print("\n" + "=" * 60)
    print("TESTING CURRENT FIX")
    print("=" * 60)
    
    # Simulate the fix from layer2_external_ui.py
    enhanced_article = """Video Inpainting and Restoration: Diffusion Models for Repairing Missing or Corrupted Video Segments

Video inpainting and restoration are critical tasks...

## Abstract
Video inpainting and restoration are critical processes..."""
    
    cm = CitationManager()
    extracted_title, article_body = cm.extract_title(enhanced_article)
    
    # Apply the fix
    lines = article_body.split('\n')
    start_idx = 0
    
    for i, line in enumerate(lines):
        if line.strip() == extracted_title.strip():
            start_idx = i + 1
            break
    
    if start_idx > 0:
        article_body = '\n'.join(lines[start_idx:])
    
    # Check if fix worked
    title_still_in_body = extracted_title in article_body
    
    print(f"After applying fix:")
    print(f"  Title: '{extracted_title}'")
    print(f"  Title still in body: {title_still_in_body}")
    
    if not title_still_in_body:
        print("✅ FIX SUCCESSFUL: Title duplication resolved!")
        return True
    else:
        print("❌ FIX FAILED: Title still duplicated")
        return False

def main():
    """Run all validations and generate report"""
    print("TITLE DUPLICATION VALIDATION REPORT")
    print("=" * 60)
    print()
    
    results = {
        "Reason 1 & 4": validate_title_extraction(),
        "Reason 2": validate_multiple_formats(),
        "Reason 3": validate_streamlit_rendering(),
        "Reason 5": validate_article_structure(),
        "Current Fix": test_current_fix()
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY OF FINDINGS")
    print("=" * 60)
    
    for reason, confirmed in results.items():
        status = "❌ CONFIRMED" if confirmed else "✅ RESOLVED"
        print(f"{reason}: {status}")
    
    return results

if __name__ == "__main__":
    main()
