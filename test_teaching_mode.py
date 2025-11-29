#!/usr/bin/env python3
"""Test script for teaching mode recording functionality."""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Suppress asyncio cleanup warnings (harmless)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

from playwright.async_api import async_playwright
from teaching.session import SessionManager
from teaching.storage import TeachingStorage
from teaching.recorder import InteractionRecorder
from teaching.models import SessionStatus


async def test_recording():
    """Test the recording functionality."""
    print("🧪 Testing Teaching Mode Recording\n")
    
    # Initialize components
    storage = TeachingStorage(Path("teaching_data"))
    session_manager = SessionManager(storage)
    recorder = InteractionRecorder(session_manager, storage, auto_save_interval=5)
    
    # Create a test session
    test_url = "https://example.com"
    session = session_manager.create_session(test_url, "test_session")
    print(f"✅ Created session: {session.session_id}")
    
    # Launch browser (headless for automated testing)
    print("🌐 Launching browser...")
    p = None
    browser = None
    context = None
    page = None
    
    try:
        p = await async_playwright().start()
        browser = await p.chromium.launch(headless=True)  # Headless for automated testing
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # Navigate to test page
        print(f"📄 Navigating to {test_url}...")
        await page.goto(test_url, wait_until='domcontentloaded')
        await asyncio.sleep(1)
        
        # Start recording
        print("🎬 Starting recording...")
        await recorder.start_recording(session, page)
        print("✅ Recording started\n")
        
        # Perform test interactions
        print("🖱️  Performing test interactions...")
        
        # Wait for click tracker to be injected
        await asyncio.sleep(0.5)
        
        # Test 1: Trigger a click event via JavaScript (simulates user click)
        print("  1. Simulating click event...")
        await page.evaluate("""
            const event = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: 100,
                clientY: 100
            });
            document.body.dispatchEvent(event);
        """)
        await asyncio.sleep(0.5)
        print("     ✅ Click event dispatched")
        
        # Test 2: Scroll (programmatic - should be detected by monitor)
        print("  2. Scrolling down...")
        await page.evaluate("window.scrollTo(0, 500)")
        await asyncio.sleep(0.8)  # Give scroll monitor time to detect
        print("     ✅ Scroll executed")
        
        # Test 3: Another scroll
        print("  3. Scrolling down more...")
        await page.evaluate("window.scrollTo(0, 1000)")
        await asyncio.sleep(0.8)
        print("     ✅ Scroll executed")
        
        # Test 4: Scroll back up
        print("  4. Scrolling back up...")
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.8)
        print("     ✅ Scroll executed")
        
        # Test 5: Another click via JavaScript
        print("  5. Simulating another click...")
        await page.evaluate("""
            const event = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: 200,
                clientY: 200
            });
            document.body.dispatchEvent(event);
        """)
        await asyncio.sleep(0.5)
        print("     ✅ Click event dispatched")
        
        print("\n⏹️  Stopping recording...")
        await recorder.stop_recording()
        
        # Get recorded data
        session_data = recorder.get_recorded_data()
        
        # Save final session data
        await storage.save_session_data(session_data)
        
        print(f"\n📊 Recording Results:")
        print(f"   Session ID: {session.session_id}")
        print(f"   Total Interactions: {len(session_data.interactions)}")
        print(f"   Total Screenshots: {len(session_data.screenshots)}")
        print(f"   Session Status: {session.status}")
        
        # Show interaction breakdown
        click_count = sum(1 for i in session_data.interactions if i.event_type.value == "click")
        scroll_count = sum(1 for i in session_data.interactions if i.event_type.value == "scroll")
        nav_count = sum(1 for i in session_data.interactions if i.event_type.value == "navigation")
        
        print(f"\n   Interaction Breakdown:")
        print(f"     - Clicks: {click_count}")
        print(f"     - Scrolls: {scroll_count}")
        print(f"     - Navigations: {nav_count}")
        
        # Verify data was saved
        print(f"\n💾 Verifying data persistence...")
        loaded_data = await storage.load_session_data(session.session_id)
        
        if loaded_data:
            print(f"   ✅ Session data loaded successfully")
            print(f"   ✅ Interactions: {len(loaded_data.interactions)}")
            print(f"   ✅ Screenshots: {len(loaded_data.screenshots)}")
            
            # Check screenshot files exist
            screenshots_dir = storage.get_screenshots_dir(session.session_id)
            screenshot_files = list(screenshots_dir.glob("*.png"))
            print(f"   ✅ Screenshot files: {len(screenshot_files)}")
            
            if len(screenshot_files) > 0:
                print(f"   📸 Sample screenshot: {screenshot_files[0].name}")
        else:
            print(f"   ❌ Failed to load session data")
            return False
        
        # Show sample interaction
        if session_data.interactions:
            print(f"\n📝 Sample Interaction:")
            sample = session_data.interactions[0]
            print(f"   Type: {sample.event_type.value}")
            print(f"   Timestamp: {sample.timestamp}")
            print(f"   Page URL: {sample.page_url}")
            if hasattr(sample, 'element_selector'):
                print(f"   Element: {sample.element_selector}")
            if hasattr(sample, 'scroll_direction'):
                print(f"   Direction: {sample.scroll_direction}")
        
        print(f"\n✅ Test completed successfully!")
        print(f"   Session data saved to: {storage.get_session_dir(session.session_id)}")
        return True
    finally:
        # Ensure cleanup even on error - close in reverse order
        if page:
            try:
                await page.close()
                await asyncio.sleep(0.1)  # Brief pause for cleanup
            except Exception as e:
                logger.debug(f"Error closing page: {e}")
        
        if context:
            try:
                await context.close()
                await asyncio.sleep(0.1)  # Brief pause for cleanup
            except Exception as e:
                logger.debug(f"Error closing context: {e}")
        
        if browser:
            try:
                # Close all remaining contexts
                for ctx in browser.contexts:
                    try:
                        await ctx.close()
                    except:
                        pass
                await browser.close()
                await asyncio.sleep(0.2)  # Pause for browser process cleanup
            except Exception as e:
                logger.debug(f"Error closing browser: {e}")
        
        if p:
            try:
                await p.stop()
                await asyncio.sleep(0.1)  # Pause for playwright cleanup
            except Exception as e:
                logger.debug(f"Error stopping playwright: {e}")


if __name__ == "__main__":
    # Suppress asyncio cleanup warnings
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*Event loop is closed.*")
    
    # Import suppression context manager
    try:
        from suppress_asyncio_warnings import suppress_asyncio_warnings
    except ImportError:
        # Fallback if file doesn't exist
        from contextlib import nullcontext as suppress_asyncio_warnings
    
    with suppress_asyncio_warnings():
        try:
            # Use a new event loop to ensure clean shutdown
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(test_recording())
                # Give time for cleanup
                loop.run_until_complete(asyncio.sleep(0.5))
                sys.exit(0 if result else 1)
            finally:
                # Close the loop properly
                try:
                    # Cancel all pending tasks
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except:
                    pass
                loop.close()
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            sys.exit(130)
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

