#!/usr/bin/env python3
"""
Test script for external reference integration
Tests the complete flow with mock data using local LLM
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from external_reference_fetcher import ExternalReference
from smart_citation_integratorator import SmartCitationIntegrator
from citation_manager import CitationManager
from citation_formatter import CitationFormatter
import time


def create_test_data():
    """Create test article with internal references and external references."""
    
    # Test article with multiple sections and internal citations
    test_article = """# Deep Learning Approaches for Medical Image Analysis

## Abstract

Medical image analysis has revolutionized healthcare through advanced machine learning techniques. This paper presents a comprehensive review of deep learning methods for medical image interpretation [1]. We demonstrate significant improvements in diagnostic accuracy using convolutional neural networks [2].

## 1. Introduction

Medical imaging plays a crucial role in modern healthcare, with millions of procedures performed annually. Traditional computer vision methods have shown limited success in medical image analysis due to the complexity and variability of medical images [3]. Recent advances in deep learning have opened new possibilities for automated diagnosis and treatment planning.

The integration of artificial intelligence in medical imaging has accelerated in recent years, with numerous studies demonstrating the potential for deep learning models to match or exceed human performance in specific diagnostic tasks [4].

## 2. Related Work

### 2.1 Traditional Machine Learning in Medical Imaging

Before the deep learning era, traditional machine learning approaches dominated medical image analysis. Support vector machines and random forests were commonly used for feature-based classification [5]. These methods required careful feature engineering and domain expertise.

### 2.2 Deep Learning Revolution

The introduction of deep learning, particularly convolutional neural networks (CNNs), has transformed medical image analysis. CNNs can automatically learn hierarchical features from raw pixel data, eliminating the need for manual feature extraction [6].

## 3. Methodology

Our approach utilizes a novel architecture combining attention mechanisms with residual connections. The model processes medical images through multiple scales, capturing both local details and global context [7].

We employ a multi-task learning framework where the model simultaneously learns segmentation, classification, and localization tasks. This approach has shown superior performance compared to single-task models [8].

## 4. Experiments and Results

We evaluated our method on three benchmark datasets: chest X-rays, mammograms, and CT scans. Our model achieved 95.2% accuracy on chest X-ray classification, outperforming previous state-of-the-art methods [9].

The attention mechanism visualization revealed that our model focuses on clinically relevant regions, demonstrating its potential for explainable AI in healthcare [10].

## 5. Discussion

The results demonstrate the effectiveness of our proposed approach. The integration of attention mechanisms with multi-task learning provides a robust framework for medical image analysis.

Future work should explore the adaptation of our method to other imaging modalities and investigate its performance in real clinical settings [11].

## 6. Conclusion

This paper presents a comprehensive deep learning approach for medical image analysis. Our method achieves state-of-the-art performance on multiple benchmark datasets while maintaining interpretability.

