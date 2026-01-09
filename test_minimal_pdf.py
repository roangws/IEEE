#!/usr/bin/env python3
"""
Minimal PDF generation test with IEEE watermark
"""

import sys
import os
from io import BytesIO

# Add the project path
sys.path.append('/Users/roan-aparavi/aparavi-repo/Roan-IEEE')

# Import only what we need
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

# Create a simple PDF with watermark
def create_test_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Add title
    title = Paragraph("<b>IEEE Watermark Test Document</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Add some content
    content = """
    This is a test document to verify that the IEEE logo watermark is working correctly.
    
    The IEEE logo should appear in the top-left corner of this page as a semi-transparent watermark.
    
    This watermark will appear on ALL pages of the PDF when generated through the main application.
    """
    
    elements.append(Paragraph(content, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Add second page content
    elements.append(PageBreak())
    elements.append(Paragraph("<b>Second Page</b>", styles['Heading1']))
    elements.append(Paragraph("The IEEE watermark should also appear on this page in the top-left corner.", styles['Normal']))
    
    # Helper function to add watermark
    def _add_watermark(canvas, doc):
        try:
            canvas.saveState()
            
            # Load and draw the IEEE logo
            logo_path = "/Users/roan-aparavi/aparavi-repo/Roan-IEEE/IEEE-Logo.jpg"
            if os.path.exists(logo_path):
                # Position: top left, small size
                canvas.drawImage(logo_path, 0.5*inch, 10*inch, width=1*inch, height=0.5*inch, 
                               preserveAspectRatio=True, mask='auto')
                # Make it transparent/light (watermark effect)
                canvas.setFillAlpha(0.3)
            
            canvas.restoreState()
        except Exception as e:
            print(f"Warning: Could not add IEEE watermark: {e}")
    
    # Build PDF with IEEE watermark
    doc.build(elements, onFirstPage=_add_watermark, onLaterPages=_add_watermark)
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

# Generate the test PDF
print("🔄 Generating test PDF with IEEE watermark...")

try:
    pdf_bytes = create_test_pdf()
    
    # Save PDF
    output_path = "/Users/roan-aparavi/aparavi-repo/Roan-IEEE/ieee_watermark_test.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    
    print('✅ Test PDF generated successfully!')
    print(f"📍 Saved to: {output_path}")
    print(f"📄 Size: {len(pdf_bytes)} bytes")
    print("\n📋 Verification checklist:")
    print("  ✓ Open the PDF file")
    print("  ✓ Check page 1: IEEE logo in top-left corner")
    print("  ✓ Check page 2: IEEE logo should also be there")
    print("  ✓ Logo should be semi-transparent (watermark)")
    print("  ✓ Logo should be small and not interfere with text")
    
except Exception as e:
    print(f"❌ Error generating PDF: {e}")
    import traceback
    traceback.print_exc()
