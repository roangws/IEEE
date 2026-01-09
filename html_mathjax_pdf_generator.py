#!/usr/bin/env python3
"""
HTML-to-PDF Generator with MathJax
Uses Playwright to render HTML with MathJax formulas, then export to PDF.
Perfect formula rendering - same as homepage display.
"""
import asyncio
import base64
import os
from io import BytesIO
from playwright.async_api import async_playwright

class HTMLMathJaxPDFGenerator:
    """Generate PDF from markdown using HTML + MathJax rendering."""
    
    def __init__(self):
        # Load IEEE logo and convert to base64
        self.ieee_logo_base64 = self._load_ieee_logo()
        
        self.html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.2;
            max-width: 700px;
            margin: 20px auto;
            padding: 10px;
            color: #333;
            font-size: 10pt;
        }}
        .ieee-header {{
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #003366;
        }}
        .ieee-logo {{
            width: 120px;
            height: auto;
            margin-bottom: 10px;
        }}
        h1 {{
            font-size: 18px;
            text-align: center;
            margin-bottom: 15px;
            padding-bottom: 5px;
            color: #003366;
        }}
        h2 {{
            font-size: 14px;
            margin-top: 15px;
            margin-bottom: 10px;
            border-bottom: 1px solid #666;
            padding-bottom: 3px;
            color: #003366;
        }}
        h3 {{
            font-size: 12px;
            margin-top: 10px;
            margin-bottom: 5px;
        }}
        p {{
            margin-bottom: 10px;
            text-align: justify;
            font-size: 10pt;
        }}
        .math-display {{
            margin: 10px 0;
            text-align: center;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 8pt 0;
            font-size: 8pt;
        }}
        th, td {{
            border: 1pt solid #000;
            padding: 4pt;
            text-align: center;
            vertical-align: middle;
        }}
        th {{
            font-weight: bold;
            background-color: #f0f0f0;
        }}
        .citation {{
            font-size: 8pt;
            vertical-align: super;
            color: #000;
        }}
        .references {{
            margin-top: 16pt;
            font-size: 8pt;
        }}
        .references p {{
            margin-bottom: 4pt;
            text-indent: -0.35in;
            padding-left: 0.35in;
        }}
        @page {{
            @bottom-center {{
                content: counter(page);
                font-size: 8pt;
            }}
        }}
    </style>
    <!-- MathJax Configuration -->
    <script>
        window.MathJax = {{
            tex: {{
                inlineMath: [['$', '$']],
                displayMath: [['$$', '$$']],
                processEscapes: true,
                processEnvironments: true
            }},
            options: {{
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
            }},
            startup: {{
                pageReady: () => {{
                    return MathJax.startup.defaultPageReady().then(() => {{
                        window.mathJaxReady = true;
                    }});
                }}
            }}
        }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
</head>
<body>
<div class="ieee-header">
    <img src="data:image/png;base64,{ieee_logo_base64}" class="ieee-logo" alt="IEEE Logo">
</div>
{content}
</body>
</html>"""
    
    def markdown_to_html(self, markdown_text):
        """Convert markdown to HTML (simple conversion)."""
        # CRITICAL FIX: Clean LaTeX for MathJax compatibility
        # Remove double-escaped backslashes that cause "Math input error"
        markdown_text = markdown_text.replace('\\\\', '\\')
        
        lines = markdown_text.split('\n')
        html_lines = []
        in_table = False
        in_display_math = False
        
        for line in lines:
            stripped = line.strip()
            
            # Handle display math
            if stripped == '$$':
                if in_display_math:
                    html_lines.append('$$</div>')
                    in_display_math = False
                else:
                    html_lines.append('<div class="math-display">$$')
                    in_display_math = True
                continue
            
            if in_display_math:
                html_lines.append(line)
                continue
            
            # Handle headers
            if stripped.startswith('### '):
                html_lines.append(f'<h3>{stripped[4:]}</h3>')
            elif stripped.startswith('## '):
                html_lines.append(f'<h2>{stripped[3:]}</h2>')
            elif stripped.startswith('# '):
                html_lines.append(f'<h1>{stripped[2:]}</h1>')
            # Handle tables
            elif '|' in stripped and stripped.startswith('|'):
                if not in_table:
                    html_lines.append('<table>')
                    in_table = True
                # Skip separator lines
                if set(stripped.replace('|', '').strip()) <= set('-: '):
                    continue
                # Parse table row
                cells = [c.strip() for c in stripped.strip('|').split('|')]
                html_lines.append('<tr>')
                for cell in cells:
                    html_lines.append(f'<td>{cell}</td>')
                html_lines.append('</tr>')
            else:
                if in_table:
                    html_lines.append('</table>')
                    in_table = False
                if stripped:
                    html_lines.append(f'<p>{line}</p>')
                else:
                    html_lines.append('<br>')
        
        if in_table:
            html_lines.append('</table>')
        
        return '\n'.join(html_lines)
    
    def _load_ieee_logo(self):
        """Load IEEE logo and convert to base64."""
        try:
            logo_path = os.path.join(os.path.dirname(__file__), 'IEEE-Logo.jpg')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                return base64.b64encode(logo_data).decode('utf-8')
            else:
                # Return empty string if logo not found
                return ""
        except Exception:
            return ""
    
    async def generate_pdf_async(self, article_text, title="Research Article", output_path=None):
        """Generate PDF from article using Playwright + MathJax."""
        # Convert markdown to HTML
        html_content = self.markdown_to_html(article_text)
        
        # Create full HTML document
        full_html = self.html_template.format(
            title=title,
            content=html_content,
            ieee_logo_base64=self.ieee_logo_base64
        )
        
        # Use Playwright to render and export PDF
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Load HTML content and wait for network to be idle
            await page.set_content(full_html, wait_until='networkidle')
            
            # CRITICAL: Wait for MathJax to load and render completely
            # This is the key to making formulas appear in the PDF
            
            # Step 1: Wait for MathJax script to load
            await page.wait_for_function('typeof MathJax !== "undefined"', timeout=30000)
            
            # Step 2: Wait for MathJax to be ready
            await page.wait_for_function('window.mathJaxReady === true', timeout=30000)
            
            # Step 3: Give MathJax extra time to render all formulas
            # This is crucial - MathJax needs time to process all math in the document
            await asyncio.sleep(5)
            
            # Step 4: Verify formulas are actually rendered by checking for MathJax output
            # MathJax adds specific classes when it renders formulas
            has_rendered = await page.evaluate('''
                () => {
                    const mjxContainers = document.querySelectorAll('.MJX-TEX, mjx-container, .mjx-chtml');
                    return mjxContainers.length > 0;
                }
            ''')
            
            if not has_rendered:
                # If no MathJax output detected, wait longer
                await asyncio.sleep(5)
            
            # Generate PDF
            pdf_bytes = await page.pdf(
                format='Letter',
                margin={
                    'top': '1in',
                    'right': '1in',
                    'bottom': '1in',
                    'left': '1in'
                },
                print_background=True
            )
            
            await browser.close()
            
            # Save to file if specified
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
            
            return BytesIO(pdf_bytes)
    
    def generate_pdf(self, article_text, title="Research Article", output_path=None):
        """Synchronous wrapper for async PDF generation."""
        return asyncio.run(self.generate_pdf_async(article_text, title, output_path))


# Test the generator
if __name__ == "__main__":
    import json
    
    print("Testing HTML-to-PDF Generator with MathJax...")
    print("="*70)
    
    # Load article from cache
    with open('.ui_cache/ui_state.json', 'r') as f:
        cache = json.load(f)
    
    article = cache.get('generated_article', '')
    
    generator = HTMLMathJaxPDFGenerator()
    
    try:
        pdf_buffer = generator.generate_pdf(article, "Video Inpainting and Restoration", "MATHJAX_PERFECT.pdf")
        print(f"✅ PDF generated: {len(pdf_buffer.getvalue())} bytes")
        print("   Saved to: MATHJAX_PERFECT.pdf")
        print("\n🎉 SUCCESS! Open MATHJAX_PERFECT.pdf to see perfect formula rendering!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
