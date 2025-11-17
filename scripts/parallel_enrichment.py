#!/usr/bin/env python3
"""
Parallel Google Maps enrichment coordinator.
Splits remaining companies into chunks and processes them in parallel.
"""

import csv
import json
import sys
from pathlib import Path

# Configuration
NUM_WORKERS = 16
CHECKPOINT_FILE = Path("data/working/.checkpoint_enrichment.json")
INPUT_CSV = Path("data/working/companies_merged.csv")
CHUNK_DIR = Path("data/working/chunks")

def main():
    # Load and validate checkpoint file
    processed_indices = set()

    try:
        if CHECKPOINT_FILE.exists():
            with open(CHECKPOINT_FILE, 'r') as f:
                checkpoint_data = json.load(f)

            # Validate checkpoint structure
            if not isinstance(checkpoint_data, dict):
                raise ValueError("Checkpoint file must contain a JSON object/dictionary")

            # Validate processed_indices field
            processed_indices_data = checkpoint_data.get("processed_indices", [])
            if not isinstance(processed_indices_data, list):
                raise ValueError("'processed_indices' must be a list")

            # Validate all indices are integers and within reasonable bounds
            MAX_INDEX = 1000000  # Reasonable upper limit
            for idx in processed_indices_data:
                if not isinstance(idx, int):
                    raise ValueError(f"Invalid index type: {type(idx)}, expected int")
                if idx < 0 or idx > MAX_INDEX:
                    raise ValueError(f"Index {idx} out of bounds (0-{MAX_INDEX})")

            processed_indices = set(processed_indices_data)
            print(f"Loaded checkpoint with {len(processed_indices)} processed companies")

    except FileNotFoundError:
        print("No checkpoint file found, starting fresh")
        processed_indices = set()

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Warning: Invalid checkpoint file, starting fresh. Error: {e}")
        processed_indices = set()

        # Backup corrupted checkpoint
        if CHECKPOINT_FILE.exists():
            backup_path = CHECKPOINT_FILE.with_suffix('.corrupt.json')
            CHECKPOINT_FILE.rename(backup_path)
            print(f"Corrupted checkpoint backed up to: {backup_path}")

    # Load all companies
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_companies = list(reader)

    total_companies = len(all_companies)
    print(f"Total companies: {total_companies}")

    # Filter to Path A companies (with Website) and add index
    path_a_companies = []
    for idx, company in enumerate(all_companies):
        if company.get('Website'):
            company['original_index'] = idx
            path_a_companies.append(company)

    # Get unprocessed companies
    unprocessed = [c for c in path_a_companies if c['original_index'] not in processed_indices]
    print(f"Unprocessed companies: {len(unprocessed)}")

    if len(unprocessed) == 0:
        print("All companies already processed!")
        return

    # Create chunk directory
    CHUNK_DIR.mkdir(exist_ok=True)

    # Split into chunks
    chunk_size = (len(unprocessed) + NUM_WORKERS - 1) // NUM_WORKERS
    chunks = []

    for i in range(NUM_WORKERS):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(unprocessed))

        if start_idx >= len(unprocessed):
            break

        chunk_companies = unprocessed[start_idx:end_idx]
        chunk_file = CHUNK_DIR / f"chunk_{i}.csv"

        # Write chunk to CSV
        if chunk_companies:
            with open(chunk_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=chunk_companies[0].keys())
                writer.writeheader()
                writer.writerows(chunk_companies)

            chunks.append({
                'worker_id': i,
                'chunk_file': str(chunk_file),
                'start_index': int(chunk_companies[0]['original_index']),
                'end_index': int(chunk_companies[-1]['original_index']),
                'size': len(chunk_companies)
            })

            print(f"Worker {i}: {len(chunk_companies)} companies (indices {chunks[-1]['start_index']}-{chunks[-1]['end_index']})")

    # Write worker config
    config_file = CHUNK_DIR / "worker_config.json"
    with open(config_file, 'w') as f:
        json.dump(chunks, f, indent=2)

    print(f"\nCreated {len(chunks)} chunks")
    print(f"Config saved to: {config_file}")
    print("\nTo run workers in parallel, use:")
    for i in range(len(chunks)):
        print(f"  ./venv/bin/python3 scripts/worker_enrichment.py {i} &")

if __name__ == "__main__":
    main()
