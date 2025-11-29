#!/usr/bin/env python3
"""
Wrapper script to run the crawler from project root.
This ensures proper Python path setup.
"""

import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import and run main
from src.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())