The integration of deep learning in medical imaging continues to evolve, with promising implications for healthcare delivery and patient outcomes [12].
"""
    
    # Internal citation map (simulating local references)
    citation_map = {
        'paper1.pdf': 1,
        'paper2.pdf': 2,
        'paper3.pdf': 3,
        'paper4.pdf': 4,
        'paper5.pdf': 5,
        'paper6.pdf': 6,
        'paper7.pdf': 7,
        'paper8.pdf': 8,
        'paper9.pdf': 9,
        'paper10.pdf': 10,
        'paper11.pdf': 11,
        'paper12.pdf': 12,
    }
    
    # External references to integrate
    external_refs = [
        ExternalReference(
            citation_number=13,
            title="Transformers in Medical Imaging: A Comprehensive Survey",
            authors=["Zhang, L.", "Wang, X.", "Chen, Y."],
            year=2023,
            venue="IEEE Transactions on Medical Imaging",
            abstract="This survey provides a comprehensive overview of transformer architectures applied to medical image analysis, covering various applications including classification, segmentation, and detection.",
            relevance_score=0.95,
            selected=True
        ),
        ExternalReference(
            citation_number=14,
            title="Self-Supervised Learning for Medical Image Analysis: A Review",
            authors=["Johnson, M.", "Smith, K.", "Brown, R."],
            year=2024,
            venue="Medical Image Analysis",
            abstract="We review recent advances in self-supervised learning techniques for medical image analysis, discussing contrastive learning, masked image modeling, and their applications in healthcare.",
            relevance_score=0.92,
            selected=True
        ),
        ExternalReference(
            citation_number=15,
            title="Federated Learning for Healthcare: Privacy-Preserving Collaborative AI",
            authors=["Lee, S.", "Kim, H.", "Park, J."],
            year=2023,
            venue="Nature Machine Intelligence",
            abstract="This paper explores federated learning approaches that enable collaborative model training across multiple hospitals while preserving patient privacy through decentralized data processing.",
            relevance_score=0.88,
            selected=True
        ),
        ExternalReference(
            citation_number=16,
            title="3D CNNs for Volumetric Medical Image Segmentation",
            authors=["Anderson, P.", "Wilson, T.", "Davis, M."],
            year=2024,
            venue="Computerized Medical Imaging and Graphics",
            abstract="We propose a novel 3D convolutional neural network architecture specifically designed for volumetric medical image segmentation, achieving state-of-the-art results on brain tumor and organ segmentation tasks.",
            relevance_score=0.90,
            selected=True
        ),
        ExternalReference(
            citation_number=17,
            title="Explainable AI in Medical Imaging: Methods and Applications",
            authors=["Taylor, E.", "Martinez, C.", "Robinson, D."],
            year=2023,
            venue="Journal of Medical Artificial Intelligence",
            abstract="This comprehensive review covers explainable AI techniques in medical imaging, including attention visualization, saliency maps, and counterfactual explanations for clinical decision support.",
            relevance_score=0.87,
            selected=True
        )
    ]
    
    return test_article, citation_map, external_refs


def test_integration_with_local_llm():
    """Test the integration process using local Ollama LLM."""
    
    print("="*60)
    print("TESTING EXTERNAL REFERENCE INTEGRATION")
    print("="*60)
    print()
    
    # Create test data
    article_text, citation_map, external_refs = create_test_data()
    
    print(f"📝 Test article created with {len(article_text)} characters")
    print(f"📚 Internal references: {len(citation_map)} (citations [1]-[12])")
    print(f"🌐 External references: {len(external_refs)} (citations [13]-[17])")
    print()
    
    # Initialize integrator
    integrator = SmartCitationIntegrator()
    
    # Track citations before integration
    cm = CitationManager()
    original_citations = set(cm.extract_citations_from_article(article_text))
    print(f"📊 Original citations in article: {sorted(original_citations)}")
    print()
    
    # Test with different LLMs
    test_models = [
        ("ollama", "gemma3:27b", "Gemma 3 27B (Local)"),
        ("ollama", "qwen3:8b", "Qwen 3 8B (Local)"),
    ]
    
    for llm_type, model_name, display_name in test_models:
        print(f"\n{'='*60}")
        print(f"TESTING WITH: {display_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Run integration
            enhanced_article, usage = integrator.integrate_citations_smart(
                article_text=article_text,
                references=external_refs,
                llm_type=llm_type,
                model=model_name,
                return_usage=True
            )
            
            # Analyze results
            enhanced_citations = set(cm.extract_citations_from_article(enhanced_article))
            new_citations = enhanced_citations - original_citations
            external_numbers = {ref.citation_number for ref in external_refs}
            external_integrated = new_citations & external_numbers
            
            integration_rate = len(external_integrated) / len(external_numbers) * 100
            
            print(f"\n📈 Results:")
            print(f"  ⏱️  Time: {time.time() - start_time:.1f} seconds")
            print(f"  📊 Total citations after: {len(enhanced_citations)}")
            print(f"  📊 New citations added: {len(new_citations)}")
            print(f"  🌐 External integrated: {len(external_integrated)}/{len(external_numbers)} ({integration_rate:.1f}%)")
            
            if external_integrated:
                print(f"  ✅ External citations added: {sorted(external_integrated)}")
            
            not_integrated = external_numbers - enhanced_citations
            if not_integrated:
                print(f"  ⚠️  External NOT integrated: {sorted(not_integrated)}")
            
            # Check 60% threshold
            if integration_rate >= 60:
                print(f"  ✅ PASSED 60% threshold!")
            else:
                print(f"  ❌ FAILED 60% threshold (need ≥60%)")
            
            # Show sample of enhanced text
            print(f"\n📝 Sample of enhanced article (first 500 chars):")
            print("-" * 40)
            print(enhanced_article[:500] + "...")
            print("-" * 40)
            
        except Exception as e:
            print(f"\n❌ ERROR with {display_name}: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    print(f"\n{'='*60}")
    print("TEST COMPLETE")
    print(f"{'='*60}")


def test_step4_simulation():
    """Simulate Step 4: Build unified reference list."""
    
    print("\n\n" + "="*60)
    print("SIMULATING STEP 4: UNIFIED REFERENCE LIST")
    print("="*60)
    
    # Get test data
    article_text, citation_map, external_refs = create_test_data()
    
    # Simulate after integration (assume all externals were added)
    cm = CitationManager()
    formatter = CitationFormatter()
    
    # Extract citations (simulating after integration)
    all_citations = set(range(1, 18))  # Assume all [1]-[17] are cited
    
    # Build unified reference list
    all_refs = []
    old_to_new_number = {}
    cited_refs = []
    
    # Map citation numbers to filenames
    number_to_filename = {num: filename for filename, num in citation_map.items()}
    
    # Collect cited references
    for num in sorted(all_citations):
        if num in number_to_filename:
            cited_refs.append((num, 'local', number_to_filename[num]))
        else:
            for ext_ref in external_refs:
                if ext_ref.citation_number == num:
                    cited_refs.append((num, 'external', ext_ref))
                    break
    
    # Renumber sequentially
    for new_num, (old_num, ref_type, ref_data) in enumerate(cited_refs, start=1):
        old_to_new_number[old_num] = new_num
        
        if ref_type == 'local':
            filename = ref_data
            ref_text = f"[{new_num}] Local Reference {new_num} (from {filename})"
            all_refs.append(ref_text)
        else:
            ext_ref = ref_data
            ref_text = f"[{new_num}] {ext_ref.authors[0]} et al., \"{ext_ref.title}\", {ext_ref.venue}, {ext_ref.year}."
            all_refs.append(ref_text)
    
    print(f"\n📋 Unified Reference List ({len(all_refs)} total references):")
    print("-" * 60)
    for ref in all_refs:
        print(ref)
    
    print(f"\n✅ Step 4 simulation complete!")
    print(f"   Local references: {sum(1 for _, t, _ in cited_refs if t == 'local')}")
    print(f"   External references: {sum(1 for _, t, _ in cited_refs if t == 'external')}")
    print(f"   Total unified: {len(all_refs)}")


if __name__ == "__main__":
    print("🧪 Starting External Reference Integration Test")
    print("This test will:")
    print("  1. Create a test article with internal citations")
    print("  2. Add 5 external references")
    print("  3. Run integration with local LLMs")
    print("  4. Verify Step 4 unified bibliography")
    print()
    
    # Run the test
    test_integration_with_local_llm()
    test_step4_simulation()
    
    print("\n🎉 All tests completed!")
