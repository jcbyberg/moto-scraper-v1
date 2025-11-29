"""Context manager to suppress asyncio cleanup warnings."""

import sys
import warnings
from contextlib import contextmanager


@contextmanager
def suppress_asyncio_warnings():
    """Suppress harmless asyncio cleanup warnings."""
    # Suppress RuntimeWarning about closed event loops
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*Event loop is closed.*")
        warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*coroutine.*was never awaited.*")
        
        # Also redirect stderr for asyncio cleanup errors
        original_stderr = sys.stderr
        
        class FilteredStderr:
            def __init__(self, original):
                self.original = original
                self.buffer = []
            
            def write(self, text):
                # Filter out asyncio cleanup errors
                if "Exception ignored in" in text and "BaseSubprocessTransport" in text:
                    return
                if "RuntimeError: Event loop is closed" in text:
                    return
                self.original.write(text)
            
            def flush(self):
                self.original.flush()
            
            def __getattr__(self, name):
                return getattr(self.original, name)
        
        filtered_stderr = FilteredStderr(original_stderr)
        sys.stderr = filtered_stderr
        
        try:
            yield
        finally:
            sys.stderr = original_stderr


