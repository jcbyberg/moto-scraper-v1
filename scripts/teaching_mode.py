#!/usr/bin/env python3
"""CLI entry point for teaching mode."""

import sys
import asyncio
import argparse
import signal
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright
from teaching.session import SessionManager
from teaching.storage import TeachingStorage
from teaching.recorder import InteractionRecorder
from teaching.models import SessionStatus


# Global variables for cleanup
recorder: InteractionRecorder = None
browser = None
playwright = None


async def start_session(url: str, session_name: str = None, headless: bool = False) -> None:
    """Start a teaching session.
    
    Args:
        url: Target URL to teach navigation for
        session_name: Optional name for the session
        headless: Whether to run in headless mode (not recommended for teaching)
    """
    global recorder, browser, playwright
    
    # Check for display if not headless
    if not headless:
        import os
        display = os.environ.get('DISPLAY')
        if not display:
            print("\n❌ Error: No X server (DISPLAY) available.")
            print("\n   Teaching mode requires a visible browser for user interaction.")
            print("\n   Options:")
            print("   1. Use a machine with a display (desktop/laptop)")
            print("   2. Use X11 forwarding: ssh -X user@server")
            print("   3. Use xvfb for virtual display:")
            print("      xvfb-run -a python3 scripts/teaching_mode.py start <url>")
            print("   4. Use VNC or similar remote desktop solution")
            print("   5. Use --headless flag (limited functionality)")
            print("\n   Note: Headless mode is not ideal for teaching mode")
            print("   as it requires real user interaction with a visible browser.\n")
            raise RuntimeError("No display available for headed browser")
    
    # Initialize components
    storage = TeachingStorage(Path("teaching_data"))
    session_manager = SessionManager(storage)
    recorder = InteractionRecorder(session_manager, storage)
    
    # Create session
    session = session_manager.create_session(url, session_name)
    print(f"📹 Started teaching session: {session.session_id}")
    print(f"   Target URL: {url}")
    print(f"   Session directory: {storage.get_session_dir(session.session_id)}")
    
    if headless:
        print("\n⚠️  WARNING: Running in headless mode.")
        print("   Teaching mode requires user interaction, which is limited in headless mode.")
        print("   Consider using a display or xvfb-run for better results.\n")
    else:
        print("\n🎯 Navigate the website in the browser window.")
        print("   All clicks, scrolls, and navigation will be recorded.")
        print("   Press Ctrl+C to stop recording.\n")
    
    # Launch browser
    playwright_instance = await async_playwright().start()
    playwright = playwright_instance
    
    try:
        browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        )
    except Exception as e:
        if "X server" in str(e) or "DISPLAY" in str(e):
            print("\n❌ Error: Cannot launch browser - no display available.")
            print("\n   Teaching mode requires a visible browser.")
            print("   Try: xvfb-run -a python scripts/teaching_mode.py start <url>")
            raise
        raise
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    
    # Remove webdriver property
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    page = await context.new_page()
    
    # Navigate to target URL
    print(f"🌐 Navigating to {url}...")
    await page.goto(url, wait_until='domcontentloaded')
    await asyncio.sleep(1)  # Brief pause for page to settle
    
    # Start recording
    await recorder.start_recording(session, page)
    print("✅ Recording started!\n")
    
    # Keep browser open until interrupted
    try:
        # Wait for user to interact
        while recorder.is_recording:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping recording...")
        await stop_recording_internal()
    except Exception as e:
        print(f"\n❌ Error during recording: {e}")
        await stop_recording_internal()
        raise
    except Exception as e:
        # Clean up on error
        await stop_recording_internal()
        raise
    finally:
        # Ensure cleanup happens
        try:
            await stop_recording_internal()
        except:
            pass


async def stop_recording_internal() -> None:
    """Internal stop recording function."""
    global recorder, browser, playwright
    
    if recorder and recorder.is_recording:
        # Get recorded data before stopping
        session_data = recorder.get_recorded_data()
        
        # Stop recording
        await recorder.stop_recording()
        
        # Save final session data
        if recorder.storage and session_data:
            await recorder.storage.save_session_data(session_data)
            print(f"💾 Session data saved: {len(session_data.interactions)} interactions, {len(session_data.screenshots)} screenshots")
    
    # Close browser resources properly
    if browser:
        try:
            # Close all contexts first
            contexts = browser.contexts
            for ctx in contexts:
                try:
                    await ctx.close()
                except:
                    pass
            await browser.close()
        except Exception as e:
            logger.debug(f"Error closing browser: {e}")
        browser = None
    
    # Stop playwright
    if playwright:
        try:
            await playwright.stop()
        except Exception as e:
            logger.debug(f"Error stopping playwright: {e}")
        playwright = None
    
    print("✅ Recording stopped and saved.")


def signal_handler(sig, frame):
    """Handle Ctrl+C signal."""
    print("\n\n⏹️  Received interrupt signal, stopping recording...")
    # Note: Actual cleanup happens in start_session's KeyboardInterrupt handler
    sys.exit(130)


