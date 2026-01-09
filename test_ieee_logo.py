#!/usr/bin/env python3
"""
Simple test to verify IEEE logo exists and can be used
"""

import os

# Check if IEEE logo exists
logo_path = "/Users/roan-aparavi/aparavi-repo/Roan-IEEE/IEEE-Logo.jpg"

if os.path.exists(logo_path):
    print(f"✅ IEEE logo found at: {logo_path}")
    print(f"📁 File size: {os.path.getsize(logo_path)} bytes")
    
    # Verify it's a valid image
    try:
        from PIL import Image
        img = Image.open(logo_path)
        print(f"📐 Image dimensions: {img.size[0]} x {img.size[1]} pixels")
        print(f"🎨 Image format: {img.format}")
        print("\n✅ IEEE logo is ready for PDF watermark!")
        print("\nThe watermark will be:")
        print("- Positioned in top-left corner (0.5 inch from left, 10 inches from bottom)")
        print("- Sized at 1 inch wide x 0.5 inch tall")
        print("- Semi-transparent (30% opacity)")
        print("- Applied to ALL pages in the PDF")
    except ImportError:
        print("⚠️ PIL not installed, but logo file exists")
    except Exception as e:
        print(f"⚠️ Error reading image: {e}")
else:
    print(f"❌ IEEE logo NOT found at: {logo_path}")
    print("Please ensure the IEEE-Logo.jpg file exists in the Roan-IEEE directory")
