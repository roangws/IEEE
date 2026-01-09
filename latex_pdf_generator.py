#!/usr/bin/env python3
"""
LaTeX-Native PDF Generator
Converts markdown article to LaTeX document and compiles to PDF.
Perfect formula rendering using native LaTeX engine.
"""
import re
import subprocess
import tempfile
from pathlib import Path
from io import BytesIO
from pylatex import Document, Section, Subsection, Command, NoEscape
from pylatex.base_classes import Environment
from pylatex.package import Package

class ArticleToPDF:
    """Convert markdown article with LaTeX formulas to PDF using native LaTeX."""
    
    def __init__(self):
        self.temp_dir = None
    
    def _clean_text(self, text):
        """Clean text for LaTeX - escape special characters ONLY outside math mode."""
        # Don't escape inside $ delimiters - preserve LaTeX commands
        result = []
        in_math = False
        i = 0
        while i < len(text):
            if text[i:i+2] == '$$':
                result.append('$$')
                in_math = not in_math
                i += 2
            elif text[i] == '$':
                result.append('$')
                in_math = not in_math
                i += 1
            elif not in_math:
                # Only escape special characters OUTSIDE math mode
                char = text[i]
                if char in ['&', '%', '#']:
                    result.append('\\' + char)
                elif char == '~':
                    result.append('\\textasciitilde{}')
                elif char == '^':
                    result.append('\\textasciicircum{}')
                elif char == '\\':
                    result.append('\\textbackslash{}')
                elif char in ['_', '{', '}']:
                    # Only escape these if not part of LaTeX command
                    result.append('\\' + char)
                else:
                    result.append(char)
                i += 1
            else:
                # Inside math mode - preserve everything including backslashes
                result.append(text[i])
                i += 1
        return ''.join(result)
    
    def markdown_to_latex(self, article_text, title="Research Article"):
        """Convert markdown article to LaTeX document."""
        # Create document with proper packages
        doc = Document(documentclass='article')
        
        # Add packages for math and formatting
        doc.packages.append(Package('amsmath'))
        doc.packages.append(Package('amssymb'))
        doc.packages.append(Package('geometry', options=['margin=1in']))
        doc.packages.append(Package('hyperref'))
        
        # Set title
        doc.preamble.append(Command('title', title))
        doc.preamble.append(Command('date', NoEscape(r'\today')))
        doc.append(NoEscape(r'\maketitle'))
        
        # Process article line by line
        lines = article_text.split('\n')
        i = 0
        in_display_math = False
        math_lines = []
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Handle display math blocks ($$...$$)
            if line == '$$':
                if in_display_math:
                    # End display math
                    math_content = '\n'.join(math_lines)
                    # Don't wrap in equation* - content already has delimiters
                    doc.append(NoEscape(r'\['))
                    doc.append(NoEscape(math_content))
                    doc.append(NoEscape(r'\]'))
                    in_display_math = False
                    math_lines = []
                else:
                    # Start display math
                    in_display_math = True
                    math_lines = []
                i += 1
                continue
            
            if in_display_math:
                math_lines.append(line)
                i += 1
                continue
            
            # Handle headers
            if line.startswith('### '):
                text = self._clean_text(line[4:])
                doc.append(Subsection(NoEscape(text)))
            elif line.startswith('## '):
                text = self._clean_text(line[3:])
                doc.append(Section(NoEscape(text), numbering=False))
            elif line.startswith('# '):
                # Skip - already used as title
                pass
            # Handle citations [1], [2], etc.
            elif re.search(r'\[\d+\]', line):
                # Process inline math in citations
                text = line
                # Replace $...$ with proper inline math
                text = re.sub(r'\$([^\$]+)\$', r'\\(\1\\)', text)
                # Clean non-math parts
                parts = re.split(r'(\\\(.*?\\\))', text)
                cleaned_parts = []
                for part in parts:
                    if part.startswith('\\('):
                        cleaned_parts.append(part)
                    else:
                        cleaned_parts.append(self._clean_text(part))
                text = ''.join(cleaned_parts)
                doc.append(NoEscape(text))
            else:
                # Regular paragraph
                text = line
                # Replace $...$ with proper inline math
                text = re.sub(r'\$([^\$]+)\$', r'\\(\1\\)', text)
                # Clean non-math parts
                parts = re.split(r'(\\\(.*?\\\))', text)
                cleaned_parts = []
                for part in parts:
                    if part.startswith('\\('):
                        cleaned_parts.append(part)
                    else:
                        cleaned_parts.append(self._clean_text(part))
                text = ''.join(cleaned_parts)
                doc.append(NoEscape(text))
                doc.append(NoEscape(r'\\'))  # Line break
            
            i += 1
        
        return doc
    
    def generate_pdf(self, article_text, title="Research Article", output_path=None):
        """
        Generate PDF from article using LaTeX.
        
        Args:
            article_text: Markdown article with LaTeX formulas
            title: Document title
            output_path: Optional path to save PDF (default: temp file)
            
        Returns:
            BytesIO containing PDF data
        """
        # Create LaTeX document
        doc = self.markdown_to_latex(article_text, title)
        
        # Use temp directory for compilation
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            tex_file = temp_path / 'article'
            
            # Generate .tex file
            doc.generate_tex(str(tex_file))
            
            # Compile with pdflatex
            try:
                # Add /Library/TeX/texbin to PATH
                import os
                env = os.environ.copy()
                env['PATH'] = '/Library/TeX/texbin:' + env.get('PATH', '')
                
                # Run pdflatex twice for references
                for _ in range(2):
                    result = subprocess.run(
                        ['pdflatex', '-interaction=nonstopmode', 'article.tex'],
                        cwd=temp_path,
                        capture_output=True,
                        timeout=30,
                        env=env
                    )
                
                # Read generated PDF
                pdf_path = temp_path / 'article.pdf'
                if pdf_path.exists():
                    with open(pdf_path, 'rb') as f:
                        pdf_data = f.read()
                    
                    # Save to output path if specified
                    if output_path:
                        with open(output_path, 'wb') as f:
                            f.write(pdf_data)
                    
                    return BytesIO(pdf_data)
                else:
                    # Print compilation errors for debugging
                    log_path = temp_path / 'article.log'
                    if log_path.exists():
                        with open(log_path, 'r') as f:
                            print("LaTeX compilation log:")
                            print(f.read()[-2000:])  # Last 2000 chars
                    raise Exception("PDF compilation failed - no output file")
                    
            except subprocess.TimeoutExpired:
                raise Exception("PDF compilation timeout")
            except FileNotFoundError:
                raise Exception("pdflatex not found - please install LaTeX distribution")


# Test the generator
if __name__ == "__main__":
    generator = ArticleToPDF()
    
    # Test with problematic formula
    test_article = """
# Test Article

## Introduction

This is a test of LaTeX rendering.

## Mathematical Framework

The diffusion process is defined as:

$$
q\\left(\\mathbf{x}_t \\mid \\mathbf{x}_{t-1}\\right) = \\mathcal{N}\\left(\\mathbf{x}_t; \\sqrt{\\alpha_t}\\mathbf{x}_{t-1}, \\left(1-\\alpha_t\\right)\\mathbf{I}\\right)
$$

This formula should render perfectly in the PDF.

## Conclusion

Native LaTeX rendering produces perfect mathematical formulas.
"""
    
    print("Testing LaTeX-Native PDF Generator...")
    print("="*70)
    
    try:
        pdf_buffer = generator.generate_pdf(test_article, "Test Article", "test_latex_native.pdf")
        print(f"✅ PDF generated successfully: {len(pdf_buffer.getvalue())} bytes")
        print(f"   Saved to: test_latex_native.pdf")
        print("\n⚠️  Open test_latex_native.pdf to verify formulas render perfectly")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
