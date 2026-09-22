"""
Split ChEMBL 37 Large Raw CSV into Excel-compatible chunks (e.g. 500,000 rows each).
Retains the header row on every chunk.
"""

import csv
import sys
import time
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config.constants import OUTPUT_DIR

INPUT_CSV = OUTPUT_DIR / "ChEMBL_37_Direct_Raw_Content_Unmapped.csv"
CHUNK_SIZE = 500000  # 500,000 rows per file (Excel limit is 1,048,576)

def split_csv(chunk_size=CHUNK_SIZE):
    if not INPUT_CSV.exists():
        print(f"❌ Error: Input CSV not found at {INPUT_CSV}")
        sys.exit(1)

    print("=" * 70)
    print(f"  SPLITTING ChEMBL 37 RAW CSV INTO CHUNKS ({chunk_size:,} rows/chunk)")
    print("=" * 70)
    print(f"Source File: {INPUT_CSV}")

    chunks_dir = OUTPUT_DIR / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    file_idx = 1
    total_rows = 0
    current_chunk_rows = 0
    current_file = None
    current_writer = None
    headers = []

    with open(INPUT_CSV, "r", encoding="utf-8", newline="") as f_in:
        reader = csv.reader(f_in)
        try:
            headers = next(reader)
        except StopIteration:
            print("❌ Error: Input CSV is empty!")
            return

        def open_new_chunk(idx):
            chunk_path = chunks_dir / f"ChEMBL_37_Direct_Raw_Part_{idx:02d}.csv"
            f_out = open(chunk_path, "w", encoding="utf-8", newline="")
            writer = csv.writer(f_out)
            writer.writerow(headers)
            return f_out, writer, chunk_path

        current_file, current_writer, current_path = open_new_chunk(file_idx)
        created_files = [current_path]

        for row in reader:
            current_writer.writerow(row)
            total_rows += 1
            current_chunk_rows += 1

            if current_chunk_rows >= chunk_size:
                current_file.close()
                print(f"  * Generated Part {file_idx:02d}: {current_path.name} ({current_chunk_rows:,} rows)")
                file_idx += 1
                current_chunk_rows = 0
                current_file, current_writer, current_path = open_new_chunk(file_idx)
                created_files.append(current_path)

        if current_chunk_rows > 0:
            current_file.close()
            print(f"  * Generated Part {file_idx:02d}: {current_path.name} ({current_chunk_rows:,} rows)")
        else:
            # If the last file was empty, remove it
            current_file.close()
            if current_path.exists():
                current_path.unlink()
                created_files.pop()

    elapsed = time.time() - t_start
    print(f"\n[SPLIT COMPLETE] {total_rows:,} records split into {len(created_files)} chunks in {elapsed:.2f}s.")
    print(f"Chunks directory: {chunks_dir}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    split_csv()
