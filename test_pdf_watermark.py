#!/usr/bin/env python3
"""
Test script to generate a sample PDF with IEEE watermark
"""

import sys
sys.path.append('/Users/roan-aparavi/aparavi-repo/Roan-IEEE')

from app import generate_article_pdf

# Sample article content
sample_article = """# Video Inpainting and Restoration: Diffusion Models for Repairing Missing or Corrupted Video Segments

## Abstract

Video inpainting has emerged as a critical task in computer vision, addressing the challenge of filling missing or corrupted regions in video sequences while maintaining temporal consistency. This paper presents a comprehensive review of diffusion-based approaches for video inpainting and restoration.

## Introduction

Video inpainting techniques have evolved significantly over the past decade [1]. The introduction of diffusion models has revolutionized the field, offering unprecedented capabilities in generating high-quality, temporally coherent video completions [2].

## Related Work

Early approaches to video inpainting relied on optical flow and patch-based methods [3]. These methods, while effective for simple scenarios, struggled with complex motion and large missing regions.

## Methodology

Our approach leverages the power of diffusion models to address video inpainting challenges. The key innovation lies in the temporal consistency mechanism that ensures smooth transitions across frames [4].

## Experimental Results

We evaluated our method on several benchmark datasets. The results demonstrate significant improvements over existing approaches [5]. Table 1 shows quantitative comparisons.

## Conclusion

This paper presents a novel approach to video inpainting using diffusion models. The experimental results validate the effectiveness of our method in various scenarios.

## References

[1] Smith et al. (2023). "Advances in Video Inpainting"
[2] Johnson and Lee (2023). "Diffusion Models for Video Processing"
[3] Brown et al. (2022). "Traditional Video Inpainting Methods"
[4] Davis et al. (2024). "Temporal Consistency in Video Generation"
[5] Wilson et al. (2023). "Benchmarking Video Inpainting Techniques"
"""

print("Generating sample PDF with IEEE watermark...")

try:
    # Generate PDF
    pdf_bytes = generate_article_pdf(
        article_text=sample_article,
        topic="Video Inpainting and Restoration: Diffusion Models for Repairing Missing or Corrupted Video Segments",
        citation_map={},
        sources=[]
    )
    
    # Save PDF
    output_path = "/Users/roan-aparavi/aparavi-repo/Roan-IEEE/sample_ieee_watermark.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    
    print('✅ Sample PDF generated successfully!')
    print(f"📍 Saved to: {output_path}")
    print(f"📄 Size: {len(pdf_bytes)} bytes")
    print("\nPlease open the PDF to verify:")
    print("- IEEE logo appears in top-left corner of all pages")
    print("- Logo is semi-transparent (watermark effect)")
    print("- Content is properly formatted")
    
except Exception as e:
    print(f"❌ Error generating PDF: {e}")
    import traceback
    traceback.print_exc()
