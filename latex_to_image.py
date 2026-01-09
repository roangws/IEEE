#!/usr/bin/env python3
"""
LaTeX to Image Renderer
Converts LaTeX formulas to PNG images for embedding in PDFs.
Uses matplotlib for rendering (no external dependencies needed).
"""
import re
import hashlib
from io import BytesIO
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

class LaTeXRenderer:
    """Renders LaTeX formulas to images."""
    
    def __init__(self, cache_dir=".latex_cache"):
        """Initialize renderer with cache directory."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_path(self, latex: str) -> Path:
        """Get cache file path for a LaTeX formula."""
        formula_hash = hashlib.md5(latex.encode()).hexdigest()
        return self.cache_dir / f"{formula_hash}.png"
    
    def render_to_image(self, latex: str, fontsize=12, dpi=150) -> BytesIO:
        """
        Render LaTeX formula to PNG image.
        
        Args:
            latex: LaTeX formula string (without $ delimiters)
            fontsize: Font size for rendering
            dpi: DPI for image quality
            
        Returns:
            BytesIO object containing PNG image data
        """
        # Check cache first
        cache_path = self._get_cache_path(latex)
        if cache_path.exists():
            with open(cache_path, 'rb') as f:
                img_data = BytesIO(f.read())
                img_data.seek(0)
                return img_data
        
        # Render formula
        fig = plt.figure(figsize=(10, 1))
        fig.patch.set_facecolor('white')
        
        # Add formula as text
        try:
            plt.text(0.5, 0.5, f'${latex}$', 
                    fontsize=fontsize,
                    ha='center', va='center',
                    transform=fig.transFigure)
            plt.axis('off')
            
            # Save to BytesIO
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=dpi, 
                       bbox_inches='tight', pad_inches=0.1,
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            # Cache the image
            img_buffer.seek(0)
            with open(cache_path, 'wb') as f:
                f.write(img_buffer.read())
            
            # Return fresh buffer
            img_buffer.seek(0)
            return img_buffer
            
        except Exception as e:
            plt.close(fig)
            print(f"Error rendering LaTeX: {latex[:50]}... - {e}")
            return None
    
    def extract_formulas(self, text: str) -> list:
        """
        Extract all LaTeX formulas from text.
        
        Returns:
            List of tuples: (formula_text, is_display_math, start_pos, end_pos)
        """
        formulas = []
        
        # Find display math ($$...$$)
        for match in re.finditer(r'\$\$(.*?)\$\$', text, re.DOTALL):
            formulas.append((
                match.group(1).strip(),
                True,  # display math
                match.start(),
                match.end()
            ))
        
        # Find inline math ($...$) - avoid matching $$ 
        for match in re.finditer(r'(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)', text):
            formulas.append((
                match.group(1).strip(),
                False,  # inline math
                match.start(),
                match.end()
            ))
        
        return formulas
    
    def replace_formulas_with_placeholders(self, text: str) -> tuple:
        """
        Replace LaTeX formulas with image placeholders.
        
        Returns:
            (modified_text, formula_map)
            formula_map: dict of {placeholder: (formula, image_buffer, is_display)}
        """
        formulas = self.extract_formulas(text)
        formula_map = {}
        
        # Sort by position (reverse) to replace from end to start
        formulas.sort(key=lambda x: x[2], reverse=True)
        
        modified_text = text
        for i, (formula, is_display, start, end) in enumerate(formulas):
            # Render formula to image
            img_buffer = self.render_to_image(formula)
            
            if img_buffer:
                # Create placeholder
                placeholder = f"[FORMULA_{len(formulas)-i-1}]"
                formula_map[placeholder] = (formula, img_buffer, is_display)
                
                # Replace in text
                modified_text = modified_text[:start] + placeholder + modified_text[end:]
        
        return modified_text, formula_map


# Test the renderer
if __name__ == "__main__":
    renderer = LaTeXRenderer()
    
    # Test formula
    test_latex = r"q\left(\mathbf{x}_t \mid \mathbf{x}_{t-1}\right) = \mathcal{N}\left(\mathbf{x}_t; \sqrt{\alpha_t}\mathbf{x}_{t-1}, \left(1-\alpha_t\right)\mathbf{I}\right)"
    
    print("Testing LaTeX to Image Renderer...")
    print(f"Formula: {test_latex[:50]}...")
    
    img = renderer.render_to_image(test_latex)
    if img:
        print(f"✅ Successfully rendered to image ({len(img.getvalue())} bytes)")
        print(f"   Cached at: {renderer._get_cache_path(test_latex)}")
    else:
        print("❌ Failed to render")
    
    # Test extraction
    test_text = """
    The formula is $x = y + z$ and also:
    $$
    E = mc^2
    $$
    """
    
    formulas = renderer.extract_formulas(test_text)
    print(f"\n✅ Extracted {len(formulas)} formulas from test text")
    for i, (formula, is_display, _, _) in enumerate(formulas):
        print(f"   {i+1}. {'Display' if is_display else 'Inline'}: {formula}")
