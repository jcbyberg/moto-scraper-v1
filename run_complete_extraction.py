#!/usr/bin/env python3
"""Run complete extraction with output."""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def run():
    try:
        from extract_and_download_complete import extract_all_content_and_download_images
        print("Starting complete extraction...")
        result = await extract_all_content_and_download_images()
        if result:
            print("\n✅ SUCCESS!")
            print(f"Images downloaded: {result.get('images_downloaded', 0)}")
            print(f"Content sections: {result.get('content_sections', 0)}")
            print(f"Tooltips: {result.get('tooltips', 0)}")
        else:
            print("\n❌ Extraction returned None")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())


