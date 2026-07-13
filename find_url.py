"""
Backward-compatible entry point for website discovery.

The implementation now lives in run_search.py and the search/ package:
- config/keywords.yaml controls country and industry expansion
- search/engines/ contains DuckDuckGo and Bing plugins
- search/aggregator.py deduplicates domains and isolates engine failures

Existing usage still works:
    python find_url.py
"""

from run_search import main, run_search


if __name__ == "__main__":
    main()
