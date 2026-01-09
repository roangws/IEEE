#!/usr/bin/env python3
"""
Multi-threaded IEEE PDF Batch Downloader
Downloads PDFs in parallel with CSV-based progress tracking.
"""

import pandas as pd
import requests
from pathlib import Path
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import os


class ParallelIEEEDownloader:
    def __init__(self, csv_file="aggregated_pdf_links.csv", output_dir="downloaded_pdfs"):
        self.csv_file = csv_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.csv_lock = Lock()
        self.stats_lock = Lock()
        
        self.stats = {
            'downloaded': 0,
            'failed': 0,
            'skipped': 0,
            'total': 0
        }
    
    def create_session(self):
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
        return session
    
    def load_or_create_tracking_csv(self):
        if not Path(self.csv_file).exists():
            print(f"Error: {self.csv_file} not found.")
            sys.exit(1)
        
        df = pd.read_csv(self.csv_file)
        
        if 'Download_Status' not in df.columns:
            df['Download_Status'] = 'pending'
            df['File_Size_KB'] = None
            df['Error_Message'] = None
            df['Downloaded_At'] = None
            print("✓ Added tracking columns to CSV")
        
        return df
    
    def save_tracking_csv(self, df):
        with self.csv_lock:
            df.to_csv(self.csv_file, index=False)
    
    def get_pdf_url(self, stamp_url):
        arnumber = stamp_url.split("arnumber=")[-1] if "arnumber=" in stamp_url else None
        if arnumber:
            return f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnumber}"
        return None
    
    def download_single_pdf(self, row_data):
        idx, url = row_data
        session = self.create_session()
        
        try:
            if pd.isna(url) or str(url).strip() == "":
                return idx, 'skipped', None, "Empty URL"
            
            url = str(url).strip()
            arnumber = url.split("arnumber=")[-1] if "arnumber=" in url else f"pdf_{idx}"
            filename = self.output_dir / f"{arnumber}.pdf"
            
            if filename.exists():
                file_size = os.path.getsize(filename) / 1024
                return idx, 'skipped', file_size, "Already exists"
            
            pdf_url = self.get_pdf_url(url)
            if not pdf_url:
                return idx, 'failed', None, "Could not extract arnumber"
            
            response = session.get(pdf_url, timeout=30, allow_redirects=True)
            
            if response.status_code == 418:
                return idx, 'failed', None, "Bot detected (418)"
            
            if response.status_code in [401, 403]:
                return idx, 'failed', None, "Authentication required"
            
            if response.status_code != 200:
                return idx, 'failed', None, f"HTTP {response.status_code}"
            
            content_type = response.headers.get('Content-Type', '')
            
            if 'text/html' in content_type and len(response.content) < 50000:
                return idx, 'failed', None, "HTML page (auth required)"
            
            if 'application/pdf' not in content_type and len(response.content) < 50000:
                return idx, 'failed', None, "Not a PDF"
            
            if len(response.content) < 10000:
                return idx, 'failed', None, "File too small"
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content) / 1024
            return idx, 'success', file_size, None
            
        except requests.exceptions.Timeout:
            return idx, 'failed', None, "Timeout"
        except requests.exceptions.RequestException as e:
            return idx, 'failed', None, f"Request error: {str(e)[:50]}"
        except Exception as e:
            return idx, 'failed', None, str(e)[:50]
        finally:
            session.close()
    
    def update_stats(self, status):
        with self.stats_lock:
            if status == 'success':
                self.stats['downloaded'] += 1
            elif status == 'failed':
                self.stats['failed'] += 1
            elif status == 'skipped':
                self.stats['skipped'] += 1
    
    def download_batch(self, batch_size=100, num_threads=5, start_index=None):
        df = self.load_or_create_tracking_csv()
        total_links = len(df)
        
        if start_index is not None:
            current_index = start_index
        else:
            pending_mask = df['Download_Status'] == 'pending'
            if pending_mask.any():
                current_index = df[pending_mask].index[0]
            else:
                current_index = 0
        
        end_index = min(current_index + batch_size, total_links)
        
        already_downloaded = (df['Download_Status'] == 'success').sum()
        already_failed = (df['Download_Status'] == 'failed').sum()
        
        print("=" * 70)
        print("MULTI-THREADED IEEE PDF DOWNLOADER")
        print("=" * 70)
        print(f"Total PDFs in list: {total_links}")
        print(f"Already downloaded: {already_downloaded}")
        print(f"Already failed: {already_failed}")
        print(f"Current batch: {current_index + 1} to {end_index}")
        print(f"Batch size: {end_index - current_index}")
        print(f"Number of threads: {num_threads}")
        print("=" * 70)
        
        batch_df = df.iloc[current_index:end_index].copy()
        download_tasks = [(idx, row['PDF Link']) for idx, row in batch_df.iterrows()]
        
        self.stats['total'] = len(download_tasks)
        start_time = time.time()
        auth_errors = 0
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            future_to_task = {executor.submit(self.download_single_pdf, task): task for task in download_tasks}
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                idx, url = task
                
                try:
                    result_idx, status, file_size, error = future.result()
                    
                    self.update_stats(status)
                    
                    arnumber = url.split("arnumber=")[-1] if "arnumber=" in url else f"pdf_{idx}"
                    
                    if status == 'success':
                        df.at[result_idx, 'Download_Status'] = 'success'
                        df.at[result_idx, 'File_Size_KB'] = file_size
                        df.at[result_idx, 'Downloaded_At'] = pd.Timestamp.now()
                        print(f"[{self.stats['downloaded'] + self.stats['failed'] + self.stats['skipped']}/{self.stats['total']}] ✓ {arnumber}.pdf ({file_size:.1f}KB)")
                    elif status == 'skipped':
                        df.at[result_idx, 'Download_Status'] = 'success'
                        if file_size:
                            df.at[result_idx, 'File_Size_KB'] = file_size
                        print(f"[{self.stats['downloaded'] + self.stats['failed'] + self.stats['skipped']}/{self.stats['total']}] ⊙ {arnumber}.pdf (already exists)")
                    else:
                        df.at[result_idx, 'Download_Status'] = 'failed'
                        df.at[result_idx, 'Error_Message'] = error
                        print(f"[{self.stats['downloaded'] + self.stats['failed'] + self.stats['skipped']}/{self.stats['total']}] ✗ {arnumber}.pdf ({error})")
                        
                        if "auth" in error.lower() or "418" in error:
                            auth_errors += 1
                    
                    if (self.stats['downloaded'] + self.stats['failed'] + self.stats['skipped']) % 10 == 0:
                        self.save_tracking_csv(df)
                    
                except Exception as e:
                    print(f"Error processing task: {e}")
        
        self.save_tracking_csv(df)
        
        elapsed_time = time.time() - start_time
        
        print("=" * 70)
        print("BATCH COMPLETE")
        print("=" * 70)
        print(f"Downloaded: {self.stats['downloaded']}")
        print(f"Skipped (already exists): {self.stats['skipped']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"Time elapsed: {elapsed_time:.1f}s")
        print(f"Average speed: {self.stats['total']/elapsed_time:.1f} PDFs/sec")
        print("=" * 70)
        
        total_success = (df['Download_Status'] == 'success').sum()
        total_failed = (df['Download_Status'] == 'failed').sum()
        total_pending = (df['Download_Status'] == 'pending').sum()
        
        print("\nOVERALL PROGRESS:")
        print(f"Total downloaded: {total_success}/{total_links} ({total_success/total_links*100:.1f}%)")
        print(f"Total failed: {total_failed}")
        print(f"Remaining: {total_pending}")
        print("=" * 70)
        
        if auth_errors >= 3:
            print("\n⚠ Multiple authentication errors detected.")
            print("You may need to set up authentication cookies.")
        
        if total_pending > 0:
            print(f"\nTo continue, run: venv/bin/python download_pdfs_parallel.py {batch_size} {num_threads}")
        else:
            print("\n✓ All PDFs processed!")


def main():
    batch_size = 100
    num_threads = 5
    start_index = None
    
    if len(sys.argv) > 1:
        try:
            batch_size = int(sys.argv[1])
        except ValueError:
            print("Usage: python download_pdfs_parallel.py [batch_size] [num_threads] [start_index]")
            print("Example: python download_pdfs_parallel.py 100 5")
            print("Example: python download_pdfs_parallel.py 200 10 500")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            num_threads = int(sys.argv[2])
        except ValueError:
            print("Invalid num_threads. Must be an integer.")
            sys.exit(1)
    
    if len(sys.argv) > 3:
        try:
            start_index = int(sys.argv[3])
        except ValueError:
            print("Invalid start_index. Must be an integer.")
            sys.exit(1)
    
    downloader = ParallelIEEEDownloader()
    downloader.download_batch(batch_size=batch_size, num_threads=num_threads, start_index=start_index)


if __name__ == "__main__":
    main()
