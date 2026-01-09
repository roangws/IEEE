#!/usr/bin/env python3
"""
Pandoc PDF Generator
Uses Pandoc to convert markdown with LaTeX formulas to PDF.
Industry-standard, battle-tested solution.
"""
import subprocess
import tempfile
from pathlib import Path
from io import BytesIO

class PandocPDFGenerator:
    """Generate PDF from markdown using Pandoc."""
    
    def generate_pdf(self, article_text, title="Research Article", output_path=None):
        """
        Generate PDF from markdown article using Pandoc.
        
        Args:
            article_text: Markdown article with LaTeX formulas
            title: Document title
            output_path: Optional path to save PDF
            
        Returns:
            BytesIO containing PDF data
        """
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            md_file = temp_path / 'article.md'
            pdf_file = temp_path / 'article.pdf'
            
            # Add title to article if not present
            if not article_text.strip().startswith('#'):
                article_text = f"# {title}\n\n{article_text}"
            
            # CRITICAL FIX: Protect math mode from Pandoc's markdown processing
            # Pandoc converts _ to \emph{} which breaks LaTeX subscripts
            # We need to use display math blocks that Pandoc won't process
            
            # Replace inline math $...$ with display math $$...$$ on separate lines
            # This prevents Pandoc from processing underscores as emphasis
            import re
            lines = article_text.split('\n')
            fixed_lines = []
            
            for line in lines:
                # If line contains inline math with underscores, convert to display math
                if '$' in line and '_' in line and not line.strip().startswith('$$'):
                    # Find all inline math patterns
                    inline_math = re.findall(r'\$([^\$]+)\$', line)
                    if inline_math:
                        # Check if any contain underscores (subscripts)
                        has_subscripts = any('_' in m for m in inline_math)
                        if has_subscripts:
                            # Convert inline to display math
                            # Extract the math part
                            for math in inline_math:
                                if '_' in math:
                                    # Replace inline with display
                                    line = line.replace(f'${math}$', f'\n$$\n{math}\n$$\n')
                
                fixed_lines.append(line)
            
            article_text = '\n'.join(fixed_lines)
            
            # Write markdown file
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(article_text)
            
            # Run Pandoc with proper PATH for pdflatex
            import os
            env = os.environ.copy()
            env['PATH'] = '/Library/TeX/texbin:' + env.get('PATH', '')
            
            try:
                result = subprocess.run(
                    [
                        'pandoc',
                        str(md_file),
                        '-o', str(pdf_file),
                        '--pdf-engine=pdflatex',
                        '-V', 'geometry:margin=1in',
                        '--variable', 'colorlinks=true'
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env=env
                )
                
                if result.returncode != 0:
                    raise Exception(f"Pandoc failed: {result.stderr}")
                
                # Read PDF
                if pdf_file.exists():
                    with open(pdf_file, 'rb') as f:
                        pdf_data = f.read()
                    
                    # Save to output path if specified
                    if output_path:
                        with open(output_path, 'wb') as f:
                            f.write(pdf_data)
                    
                    return BytesIO(pdf_data)
                else:
                    raise Exception("PDF file not created")
                    
            except subprocess.TimeoutExpired:
                raise Exception("Pandoc timeout")
            except FileNotFoundError:
                raise Exception("Pandoc not found - please install: brew install pandoc")


if __name__ == "__main__":
    import json
    
    generator = PandocPDFGenerator()
    
    # Load article from cache
    with open('.ui_cache/ui_state.json', 'r') as f:
        cache = json.load(f)
    
    article = cache.get('generated_article', '')
    
    print("Testing Pandoc PDF Generator...")
    print("="*70)
    
    try:
        pdf_buffer = generator.generate_pdf(article, "Video Inpainting Test", "PANDOC_FINAL_TEST.pdf")
        print(f"✅ PDF generated: {len(pdf_buffer.getvalue())} bytes")
        print(f"   Saved to: PANDOC_FINAL_TEST.pdf")
        print("\nOpen PANDOC_FINAL_TEST.pdf to verify formulas.")
    except Exception as e:
        print(f"❌ Error: {e}")
