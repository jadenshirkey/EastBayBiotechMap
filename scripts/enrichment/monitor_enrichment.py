#!/usr/bin/env python3
"""
Monitor enrichment progress in real-time
"""

import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.db_manager import DatabaseManager

def get_stats(db):
    """Get current enrichment statistics"""
    cursor = db.connection.cursor()

    stats = {}

    # Total companies
    cursor.execute("SELECT COUNT(*) FROM companies")
    stats['total_companies'] = cursor.fetchone()[0]

    # Companies with current classifications
    cursor.execute("""
        SELECT COUNT(DISTINCT company_id)
        FROM company_classifications
        WHERE is_current = 1
    """)
    stats['classified'] = cursor.fetchone()[0]

    # Companies with SEC data
    cursor.execute("SELECT COUNT(DISTINCT company_id) FROM sec_edgar_data")
    stats['sec_data'] = cursor.fetchone()[0]

    # Companies with clinical trials
    cursor.execute("SELECT COUNT(DISTINCT company_id) FROM clinical_trials")
    stats['ct_data'] = cursor.fetchone()[0]

    # Classification breakdown
    cursor.execute("""
        SELECT company_stage, COUNT(DISTINCT company_id) as count
        FROM company_classifications
        WHERE is_current = 1
        GROUP BY company_stage
    """)
    stats['stages'] = {row[0]: row[1] for row in cursor.fetchall()}

    # Recent API calls
    cursor.execute("""
        SELECT
            api_provider,
            COUNT(*) as calls,
            SUM(CASE WHEN response_status = 200 THEN 1 ELSE 0 END) as success,
            MAX(called_at) as last_call
        FROM api_calls
        WHERE called_at > datetime('now', '-1 hour')
        GROUP BY api_provider
    """)
    stats['recent_api'] = {}
    for row in cursor.fetchall():
        stats['recent_api'][row[0]] = {
            'calls': row[1],
            'success': row[2],
            'last_call': row[3]
        }

    return stats

def print_stats(stats, previous_stats=None):
    """Print statistics"""
    print("\n" + "="*80)
    print(f"ENRICHMENT PROGRESS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    total = stats['total_companies']
    classified = stats['classified']
    unclassified = total - classified

    print(f"\nOVERALL PROGRESS:")
    print(f"  Total companies: {total}")
    print(f"  Classified: {classified} ({classified/total*100:.1f}%)")
    print(f"  Unclassified: {unclassified} ({unclassified/total*100:.1f}%)")

    if previous_stats:
        newly_classified = classified - previous_stats['classified']
        if newly_classified > 0:
            print(f"  Newly classified (since last check): {newly_classified}")

    print(f"\nDATA SOURCES:")
    print(f"  Companies with SEC data: {stats['sec_data']}")
    print(f"  Companies with clinical trials: {stats['ct_data']}")

    if previous_stats:
        sec_new = stats['sec_data'] - previous_stats['sec_data']
        ct_new = stats['ct_data'] - previous_stats['ct_data']
        if sec_new > 0:
            print(f"    New SEC data: {sec_new}")
        if ct_new > 0:
            print(f"    New clinical trials: {ct_new}")

    print(f"\nCLASSIFICATION BREAKDOWN:")
    for stage, count in sorted(stats['stages'].items(), key=lambda x: x[1], reverse=True):
        pct = count/total*100
        print(f"  {stage:30s}: {count:4d} ({pct:5.1f}%)")

    print(f"\nRECENT API ACTIVITY (last hour):")
    if stats['recent_api']:
        for api_name, api_stats in stats['recent_api'].items():
            success_rate = (api_stats['success'] / api_stats['calls'] * 100) if api_stats['calls'] > 0 else 0
            print(f"  {api_name:20s}: {api_stats['calls']:4d} calls, {success_rate:5.1f}% success, last: {api_stats['last_call']}")
    else:
        print("  No recent API calls")

def monitor(interval=60, max_iterations=None):
    """Monitor enrichment progress"""
    db = DatabaseManager('data/bayarea_biotech_sources.db')
    previous_stats = None
    iteration = 0

    try:
        while True:
            stats = get_stats(db)
            print_stats(stats, previous_stats)
            previous_stats = stats

            iteration += 1
            if max_iterations and iteration >= max_iterations:
                break

            print(f"\nNext update in {interval} seconds... (Ctrl+C to stop)")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Monitor enrichment progress')
    parser.add_argument('--interval', type=int, default=60, help='Update interval in seconds (default: 60)')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    args = parser.parse_args()

    if args.once:
        db = DatabaseManager('data/bayarea_biotech_sources.db')
        stats = get_stats(db)
        print_stats(stats)
        db.close()
    else:
        monitor(interval=args.interval)
