#!/usr/bin/env python3
"""
Demo script using Cursor IDE's built-in browser.
Shows the scraping process using Cursor browser MCP tools.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("DUCATI SCRAPER DEMO - Cursor Browser Mode")
print("=" * 80)
print("\nThis demo uses Cursor IDE's built-in browser.")
print("The browser will open in Cursor and you can watch the scraping process.\n")

# Example URLs
demo_urls = [
    ("1", "https://www.ducati.com/ww/en/bikes/multistrada/multistrada-v4-rally", "Multistrada V4 Rally"),
    ("2", "https://www.ducati.com/ww/en/bikes/hypermotard/hypermotard-v2", "Hypermotard V2"),
    ("3", "https://www.ducati.com/ww/en/bikes/scrambler", "Scrambler Category"),
    ("4", "https://www.ducati.com/ww/en/stories/travel/road-to-olympus-multistrada-v4-rally", "Travel Story"),
    ("5", "https://www.ducati.com/ww/en/bikes/offroad/desmo250-mx", "Desmo250 MX"),
]

print("Available demo pages:")
for num, url, name in demo_urls:
    print(f"  {num}. {name}")
    print(f"     {url}")

print("\nNote: This script uses Cursor's browser MCP tools.")
print("The browser will be controlled through Cursor IDE.\n")

# Get URL from command line or use default
if len(sys.argv) > 1:
    target_url = sys.argv[1]
    print(f"🎯 Using URL from command line: {target_url}\n")
else:
    target_url = demo_urls[0][1]
    print(f"🎯 Using default URL: {target_url}\n")

print("=" * 80)
print("INSTRUCTIONS FOR CURSOR BROWSER")
print("=" * 80)
print("""
To use Cursor's browser for scraping:

1. The browser will open in Cursor IDE
2. I will navigate to the page
3. I will extract content and images
4. You can watch the process in real-time

The scraping will happen through Cursor's browser MCP tools.
All actions will be visible in the Cursor browser window.

Ready to start? The browser will open now...
""")


