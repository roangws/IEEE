#!/usr/bin/env python3
"""
Retry downloading only the failed PDFs from the CSV file.
"""

import pandas as pd
import requests
import os
from pathlib import Path
from datetime import datetime
import time

def create_session():
    """Create a session with authentication cookies."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    return session

def download_pdf(session, url, output_dir):
    """Download a single PDF."""
    try:
        # Extract article number from URL
        arnumber = url.split('arnumber=')[1] if 'arnumber=' in url else None
        if not arnumber:
            return None, "Invalid URL format"
        
        filename = output_dir / f"{arnumber}.pdf"
        
        # Check if already exists
        if filename.exists():
            file_size = os.path.getsize(filename) / 1024
            return file_size, "Already exists"
        
        # Download PDF
        pdf_url = f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnumber}"
        response = session.get(pdf_url, timeout=60, allow_redirects=True)
        
        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"
        
        # Save PDF
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        file_size = len(response.content) / 1024
        print(f"✓ {arnumber}.pdf ({file_size:.1f}KB)")
        return file_size, None
        
    except requests.exceptions.Timeout:
        return None, "Timeout"
    except Exception as e:
        return None, str(e)

def main():
    csv_file = Path('aggregated_pdf_links.csv')
    output_dir = Path('downloaded_pdfs')
    output_dir.mkdir(exist_ok=True)
    
    # Read CSV
    print("Loading CSV file...")
    df = pd.read_csv(csv_file)
    
    # Find failed downloads
    failed_mask = df['Download_Status'] == 'failed'
    failed_df = df[failed_mask]
    
    print(f"\nFound {len(failed_df)} failed downloads to retry\n")
    print("="*70)
    
    if len(failed_df) == 0:
        print("No failed downloads to retry!")
        return
    
    session = create_session()
    success_count = 0
    still_failed_count = 0
    
    for idx in failed_df.index:
        url = df.at[idx, 'PDF Link']
        arnumber = url.split('arnumber=')[1] if 'arnumber=' in url else 'unknown'
        
        print(f"Retrying [{idx+1}] {arnumber}.pdf... ", end='', flush=True)
        
        file_size, error = download_pdf(session, url, output_dir)
        
        if error is None:
            # Success
            df.at[idx, 'Download_Status'] = 'success'
            df.at[idx, 'File_Size_KB'] = file_size
            df.at[idx, 'Error_Message'] = None
            df.at[idx, 'Downloaded_At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            success_count += 1
            print(f"SUCCESS")
        elif error == "Already exists":
            # Already downloaded
            df.at[idx, 'Download_Status'] = 'success'
            df.at[idx, 'File_Size_KB'] = file_size
            df.at[idx, 'Error_Message'] = None
            success_count += 1
            print(f"ALREADY EXISTS")
        else:
            # Still failed
            df.at[idx, 'Error_Message'] = error
            still_failed_count += 1
            print(f"FAILED ({error})")
        
        time.sleep(0.5)  # Small delay between requests
    
    # Save updated CSV
    print("\nSaving updated CSV...")
    df.to_csv(csv_file, index=False)
    
    print("\n" + "="*70)
    print("RETRY COMPLETE")
    print("="*70)
    print(f"Successfully downloaded: {success_count}")
    print(f"Still failed: {still_failed_count}")
    print(f"Total in CSV: {len(df)}")
    print(f"Total successful: {len(df[df['Download_Status'] == 'success'])}")
    print("="*70)

if __name__ == '__main__':
    main()
