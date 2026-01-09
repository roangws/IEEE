#!/usr/bin/env python3
"""
Simple LaTeX to Image using online API (latex.codecogs.com)
No additional dependencies needed - uses requests which is already installed.
"""
import re
import hashlib
import urllib.parse
import urllib.request
from io import BytesIO
from pathlib import Path

class LaTeXImageRenderer:
    """Renders LaTeX to images using CodeCogs API."""
    
    def __init__(self, cache_dir=".latex_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        # CodeCogs API endpoint
        self.api_url = "https://latex.codecogs.com/png.latex"
    
    def _get_cache_path(self, latex: str) -> Path:
        formula_hash = hashlib.md5(latex.encode()).hexdigest()
        return self.cache_dir / f"{formula_hash}.png"
    
    def render_to_image(self, latex: str, dpi=150) -> BytesIO:
        """Render LaTeX to PNG using CodeCogs API."""
        cache_path = self._get_cache_path(latex)
        
        # Check cache
        if cache_path.exists():
            with open(cache_path, 'rb') as f:
                img_data = BytesIO(f.read())
                img_data.seek(0)
                return img_data
        
        try:
            # Build API URL
            # Add \dpi{} command for quality
            latex_with_dpi = f"\\dpi{{{dpi}}} {latex}"
            encoded_latex = urllib.parse.quote(latex_with_dpi)
            url = f"{self.api_url}?{encoded_latex}"
            
            # Fetch image
            response = urllib.request.urlopen(url, timeout=10)
            img_data = response.read()
            
            # Cache it
            with open(cache_path, 'wb') as f:
                f.write(img_data)
            
            # Return as BytesIO
            img_buffer = BytesIO(img_data)
            img_buffer.seek(0)
            return img_buffer
            
        except Exception as e:
            print(f"Error rendering LaTeX: {latex[:50]}... - {e}")
            return None
    
    def extract_and_render_formulas(self, text: str) -> dict:
        """
        Extract formulas and render them to images.
        
        Returns:
            dict: {placeholder: (original_latex, image_buffer, is_display)}
        """
        formula_map = {}
        
        # Find display math ($$...$$)
        display_formulas = list(re.finditer(r'\$\$(.*?)\$\$', text, re.DOTALL))
        
        # Find inline math ($...$)
        inline_formulas = list(re.finditer(r'(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)', text))
        
        # Combine and sort by position
        all_formulas = []
        for match in display_formulas:
            all_formulas.append((match.group(1).strip(), True, match.start(), match.end()))
        for match in inline_formulas:
            all_formulas.append((match.group(1).strip(), False, match.start(), match.end()))
        
        all_formulas.sort(key=lambda x: x[2])
        
        # Render each formula
        for i, (formula, is_display, start, end) in enumerate(all_formulas):
            img_buffer = self.render_to_image(formula)
            if img_buffer:
                placeholder = f"[LATEX_IMG_{i}]"
                formula_map[placeholder] = (formula, img_buffer, is_display)
        
        return formula_map


# Test
if __name__ == "__main__":
    renderer = LaTeXImageRenderer()
    
    # Test with the problematic formula
    test_latex = r"q\left(\mathbf{x}_t \mid \mathbf{x}_{t-1}\right) = \mathcal{N}\left(\mathbf{x}_t; \sqrt{\alpha_t}\mathbf{x}_{t-1}, \left(1-\alpha_t\right)\mathbf{I}\right)"
    
    print("Testing LaTeX to Image Renderer (CodeCogs API)...")
    print(f"Formula: {test_latex[:60]}...")
    
    img = renderer.render_to_image(test_latex)
    if img:
        print(f"✅ Successfully rendered ({len(img.getvalue())} bytes)")
        print(f"   Cached at: {renderer._get_cache_path(test_latex)}")
    else:
        print("❌ Failed to render")
    
    # Test extraction
    test_text = """
    The diffusion process is $q(x_t | x_{t-1})$ and:
    $$
    E = mc^2
    $$
    """
    
    formula_map = renderer.extract_and_render_formulas(test_text)
    print(f"\n✅ Extracted and rendered {len(formula_map)} formulas")
    for placeholder, (latex, img, is_display) in formula_map.items():
        print(f"   {placeholder}: {'Display' if is_display else 'Inline'} - {len(img.getvalue())} bytes")
