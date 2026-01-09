#!/usr/bin/env python3
"""
IEEE PDF Batch Downloader with Session Support
Downloads PDFs from IEEE Xplore with proper session handling and authentication support.
"""

import pandas as pd
import requests
from pathlib import Path
import time
import json
import sys


class IEEEDownloader:
    def __init__(self, csv_file="aggregated_pdf_links.csv", output_dir="downloaded_pdfs", 
                 progress_file="download_progress.json", cookies_file="ieee_cookies.json"):
        self.csv_file = csv_file
        self.output_dir = Path(output_dir)
        self.progress_file = progress_file
        self.cookies_file = cookies_file
        self.output_dir.mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.load_cookies()
    
    def load_cookies(self):
        if Path(self.cookies_file).exists():
            try:
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                    for cookie in cookies:
                        self.session.cookies.set(cookie['name'], cookie['value'], 
                                                domain=cookie.get('domain', '.ieee.org'))
                print(f"✓ Loaded cookies from {self.cookies_file}")
            except Exception as e:
                print(f"⚠ Could not load cookies: {e}")
    
    def save_cookies_instructions(self):
        instructions = """
To download PDFs from IEEE Xplore, you need to be authenticated.

SETUP INSTRUCTIONS:
1. Open your browser and log into IEEE Xplore (https://ieeexplore.ieee.org/)
2. Open Developer Tools (F12 or Cmd+Option+I)
3. Go to the Console tab
4. Paste this code and press Enter:

copy(JSON.stringify(document.cookie.split('; ').map(c => {
  const [name, value] = c.split('=');
  return {name, value, domain: '.ieee.org'};
})))

5. The cookies are now in your clipboard
6. Create a file named 'ieee_cookies.json' in this directory
7. Paste the cookies into that file
8. Run this script again

Alternatively, if your institution has IEEE access, you can:
- Connect to your institution's VPN
- Or access from your institution's network
- Then run this script (cookies may not be needed)
"""
        print(instructions)
        with open("SETUP_INSTRUCTIONS.txt", "w") as f:
            f.write(instructions)
        print("\n✓ Instructions saved to SETUP_INSTRUCTIONS.txt")
    
    def load_progress(self):
        if Path(self.progress_file).exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {"downloaded": [], "failed": [], "last_index": 0}
    
    def save_progress(self, progress):
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def get_pdf_url(self, stamp_url):
        arnumber = stamp_url.split("arnumber=")[-1] if "arnumber=" in stamp_url else None
        if arnumber:
            return f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnumber}"
        return None
    
    def download_pdf(self, url, filename):
        try:
            pdf_url = self.get_pdf_url(url)
            if not pdf_url:
                return False, "Could not extract arnumber"
            
            response = self.session.get(pdf_url, timeout=30, allow_redirects=True)
            
            if response.status_code == 418:
                return False, "Bot detected (418)"
            
            if response.status_code == 401 or response.status_code == 403:
                return False, "Authentication required"
            
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}"
            
            content_type = response.headers.get('Content-Type', '')
            
            if 'text/html' in content_type:
                if len(response.content) < 50000:
                    return False, "HTML page (auth required)"
                
            if 'application/pdf' not in content_type and len(response.content) < 50000:
                return False, f"Not a PDF ({content_type})"
            
            if len(response.content) < 10000:
                return False, "File too small"
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content) / 1024
            return True, f"{file_size:.1f}KB"
            
        except requests.exceptions.Timeout:
            return False, "Timeout"
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)[:50]}"
        except Exception as e:
            return False, str(e)[:50]
    
    def download_batch(self, batch_size=50, start_index=None, delay=1.0):
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
        print("IEEE PDF BATCH DOWNLOADER v2")
        print("=" * 70)
        print(f"Total PDFs in list: {total_links}")
        print(f"Already downloaded: {len(progress['downloaded'])}")
        print(f"Already failed: {len(progress['failed'])}")
        print(f"Current batch: {current_index + 1} to {end_index}")
        print(f"Batch size: {end_index - current_index}")
        print(f"Delay between downloads: {delay}s")
        print("=" * 70)
        
        batch_downloaded = 0
        batch_failed = 0
        auth_errors = 0
        
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
            
            success, message = self.download_pdf(url, filename)
            
            if success:
                print(f"✓ ({message})")
                batch_downloaded += 1
                if url not in progress["downloaded"]:
                    progress["downloaded"].append(url)
            else:
                print(f"✗ ({message})")
                batch_failed += 1
                if "auth" in message.lower() or "418" in message:
                    auth_errors += 1
                if url not in progress["failed"]:
                    progress["failed"].append({"url": url, "error": message, "index": idx})
            
            progress["last_index"] = idx + 1
            self.save_progress(progress)
            
            if auth_errors >= 3:
                print("\n" + "=" * 70)
                print("⚠ AUTHENTICATION REQUIRED")
                print("=" * 70)
                print("Multiple authentication errors detected.")
                self.save_cookies_instructions()
                return
            
            time.sleep(delay)
        
        print("=" * 70)
        print("BATCH COMPLETE")
        print("=" * 70)
        print(f"This batch - Downloaded: {batch_downloaded}, Failed: {batch_failed}")
        print(f"Total progress - Downloaded: {len(progress['downloaded'])}, Failed: {len(progress['failed'])}")
        print(f"Remaining: {total_links - progress['last_index']}")
        print(f"Progress: {progress['last_index']}/{total_links} ({progress['last_index']/total_links*100:.1f}%)")
        print("=" * 70)
        
        if progress["last_index"] < total_links:
            print(f"\nTo continue, run: venv/bin/python download_pdfs_v2.py {batch_size}")
        else:
            print("\n✓ All PDFs processed!")


def main():
    batch_size = 50
    start_index = None
    delay = 1.0
    
    if len(sys.argv) > 1:
        try:
            batch_size = int(sys.argv[1])
        except ValueError:
            print("Usage: python download_pdfs_v2.py [batch_size] [start_index] [delay]")
            print("Example: python download_pdfs_v2.py 100")
            print("Example: python download_pdfs_v2.py 50 200 2.0")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            start_index = int(sys.argv[2])
        except ValueError:
            print("Invalid start_index. Must be an integer.")
            sys.exit(1)
    
    if len(sys.argv) > 3:
        try:
            delay = float(sys.argv[3])
        except ValueError:
            print("Invalid delay. Must be a number.")
            sys.exit(1)
    
    downloader = IEEEDownloader()
    downloader.download_batch(batch_size=batch_size, start_index=start_index, delay=delay)


if __name__ == "__main__":
    main()
