"""Interaction recorder for teaching mode."""

import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from playwright.async_api import Page
from .models import (
    TeachingSession,
    ClickEvent,
    ScrollEvent,
    NavigationEvent,
    Screenshot,
    EventType,
    TeachingSessionData,
)
from .storage import TeachingStorage
from .session import SessionManager

logger = logging.getLogger(__name__)


class RecordingError(Exception):
    """Base exception for recording-related errors."""
    
    def __init__(self, message: str, session_id: Optional[str] = None):
        self.message = message
        self.session_id = session_id
        super().__init__(self.message)


class ScreenshotError(RecordingError):
    """Exception raised when screenshot capture fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, session_id: Optional[str] = None):
        self.file_path = file_path
        super().__init__(message, session_id)


class InteractionRecorder:
    """Records browser interactions during teaching mode."""
    
    def __init__(
        self,
        session_manager: SessionManager,
        storage: TeachingStorage,
        auto_save_interval: int = 10
    ):
        """Initialize recorder.
        
        Args:
            session_manager: Session manager instance
            storage: Storage instance
            auto_save_interval: Number of interactions between auto-saves
        """
        self.session_manager = session_manager
        self.storage = storage
        self.auto_save_interval = auto_save_interval
        
        self.page: Optional[Page] = None
        self.session: Optional[TeachingSession] = None
        self.is_recording = False
        
        self.interactions: List[Any] = []
        self.screenshots: List[Screenshot] = []
        
        self._last_scroll_position: Dict[str, int] = {"x": 0, "y": 0}
        self._scroll_milestone_distance = 500  # Screenshot every 500px scroll
        self._last_scroll_milestone = 0
        
        self._event_handlers: List[Any] = []
    
    async def start_recording(self, session: TeachingSession, page: Page) -> None:
        """Start recording interactions on a Playwright page.
        
        Args:
            session: Teaching session to record for
            page: Playwright page to record interactions on
            
        Raises:
            RecordingError: If recording is already active or page is invalid
        """
        if self.is_recording:
            raise RecordingError("Recording is already active", session.session_id)
        
        if not page:
            raise RecordingError("Invalid page provided", session.session_id)
        
        self.session = session
        self.page = page
        self.is_recording = True
        self.interactions = []
        self.screenshots = []
        
        # Get initial viewport size
        viewport = page.viewport_size or {"width": 1920, "height": 1080}
        
        # Capture initial screenshot
        try:
            await self.capture_screenshot("page_load")
        except ScreenshotError as e:
            logger.warning(f"Failed to capture initial screenshot: {e}")
        
        # Attach event listeners
        self._attach_event_listeners()
        
        logger.info(f"Started recording for session {session.session_id}")
    
    def _attach_event_listeners(self) -> None:
        """Attach Playwright event listeners."""
        if not self.page:
            return
        
        # Inject JavaScript to track clicks and store element info
        async def inject_click_tracker() -> None:
            await self.page.evaluate("""
                window.lastClickInfo = null;
                document.addEventListener('click', function(e) {
                    const el = e.target;
                    const getSelector = (el) => {
                        if (el.id) return `#${el.id}`;
                        if (el.className) {
                            const classes = el.className.split(' ').filter(c => c).join('.');
                            if (classes) return `${el.tagName.toLowerCase()}.${classes}`;
                        }
                        return el.tagName.toLowerCase();
                    };
                    const getXPath = (el) => {
                        if (el.id) return `//*[@id="${el.id}"]`;
                        let path = '';
                        for (; el && el.nodeType === 1; el = el.parentNode) {
                            let idx = 1;
                            for (let sib = el.previousSibling; sib; sib = sib.previousSibling) {
                                if (sib.nodeType === 1 && sib.tagName === el.tagName) idx++;
                            }
                            path = `/${el.tagName.toLowerCase()}[${idx}]${path}`;
                        }
                        return path;
                    };
                    window.lastClickInfo = {
                        x: e.clientX,
                        y: e.clientY,
                        selector: getSelector(el),
                        xpath: getXPath(el),
                        text: el.textContent?.trim().substring(0, 100) || '',
                        tag: el.tagName.toLowerCase(),
                        id: el.id || null,
                        classes: el.className ? el.className.split(' ').filter(c => c) : [],
                        button: e.button === 0 ? 'left' : e.button === 2 ? 'right' : 'middle',
                        clickCount: e.detail || 1
                    };
                }, true);
            """)
        
        # Inject click tracker
        asyncio.create_task(inject_click_tracker())
        
        # Click event listener
        async def on_click(event: Any) -> None:
            try:
                await self._handle_click(event)
            except Exception as e:
                logger.error(f"Error handling click event: {e}", exc_info=True)
        
        # Navigation event listener
        async def on_navigation(event: Any) -> None:
            try:
                await self._handle_navigation(event)
            except Exception as e:
                logger.error(f"Error handling navigation event: {e}", exc_info=True)
        
        # Attach listeners
        self.page.on("click", on_click)
        self.page.on("framenavigated", on_navigation)
        
        # Monitor scroll using periodic check
        self._start_scroll_monitoring()
        
        logger.debug("Event listeners attached")
    
    def _start_scroll_monitoring(self) -> None:
        """Start monitoring scroll events."""
        async def monitor_scroll() -> None:
            if not self.is_recording or not self.page:
                return
            
            try:
                scroll_pos = await self.page.evaluate("() => ({ x: window.scrollX, y: window.scrollY })")
                if scroll_pos != self._last_scroll_position:
                    await self._handle_scroll()
                    self._last_scroll_position = scroll_pos
            except Exception as e:
                logger.debug(f"Scroll monitoring error: {e}")
            
            if self.is_recording:
                # Check again in 100ms
                await asyncio.sleep(0.1)
                asyncio.create_task(monitor_scroll())
        
        asyncio.create_task(monitor_scroll())
    
    async def _handle_click(self, event: Any) -> None:
        """Handle click event."""
        if not self.page or not self.session:
            return
        
        try:
            # Get click info from injected JavaScript
            click_info = await self.page.evaluate("() => window.lastClickInfo")
            
            if not click_info:
                logger.warning("Could not get click info from page")
                return
            
            click_pos = {"x": click_info.get("x", 0), "y": click_info.get("y", 0)}
            
            # Capture screenshot before click (if we can do it quickly)
            # Note: This happens after the click, so it's more of a "state after click"
            # For true "before" screenshot, we'd need to capture on mousedown
            screenshot_before = None  # Skip before screenshot for now to avoid delay
            
            # Wait a moment for click effects to register
            await asyncio.sleep(0.2)
            
            # Capture screenshot after click
            screenshot_after = await self.capture_screenshot("after_click")
            
            # Create click event
            event_id = f"evt_{uuid.uuid4().hex[:8]}"
            click_event = ClickEvent(
                event_id=event_id,
                event_type=EventType.CLICK,
                timestamp=datetime.now(),
                page_url=self.page.url,
                viewport_size=self.page.viewport_size or {"width": 1920, "height": 1080},
                scroll_position=self._last_scroll_position,
                element_selector=click_info.get("selector", ""),
                element_xpath=click_info.get("xpath"),
                element_text=click_info.get("text", ""),
                element_tag=click_info.get("tag", ""),
                element_id=click_info.get("id"),
                element_classes=click_info.get("classes", []),
                click_position=click_pos,
                button=click_info.get("button", "left"),
                click_count=click_info.get("clickCount", 1),
                screenshot_before_id=screenshot_before.screenshot_id if screenshot_before else None,
                screenshot_after_id=screenshot_after.screenshot_id if screenshot_after else None,
            )
            
            self.interactions.append(click_event)
            self._update_session_counts()
            
            # Auto-save if needed
            if len(self.interactions) % self.auto_save_interval == 0:
                await self._auto_save()
            
            logger.debug(f"Recorded click event: {event_id} on {click_info.get('tag', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error recording click: {e}", exc_info=True)
    
    async def _handle_scroll(self) -> None:
        """Handle scroll event."""
        if not self.page or not self.session:
            return
        
        try:
            scroll_pos = await self.page.evaluate("() => ({ x: window.scrollX, y: window.scrollY })")
            
            # Calculate scroll distance
            dx = scroll_pos["x"] - self._last_scroll_position["x"]
            dy = scroll_pos["y"] - self._last_scroll_position["y"]
            
            if dx == 0 and dy == 0:
                return
            
            # Determine direction
            if abs(dy) > abs(dx):
                direction = "down" if dy > 0 else "up"
                distance = abs(dy)
            else:
                direction = "right" if dx > 0 else "left"
                distance = abs(dx)
            
            # Check if we've reached a scroll milestone
            total_scrolled = abs(scroll_pos["y"]) + abs(scroll_pos["x"])
            milestone = (total_scrolled // self._scroll_milestone_distance) * self._scroll_milestone_distance
            
            screenshot_id = None
            if milestone > self._last_scroll_milestone:
                screenshot = await self.capture_screenshot("scroll_milestone")
                screenshot_id = screenshot.screenshot_id if screenshot else None
                self._last_scroll_milestone = milestone
            
            # Create scroll event
            event_id = f"evt_{uuid.uuid4().hex[:8]}"
            scroll_event = ScrollEvent(
                event_id=event_id,
                event_type=EventType.SCROLL,
                timestamp=datetime.now(),
                page_url=self.page.url,
                viewport_size=self.page.viewport_size or {"width": 1920, "height": 1080},
                scroll_position=self._last_scroll_position,
                scroll_direction=direction,
                scroll_distance=distance,
                final_scroll_position=scroll_pos,
                screenshot_id=screenshot_id,
            )
            
            self.interactions.append(scroll_event)
            self._last_scroll_position = scroll_pos
            self._update_session_counts()
            
            logger.debug(f"Recorded scroll event: {event_id}")
            
        except Exception as e:
            logger.error(f"Error recording scroll: {e}", exc_info=True)
    
    async def _handle_navigation(self, event: Any) -> None:
        """Handle navigation event."""
        if not self.page or not self.session:
            return
        
        try:
            # Wait for page to load
            await self.page.wait_for_load_state("networkidle", timeout=5000)
            
            # Capture screenshot after navigation
            screenshot = await self.capture_screenshot("page_load")
            
            # Determine navigation type
            nav_type = "link_click"  # Default, could be improved
            
            # Get trigger event (last click if available)
            trigger_event_id = None
            if self.interactions:
                last_event = self.interactions[-1]
                if isinstance(last_event, ClickEvent):
                    trigger_event_id = last_event.event_id
            
            # Create navigation event
            event_id = f"evt_{uuid.uuid4().hex[:8]}"
            nav_event = NavigationEvent(
                event_id=event_id,
                event_type=EventType.NAVIGATION,
                timestamp=datetime.now(),
                page_url=self.page.url,
                viewport_size=self.page.viewport_size or {"width": 1920, "height": 1080},
                scroll_position=self._last_scroll_position,
                source_url=self.session.target_url,  # Could track previous URL better
                target_url=self.page.url,
                navigation_type=nav_type,
                trigger_event_id=trigger_event_id,
                screenshot_id=screenshot.screenshot_id if screenshot else None,
            )
            
            self.interactions.append(nav_event)
            self._update_session_counts()
            
            logger.info(f"Recorded navigation event: {event_id} to {self.page.url}")
            
        except Exception as e:
            logger.error(f"Error recording navigation: {e}", exc_info=True)
    
    
    async def capture_screenshot(
        self,
        trigger: str,
        event_id: Optional[str] = None
    ) -> Optional[Screenshot]:
        """Capture a screenshot at the current page state.
        
        Args:
            trigger: Trigger type (before_click, after_click, scroll_milestone, page_load, manual)
            event_id: Associated event ID if applicable
            
        Returns:
            Screenshot metadata or None if capture fails
            
        Raises:
            ScreenshotError: If screenshot capture fails
        """
        if not self.page or not self.session:
            return None
        
        try:
            screenshot_id = f"scr_{uuid.uuid4().hex[:8]}"
            screenshot_path = self.storage.get_screenshot_path(
                self.session.session_id,
                screenshot_id
            )
            
            # Capture screenshot
            await self.page.screenshot(path=str(screenshot_path), full_page=False)
            
            # Get file size
            file_size = screenshot_path.stat().st_size
            
            # Get current state
            viewport = self.page.viewport_size or {"width": 1920, "height": 1080}
            scroll_pos = await self.page.evaluate(
                "() => ({ x: window.scrollX, y: window.scrollY })"
            )
            
            # Create screenshot metadata
            screenshot = Screenshot(
                screenshot_id=screenshot_id,
                file_path=str(screenshot_path.relative_to(self.storage.base_dir)),
                timestamp=datetime.now(),
                page_url=self.page.url,
                viewport_size=viewport,
                scroll_position=scroll_pos,
                trigger_event_id=event_id,
                trigger_type=trigger,
                full_page=False,
                file_size_bytes=file_size,
            )
            
            self.screenshots.append(screenshot)
            self._update_session_counts()
            
            logger.debug(f"Captured screenshot: {screenshot_id} ({trigger})")
            return screenshot
            
        except Exception as e:
            error_msg = f"Screenshot capture failed: {e}"
            logger.error(error_msg)
            raise ScreenshotError(
                error_msg,
                file_path=str(screenshot_path) if 'screenshot_path' in locals() else None,
                session_id=self.session.session_id if self.session else None
            )
    
    def _update_session_counts(self) -> None:
        """Update session interaction and screenshot counts."""
        if self.session:
            self.session_manager.update_interaction_count(len(self.interactions))
            self.session_manager.update_screenshot_count(len(self.screenshots))
    
    async def _auto_save(self) -> None:
        """Auto-save session data."""
        if not self.session:
            return
        
        try:
            session_data = TeachingSessionData(
                version="1.0",
                session=self.session,
                interactions=self.interactions,
                screenshots=self.screenshots,
            )
            await self.storage.save_session_data(session_data)
            logger.debug(f"Auto-saved session {self.session.session_id}")
        except Exception as e:
            logger.error(f"Auto-save failed: {e}", exc_info=True)
    
    async def stop_recording(self) -> None:
        """Stop recording interactions.
        
        Raises:
            RecordingError: If recording is not active
        """
        if not self.is_recording:
            raise RecordingError("Recording is not active")
        
        self.is_recording = False
        
        # Final save
        if self.session:
            await self._auto_save()
            from .models import SessionStatus
            self.session_manager.update_session_status(SessionStatus.COMPLETED)
        
        # Clear event handlers
        self._event_handlers.clear()
        
        logger.info(f"Stopped recording for session {self.session.session_id if self.session else 'unknown'}")
    
    def get_recorded_data(self) -> TeachingSessionData:
        """Get all recorded data.
        
        Returns:
            Complete session data
        """
        if not self.session:
            raise RecordingError("No active session")
        
        return TeachingSessionData(
            version="1.0",
            session=self.session,
            interactions=self.interactions,
            screenshots=self.screenshots,
        )

