#!/usr/bin/env python3
"""Quick test of snapshot extraction."""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from extract_from_cursor_browser import process_snapshot

async def test():
    snapshot_file = r"C:\Users\jcbyb\.cursor\browser-logs\snapshot-2025-11-29T21-12-21-685Z.log"
    print(f"Testing extraction from: {snapshot_file}")
    print(f"File exists: {Path(snapshot_file).exists()}")
    
    try:
        result = await process_snapshot(
            snapshot_file=snapshot_file,
            manufacturer="Ducati",
            output_dir="output",
            images_dir="images"
        )
        print("\n✅ Success!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())