async def stop_session(session_id: str = None) -> None:
    """Stop a teaching session.
    
    Args:
        session_id: Session ID to stop (if not current session)
    """
    # For now, this is handled by Ctrl+C in start_session
    # In the future, could implement session management
    print("Use Ctrl+C in the recording session to stop, or use the start command's interrupt handler.")


async def analyze_session(session_id: str) -> None:
    """Analyze a teaching session.
    
    Args:
        session_id: Session ID to analyze
    """
    print(f"🔍 Analyzing session {session_id}...")
    print("   Analysis not yet implemented (Phase 4)")


async def verify_session(session_id: str) -> None:
    """Verify learned patterns.
    
    Args:
        session_id: Session ID to verify
    """
    print(f"✅ Verifying patterns for session {session_id}...")
    print("   Verification not yet implemented (Phase 5)")


async def export_session(session_id: str, output: str = None, format: str = "yaml") -> None:
    """Export patterns to config.
    
    Args:
        session_id: Session ID to export
        output: Output file path
        format: Export format (yaml or json)
    """
    print(f"📤 Exporting patterns for session {session_id}...")
    print("   Export not yet implemented (Phase 5)")


async def list_sessions() -> None:
    """List all teaching sessions."""
    storage = TeachingStorage(Path("teaching_data"))
    sessions = storage.list_sessions()
    
    if not sessions:
        print("No teaching sessions found.")
        return
    
    print(f"Found {len(sessions)} teaching session(s):\n")
    for session_id in sessions:
        print(f"  - {session_id}")


async def show_session_info(session_id: str) -> None:
    """Show session information.
    
    Args:
        session_id: Session ID to show info for
    """
    storage = TeachingStorage(Path("teaching_data"))
    session_data = await storage.load_session_data(session_id)
    
    if not session_data:
        print(f"❌ Session not found: {session_id}")
        return
    
    session = session_data.session
    print(f"\n📊 Session Information: {session_id}\n")
    print(f"  Target URL: {session.target_url}")
    print(f"  Status: {session.status}")
    print(f"  Started: {session.started_at}")
    if session.completed_at:
        print(f"  Completed: {session.completed_at}")
    print(f"  Interactions: {session.interaction_count}")
    print(f"  Screenshots: {session.screenshot_count}")
    if session.notes:
        print(f"  Notes: {session.notes}")
    print(f"\n  Total Interactions: {len(session_data.interactions)}")
    print(f"  Total Screenshots: {len(session_data.screenshots)}")
    print(f"  Patterns Extracted: {len(session_data.patterns)}")


async def delete_session(session_id: str) -> None:
    """Delete a teaching session.
    
    Args:
        session_id: Session ID to delete
    """
    import shutil
    
    storage = TeachingStorage(Path("teaching_data"))
    session_dir = storage.get_session_dir(session_id)
    
    if not session_dir.exists():
        print(f"❌ Session not found: {session_id}")
        return
    
    # Confirm deletion
    response = input(f"⚠️  Delete session {session_id}? This cannot be undone. (yes/no): ")
    if response.lower() != "yes":
        print("Cancelled.")
        return
    
    shutil.rmtree(session_dir)
    print(f"✅ Deleted session: {session_id}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Teaching mode for website navigation learning"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start a teaching session")
    start_parser.add_argument("url", help="Target URL to teach navigation for")
    start_parser.add_argument(
        "--session-name", 
        help="Name for this teaching session"
    )
    start_parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (not recommended - requires display for user interaction)"
    )
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop current teaching session")
    stop_parser.add_argument(
        "--session-id",
        help="Session ID to stop (if not current session)"
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a teaching session")
    analyze_parser.add_argument("session_id", help="Session ID to analyze")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify learned patterns")
    verify_parser.add_argument("session_id", help="Session ID to verify")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export patterns to config")
    export_parser.add_argument("session_id", help="Session ID to export")
    export_parser.add_argument(
        "--output",
        help="Output file path (default: teaching_data/patterns/{site}_patterns.yaml)"
    )
    export_parser.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Export format (default: yaml)"
    )
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all teaching sessions")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show session information")
    info_parser.add_argument("session_id", help="Session ID to show info for")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a teaching session")
    delete_parser.add_argument("session_id", help="Session ID to delete")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Execute command
    try:
        if args.command == "start":
            asyncio.run(start_session(args.url, args.session_name, headless=args.headless))
        elif args.command == "stop":
            asyncio.run(stop_session(args.session_id))
        elif args.command == "analyze":
            asyncio.run(analyze_session(args.session_id))
        elif args.command == "verify":
            asyncio.run(verify_session(args.session_id))
        elif args.command == "export":
            asyncio.run(export_session(args.session_id, args.output, args.format))
        elif args.command == "list":
            asyncio.run(list_sessions())
        elif args.command == "info":
            asyncio.run(show_session_info(args.session_id))
        elif args.command == "delete":
            asyncio.run(delete_session(args.session_id))
        
        return 0
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
