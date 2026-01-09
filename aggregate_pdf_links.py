#!/usr/bin/env python3
"""
Aggregate PDF Links from Multiple CSV Files
Loads all CSV files from data-raw directory and creates a single deduplicated list of PDF links.
"""

import pandas as pd
from pathlib import Path
import sys


def main():
    data_dir = Path("data-raw")
    output_file = "aggregated_pdf_links.csv"
    
    if not data_dir.exists():
        print(f"Error: Directory '{data_dir}' not found.")
        sys.exit(1)
    
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"Error: No CSV files found in '{data_dir}'.")
        sys.exit(1)
    
    print(f"Found {len(csv_files)} CSV file(s) in '{data_dir}'")
    print("-" * 60)
    
    all_pdf_links = []
    files_processed = 0
    files_skipped = 0
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            
            if "PDF Link" not in df.columns:
                print(f"⚠ Skipping {csv_file.name}: 'PDF Link' column not found")
                files_skipped += 1
                continue
            
            pdf_links = df["PDF Link"].tolist()
            all_pdf_links.extend(pdf_links)
            files_processed += 1
            
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_file, encoding='latin-1')
                
                if "PDF Link" not in df.columns:
                    print(f"⚠ Skipping {csv_file.name}: 'PDF Link' column not found")
                    files_skipped += 1
                    continue
                
                pdf_links = df["PDF Link"].tolist()
                all_pdf_links.extend(pdf_links)
                files_processed += 1
                
            except Exception as e:
                print(f"⚠ Skipping {csv_file.name}: Error reading file - {e}")
                files_skipped += 1
                continue
                
        except Exception as e:
            print(f"⚠ Skipping {csv_file.name}: Error - {e}")
            files_skipped += 1
            continue
    
    print("-" * 60)
    print(f"Files processed: {files_processed}")
    print(f"Files skipped: {files_skipped}")
    print(f"Total rows collected: {len(all_pdf_links)}")
    
    result_df = pd.DataFrame(all_pdf_links, columns=["PDF Link"])
    
    result_df = result_df.dropna()
    result_df = result_df[result_df["PDF Link"].astype(str).str.strip() != ""]
    
    rows_after_null_removal = len(result_df)
    print(f"Rows after removing null/empty: {rows_after_null_removal}")
    
    result_df = result_df.drop_duplicates()
    
    final_row_count = len(result_df)
    print(f"Rows after deduplication: {final_row_count}")
    
    result_df.to_csv(output_file, index=False)
    
    print("-" * 60)
    print(f"✓ Output saved to: {output_file}")
    print(f"✓ Final unique PDF links: {final_row_count}")


if __name__ == "__main__":
    main()
