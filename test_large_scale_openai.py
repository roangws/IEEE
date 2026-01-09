#!/usr/bin/env python3
"""
Large-scale test with OpenAI - Double the citations
"""

import os
import json
import subprocess
import re
import time


def call_openai_direct(prompt, model="gpt-4o", max_tokens=3000, system=None):
    """Direct OpenAI API call using environment variable."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    cmd = [
        "curl", "https://api.openai.com/v1/chat/completions",
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {api_key}",
        "-d", json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        })
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise Exception(f"OpenAI API error: {result.stderr}")
    
    response = json.loads(result.stdout)
    if "error" in response:
        raise Exception(f"OpenAI API error: {response['error']}")
    
    return response["choices"][0]["message"]["content"]


def test_large_scale_openai():
    """Test with double the scale using OpenAI."""
    
    print("="*70)
    print("LARGE-SCALE INTEGRATION TEST WITH OPENAI")
    print("="*70)
    
    # Larger test section with MORE internal citations
    test_section = """## 2. Deep Learning Methods in Medical Imaging

The introduction of deep learning has revolutionized medical image analysis [1]. Convolutional neural networks (CNNs) have become the dominant architecture for medical image classification [2], demonstrating superior performance compared to traditional machine learning methods [3].

Recent advances in attention mechanisms have enabled models to focus on clinically relevant regions [4]. These attention-based approaches have shown particular promise in radiology [5] and pathology [6]. The integration of multi-scale processing allows for better handling of anatomical structures at different resolutions [7].

Transfer learning from natural images has proven effective for medical imaging tasks [8]. Pre-trained models on ImageNet can be fine-tuned for medical applications [9], significantly reducing training time and data requirements [10]. However, domain-specific pre-training on medical images yields even better results [11].

Data augmentation techniques are crucial for improving model robustness [12]. Common augmentation strategies include rotation, scaling, and elastic deformations [13]. More advanced techniques like mixup and cutout have also been successfully applied [14].

Model interpretability remains a critical challenge in medical AI [15]. Techniques such as Grad-CAM and saliency maps help visualize what the model is learning [16]. Ensuring model predictions align with clinical knowledge is essential for adoption [17].

The integration of multiple imaging modalities can improve diagnostic accuracy [18]. Fusion strategies for combining CT, MRI, and PET scans are actively being researched [19]. Multi-modal learning presents unique challenges in data alignment and feature extraction [20]."""
    
    # SIX external references to integrate (double the previous amount)
    external_refs = [
        {"number": 21, "title": "Vision Transformers for Medical Image Recognition", "year": 2023},
        {"number": 22, "title": "Self-Supervised Learning in Medical Imaging", "year": 2024},
        {"number": 23, "title": "Federated Learning for Healthcare Applications", "year": 2023},
        {"number": 24, "title": "Graph Neural Networks in Medical Image Analysis", "year": 2024},
        {"number": 25, "title": "Diffusion Models for Medical Image Generation", "year": 2024},
        {"number": 26, "title": "Foundation Models for Medical AI", "year": 2024}
    ]
    
    print("\n📝 Test Section with Internal Citations:")
    print("-" * 70)
    print(f"Length: {len(test_section)} characters")
    print(f"Paragraphs: 6")
    
    original_citations = set(re.findall(r'\[(\d+)\]', test_section))
    print(f"Internal citations: {len(original_citations)} citations")
    print(f"Citation numbers: {sorted(original_citations)}")
    
    print("\n🌐 External References to Integrate:")
    print(f"Total: {len(external_refs)} references")
    for ref in external_refs:
        print(f"   [{ref['number']}] {ref['title']} ({ref['year']})")
    
    # Build prompt with explicit citation numbers
    citation_context = "\nAVAILABLE EXTERNAL CITATIONS:\n"
    for ref in external_refs:
        citation_context += f"[{ref['number']}] {ref['title']} ({ref['year']})\n"
    
    system_msg = """You are an expert academic writer. Your task is to enhance a section by adding citations in the correct locations.

