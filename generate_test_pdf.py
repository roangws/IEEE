#!/usr/bin/env python3
"""
Generate actual PDF to test and validate the LaTeX fixes.
This runs WITHOUT Streamlit to avoid import issues.
"""
import json
import os
import re
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime

def _normalize_article_for_rendering(text: str) -> str:
    """Normalize LaTeX/Markdown - COPIED FROM app.py with the fix."""
    t = text or ""
    
    # Fix malformed LaTeX delimiters
    t = t.replace("\\left$", "\\left(")
    t = t.replace("\\right$", "\\right)")
    t = t.replace("$\\left(", "\\left(")
    t = t.replace("\\right)$", "\\right)")
    t = t.replace("\\left\\frac", "\\left(\\frac")
    
    # Apply regex fixes
    for _ in range(20):
        before = t
        t = re.sub(r"\\left\$", r"\\left(", t)
        t = re.sub(r"\\right\$", r"\\right)", t)
        t = re.sub(r"\$\\left\(", r"\\left(", t)
        t = re.sub(r"\\right\)\$(?!\$)", r"\\right)", t)
        t = re.sub(r"\\left\\frac", r"\\left(\\frac", t)
        t = re.sub(r"\\right([A-Za-z])", r"\\right)\\1", t)
        if t == before:
            break
    
    # Final safety net
    t = t.replace("\\left$", "\\left(")
    t = t.replace("\\right$", "\\right)")
    t = t.replace("$\\left(", "\\left(")
    
    # Normal normalization
    t = t.replace('\\[', '$$').replace('\\]', '$$')
    
    # Convert equation environments
    t = re.sub(r"\\begin\{equation\*?\}\s*([\s\S]*?)\s*\\end\{equation\*?\}", r"$$\n\1\n$$", t)
    t = re.sub(r"\\begin\{align\*?\}\s*([\s\S]*?)\s*\\end\{align\*?\}", r"$$\n\\begin{aligned}\n\1\n\\end{aligned}\n$$", t)
    
    # CRITICAL: Fix bare LaTeX formulas
    def fix_bare_latex_lines(text):
        """Wrap lines containing bare LaTeX in display math."""
        lines = text.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Skip empty lines, tables, and lines already in math mode
            if not stripped or '|' in line or stripped.startswith('$$') or stripped.startswith('#'):
                fixed_lines.append(line)
                i += 1
                continue
            
            # Check if line has LaTeX commands
            has_latex = bool(re.search(r'\\(?:left|right|frac|sqrt|mathbf|mathcal|text|mathrm|alpha|beta|gamma|delta|epsilon|theta|lambda|mu|sigma|omega|sum|int|prod|lim|infty|partial|nabla|times|cdot)', line))
            
            if has_latex:
                dollar_count = line.count('$')
                
                # If no $ at all, this is bare LaTeX
                if dollar_count == 0:
                    # Check if this is part of a multi-line formula
                    formula_lines = [stripped]
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line:
                            break
                        next_has_latex = bool(re.search(r'\\(?:left|right|frac|sqrt|mathbf|mathcal|alpha|beta|gamma)', next_line))
                        next_has_dollar = '$' in next_line
                        if next_has_latex and not next_has_dollar:
                            formula_lines.append(next_line)
                            j += 1
                        else:
                            break
                    
                    # Wrap the entire multi-line formula
                    formula = '\n'.join(formula_lines)
                    fixed_lines.append(f"$$\n{formula}\n$$")
                    i = j
                    continue
                
                # If odd number of $, there's an unclosed $
                if dollar_count % 2 == 1:
                    if '$' in line:
                        first_dollar_pos = line.find('$')
                        after_dollar = line[first_dollar_pos+1:]
                        if re.search(r'\\(?:left|right|mathbf|mathcal)', after_dollar):
                            match = re.search(r'(\\right[)\]])(\s*[,;.])', after_dollar)
                            if match:
                                insert_pos = first_dollar_pos + 1 + match.start(2)
                                fixed_line = line[:insert_pos] + '$' + line[insert_pos:]
                                fixed_lines.append(fixed_line)
                                i += 1
                                continue
            
            fixed_lines.append(line)
            i += 1
        
        return '\n'.join(fixed_lines)
    
    t = fix_bare_latex_lines(t)
    
    return t

def generate_simple_pdf(article_text, output_path="test_output.pdf"):
    """Generate a simple PDF with the article text."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Extract title
    lines = article_text.split('\n')
    title = "Test Article"
    body_start = 0
    for i, line in enumerate(lines[:10]):
        if line.strip().startswith('# '):
            title = line.strip()[2:]
            body_start = i + 1
            break
    
    # Add title
    title_style = ParagraphStyle(name='Title', fontSize=18, alignment=TA_CENTER, spaceAfter=30)
    elements.append(Paragraph(f"<b>{title}</b>", title_style))
    elements.append(Spacer(1, 12))
    
    # Normalize the body
    article_body = '\n'.join(lines[body_start:])
    normalized = _normalize_article_for_rendering(article_body)
    
    # Add normalized text
    for line in normalized.split('\n'):
        if line.strip():
            # Simple rendering - just add as paragraphs
            try:
                p = Paragraph(line, styles['Normal'])
                elements.append(p)
                elements.append(Spacer(1, 6))
            except:
                # If paragraph fails, just skip
                pass
    
    doc.build(elements)
    
    # Save to file
    with open(output_path, 'wb') as f:
        f.write(buffer.getvalue())
    
    return buffer.getvalue()

# Main test
print("="*70)
print("GENERATING TEST PDF WITH LATEX FIXES")
print("="*70)

cache_path = ".ui_cache/ui_state.json"
if os.path.exists(cache_path):
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    
    article = cache.get('generated_article', '')
    
    if article:
        print(f"\nArticle length: {len(article)} chars")
        
        # Check for the problematic formula BEFORE normalization
        if 'q\\left(\\mathbf{x}_t' in article:
            idx = article.find('q\\left(\\mathbf{x}_t')
            context = article[max(0,idx-100):min(len(article),idx+200)]
            print(f"\nFound problematic formula at position {idx}")
            print(f"Context BEFORE normalization:")
            print(context)
            
            # Apply normalization
            lines = article.split('\n')
            body_start = 0
            for i, line in enumerate(lines[:10]):
                if line.strip().startswith('# '):
                    body_start = i + 1
                    break
            
            article_body = '\n'.join(lines[body_start:])
            normalized = _normalize_article_for_rendering(article_body)
            
            # Check AFTER normalization
            if 'q\\left(\\mathbf{x}_t' in normalized:
                idx2 = normalized.find('q\\left(\\mathbf{x}_t')
                context2 = normalized[max(0,idx2-100):min(len(normalized),idx2+200)]
                print(f"\nContext AFTER normalization:")
                print(context2)
                
                # Check if it's now wrapped in $$
                if '$$' in context2[:50] or '$$' in context2[-50:]:
                    print("\n✅ Formula is now wrapped in $$ ... $$")
                else:
                    print("\n❌ Formula still not wrapped properly")
        
        # Generate the PDF
        print(f"\nGenerating PDF...")
        try:
            pdf_bytes = generate_simple_pdf(article, "test_latex_fix.pdf")
            print(f"✅ PDF generated: test_latex_fix.pdf ({len(pdf_bytes):,} bytes)")
            print(f"\n⚠️  MANUAL VERIFICATION REQUIRED:")
            print(f"   Open test_latex_fix.pdf and check if formulas render correctly")
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ No article in cache")
else:
    print(f"❌ Cache file not found: {cache_path}")
