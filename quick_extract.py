#!/usr/bin/env python3
"""Quick extraction test."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test():
    try:
        from extract_with_playwright import extract_page_data
        print("Starting extraction...")
        result = await extract_page_data()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())


