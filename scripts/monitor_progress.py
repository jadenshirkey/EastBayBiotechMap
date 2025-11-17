#!/usr/bin/env python3
"""Monitor enrichment progress in real-time."""

import time
import csv
from pathlib import Path
from datetime import datetime

CHUNKS_DIR = Path("data/working/chunks")
TOTAL_COMPANIES = 1941
NUM_WORKERS = 16

print("=" * 70)
print("LIVE ENRICHMENT PROGRESS MONITOR")
print("=" * 70)
print(f"Target: {TOTAL_COMPANIES} companies across {NUM_WORKERS} workers")
print("=" * 70)
print()

start_time = time.time()

while True:
    # Count enriched files and companies
    enriched_files = list(CHUNKS_DIR.glob("chunk_*_enriched.csv"))
    total_enriched = 0

    worker_status = []
    for i in range(NUM_WORKERS):
        chunk_file = CHUNKS_DIR / f"chunk_{i}_enriched.csv"
        if chunk_file.exists():
            with open(chunk_file, 'r', encoding='utf-8') as f:
                count = sum(1 for _ in f) - 1  # Subtract header
                total_enriched += count
                worker_status.append(f"W{i:02d}: ✓ ({count})")
        else:
            worker_status.append(f"W{i:02d}: ...")

    # Calculate progress
    completed_workers = len(enriched_files)
    progress_pct = (total_enriched / TOTAL_COMPANIES * 100) if TOTAL_COMPANIES > 0 else 0
    elapsed = time.time() - start_time

    # Clear screen (for terminal) and show status
    print(f"\r\033[K[{datetime.now().strftime('%H:%M:%S')}] "
          f"Workers: {completed_workers}/{NUM_WORKERS} | "
          f"Enriched: {total_enriched}/{TOTAL_COMPANIES} ({progress_pct:.1f}%) | "
          f"Elapsed: {int(elapsed)}s", end='', flush=True)

    # Check if complete
    if completed_workers == NUM_WORKERS:
        print("\n\n✓ All workers completed!")
        print("=" * 70)
        print(f"Total enriched: {total_enriched} companies")
        print(f"Total time: {int(elapsed)}s ({elapsed/60:.1f} minutes)")
        print("=" * 70)
        break

    time.sleep(10)
