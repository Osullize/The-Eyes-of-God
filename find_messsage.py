"""
Backward-compatible entry point for company info crawling.

The implementation now lives in run_crawl.py and the crawl/pipeline packages:
- crawl/fetcher.py handles retry, exponential backoff, UA rotation, optional proxy,
  robots.txt checks, and global/per-domain rate limiting.
- crawl/link_explorer.py handles bounded BFS page discovery.
- pipeline/state.py and pipeline/csv_writer.py handle resume state and incremental CSV.

Existing usage still works:
    python find_messsage.py
"""

from run_crawl import main, run_crawl


if __name__ == "__main__":
    main()