CRITICAL RULES:
1. PRESERVE all existing citations exactly as they appear
2. Add new citations from the AVAILABLE EXTERNAL CITATIONS list
3. Place citations immediately after the claim they support
4. Use IEEE format: [number]
5. DO NOT invent citation numbers - ONLY use the numbers provided in the prompt
6. Keep the section structure unchanged
7. DO NOT add titles or headings - only enhance the existing content with citations
8. Add minimal context around citations without changing the core content
9. You MUST use ONLY the exact citation numbers listed in the AVAILABLE EXTERNAL CITATIONS section"""

    prompt = f"""Enhance this section with citations from the AVAILABLE EXTERNAL CITATIONS list:

SECTION CONTENT:
{test_section}

{citation_context}

CRITICAL REQUIREMENTS:
- You MUST add citations using ONLY these numbers: [21], [22], [23], [24], [25], [26]
- Add citations where they naturally support the content
- Match citation topics to content topics
- Preserve all existing citations [1]-[20]
- Add minimal supporting context where needed
- Return the enhanced text with citations added

IMPORTANT: Aim to integrate at least 60% of the external citations (at least 4 out of 6).
Return ONLY the enhanced section content."""

    print("\n🔄 Testing with OpenAI GPT-4o...")
    start_time = time.time()
    
    try:
        enhanced = call_openai_direct(prompt, model="gpt-4o", max_tokens=3000, system=system_msg)
        elapsed = time.time() - start_time
        
        print(f"✅ Response received in {elapsed:.1f} seconds")
        
        # Analyze results
        enhanced_citations = set(re.findall(r'\[(\d+)\]', enhanced))
        new_citations = enhanced_citations - original_citations
        external_numbers = {str(ref['number']) for ref in external_refs}
        
        print("\n📊 Results:")
        print(f"  Original citations: {len(original_citations)} → {sorted(original_citations)}")
        print(f"  Enhanced citations: {len(enhanced_citations)} → {sorted(enhanced_citations)}")
        print(f"  New citations added: {len(new_citations)} → {sorted(new_citations)}")
        
        # Check if external citations are present
        all_external_in_text = external_numbers & enhanced_citations
        integration_rate = len(all_external_in_text) / len(external_numbers) * 100
        
        print(f"\n  External citations in text: {sorted(all_external_in_text)}")
        print(f"  Integration rate: {integration_rate:.1f}% ({len(all_external_in_text)}/{len(external_numbers)})")
        
        print("\n📝 Enhanced Section (first 800 chars):")
        print("-" * 70)
        print(enhanced[:800] + "...")
        
        # Show where citations were added
        print("\n📍 Citation Analysis by Paragraph:")
        print("-" * 70)
        paragraphs = enhanced.split('\n\n')
        for i, para in enumerate(paragraphs, 1):
            citations = set(re.findall(r'\[(\d+)\]', para))
            external_in_para = citations & external_numbers
            if external_in_para:
                print(f"\nParagraph {i}:")
                print(f"  All citations: {sorted(citations)}")
                print(f"  External citations: {sorted(external_in_para)}")
                for cit in sorted(external_in_para):
                    ref = next(r for r in external_refs if str(r['number']) == cit)
                    print(f"    → [{cit}] {ref['title']}")
        
        # Check 60% threshold
        print("\n" + "="*70)
        if integration_rate >= 60:
            print(f"✅ SUCCESS: Integration rate {integration_rate:.1f}% meets 60% threshold!")
        else:
            print(f"⚠️  WARNING: Integration rate {integration_rate:.1f}% below 60% threshold")
        
        # Show unified bibliography preview
        print("\n📋 UNIFIED BIBLIOGRAPHY PREVIEW:")
        print("-" * 70)
        print(f"Total references after integration: {len(enhanced_citations)}")
        print(f"  • Internal references: {len(original_citations)} ([1]-[20])")
        print(f"  • External references: {len(all_external_in_text)} ([21]-[26])")
        print(f"  • Final sequential numbering: [1] to [{len(enhanced_citations)}]")
        
        # Show sample of how references would be renumbered
        print("\n📊 Sample Citation Renumbering:")
        all_nums = sorted([int(x) for x in enhanced_citations])
        for i, old_num in enumerate(all_nums[:5], 1):
            ref_type = "Internal" if old_num <= 20 else "External"
            print(f"  [{old_num}] → [{i}] ({ref_type})")
        print(f"  ...")
        print(f"  [{all_nums[-1]}] → [{len(all_nums)}] ({'Internal' if all_nums[-1] <= 20 else 'External'})")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    test_large_scale_openai()
