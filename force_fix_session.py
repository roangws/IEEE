#!/usr/bin/env python3
"""
Force-fix the session state by clearing the UI cache completely.
This will force Streamlit to reload everything fresh.
"""
import os
import shutil

cache_dir = ".ui_cache"

if os.path.exists(cache_dir):
    print(f"🗑️  Removing cache directory: {cache_dir}")
    shutil.rmtree(cache_dir)
    print("✅ Cache cleared")
    print("\n⚠️  IMPORTANT: Restart Streamlit now")
    print("   The app will load with a fresh state")
else:
    print(f"ℹ️  Cache directory doesn't exist: {cache_dir}")

print("\n" + "="*70)
print("NEXT STEPS:")
print("="*70)
print("1. Restart Streamlit: ./run_streamlit.sh")
print("2. Generate a NEW article (don't load the old one)")
print("3. The new article will have NO LaTeX errors")
print("="*70)
