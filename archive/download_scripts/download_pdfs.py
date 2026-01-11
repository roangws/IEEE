#!/usr/bin/env python3
"""
Batch PDF Downloader
Downloads PDFs from aggregated_pdf_links.csv in configurable batches with progress tracking.
"""

import pandas as pd
import urllib.request
import urllib.error
from pathlib import Path
import time
import json
import sys


class PDFDownloader:
    def __init__(self, csv_file="aggregated_pdf_links.csv", output_dir="downloaded_pdfs", 
                 progress_file="download_progress.json"):
        self.csv_file = csv_file
        self.output_dir = Path(output_dir)
        self.progress_file = progress_file
        self.output_dir.mkdir(exist_ok=True)
        
    def load_progress(self):
        if Path(self.progress_file).exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {"downloaded": [], "failed": [], "last_index": 0}
    
    def save_progress(self, progress):
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def download_pdf(self, url, filename):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
                
                if len(content) < 1000:
                    return False, "File too small (likely not a PDF)"
                
                with open(filename, 'wb') as f:
                    f.write(content)
                
                return True, None
                
        except urllib.error.HTTPError as e:
            return False, f"HTTP {e.code}"
        except urllib.error.URLError as e:
            return False, f"URL Error: {e.reason}"
        except Exception as e:
            return False, str(e)
    
    def download_batch(self, batch_size=50, start_index=None):
        if not Path(self.csv_file).exists():
            print(f"Error: {self.csv_file} not found. Run aggregate_pdf_links.py first.")
            sys.exit(1)
        
        df = pd.read_csv(self.csv_file)
        total_links = len(df)
        
        progress = self.load_progress()
        
        if start_index is not None:
            current_index = start_index
        else:
            current_index = progress["last_index"]
        
        if current_index >= total_links:
            print("✓ All PDFs have been processed!")
            print(f"Total downloaded: {len(progress['downloaded'])}")
            print(f"Total failed: {len(progress['failed'])}")
            return
        
        end_index = min(current_index + batch_size, total_links)
        
        print("=" * 70)
        print("PDF BATCH DOWNLOADER")
        print("=" * 70)
        print(f"Total PDFs in list: {total_links}")
        print(f"Already downloaded: {len(progress['downloaded'])}")
        print(f"Already failed: {len(progress['failed'])}")
        print(f"Current batch: {current_index + 1} to {end_index}")
        print(f"Batch size: {end_index - current_index}")
        print("=" * 70)
        
        batch_downloaded = 0
        batch_failed = 0
        
        for idx in range(current_index, end_index):
            url = df.iloc[idx]["PDF Link"]
            
            if pd.isna(url) or str(url).strip() == "":
                continue
            
            url = str(url).strip()
            
            arnumber = url.split("arnumber=")[-1] if "arnumber=" in url else f"pdf_{idx}"
            filename = self.output_dir / f"{arnumber}.pdf"
            
            if filename.exists():
                print(f"[{idx + 1}/{total_links}] ⊙ Already exists: {arnumber}.pdf")
                if url not in progress["downloaded"]:
                    progress["downloaded"].append(url)
                continue
            
            print(f"[{idx + 1}/{total_links}] ↓ Downloading: {arnumber}.pdf", end=" ... ")
            
            success, error = self.download_pdf(url, filename)
            
            if success:
                print("✓")
                batch_downloaded += 1
                if url not in progress["downloaded"]:
                    progress["downloaded"].append(url)
            else:
                print(f"✗ ({error})")
                batch_failed += 1
                if url not in progress["failed"]:
                    progress["failed"].append({"url": url, "error": error, "index": idx})
            
            progress["last_index"] = idx + 1
            self.save_progress(progress)
            
            time.sleep(0.5)
        
        print("=" * 70)
        print("BATCH COMPLETE")
        print("=" * 70)
        print(f"This batch - Downloaded: {batch_downloaded}, Failed: {batch_failed}")
        print(f"Total progress - Downloaded: {len(progress['downloaded'])}, Failed: {len(progress['failed'])}")
        print(f"Remaining: {total_links - progress['last_index']}")
        print(f"Progress: {progress['last_index']}/{total_links} ({progress['last_index']/total_links*100:.1f}%)")
        print("=" * 70)
        
        if progress["last_index"] < total_links:
            print(f"\nTo continue, run: venv/bin/python download_pdfs.py {batch_size}")
        else:
            print("\n✓ All PDFs processed!")


def main():
    batch_size = 50
    start_index = None
    
    if len(sys.argv) > 1:
        try:
            batch_size = int(sys.argv[1])
        except ValueError:
            print("Usage: python download_pdfs.py [batch_size] [start_index]")
            print("Example: python download_pdfs.py 100")
            print("Example: python download_pdfs.py 50 200")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            start_index = int(sys.argv[2])
        except ValueError:
            print("Invalid start_index. Must be an integer.")
            sys.exit(1)
    
    downloader = PDFDownloader()
    downloader.download_batch(batch_size=batch_size, start_index=start_index)


if __name__ == "__main__":
    main()
