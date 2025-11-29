"""Pydantic models for teaching mode data structures."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class SessionStatus(str, Enum):
    """Teaching session status."""
    RECORDING = "recording"
    PAUSED = "paused"
    COMPLETED = "completed"
    ANALYZED = "analyzed"


class EventType(str, Enum):
    """Interaction event types."""
    CLICK = "click"
    SCROLL = "scroll"
    NAVIGATION = "navigation"
    KEYBOARD = "keyboard"
    HOVER = "hover"


class TeachingSession(BaseModel):
    """Teaching session metadata and state."""
    session_id: str = Field(..., description="Unique session identifier")
    target_url: str = Field(..., description="Base URL being taught")
    status: SessionStatus = Field(default=SessionStatus.RECORDING)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    interaction_count: int = Field(default=0, description="Total number of interactions recorded")
    screenshot_count: int = Field(default=0, description="Total number of screenshots captured")
    browser_info: Dict[str, Any] = Field(default_factory=dict, description="Browser version, user agent, etc.")
    notes: Optional[str] = Field(None, description="User-provided notes about the session")


class InteractionEvent(BaseModel):
    """Base class for all interaction events."""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    page_url: str = Field(..., description="URL of the page where event occurred")
    viewport_size: Dict[str, int] = Field(..., description="Viewport width and height")
    scroll_position: Dict[str, int] = Field(..., description="Scroll X and Y position")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")


class ClickEvent(InteractionEvent):
    """Click interaction event."""
    event_type: EventType = Field(default=EventType.CLICK)
    element_selector: str = Field(..., description="CSS selector of clicked element")
    element_xpath: Optional[str] = Field(None, description="XPath of clicked element")
    element_text: Optional[str] = Field(None, description="Text content of clicked element")
    element_tag: str = Field(..., description="HTML tag name (button, a, div, etc.)")
    element_id: Optional[str] = Field(None, description="Element ID if present")
    element_classes: List[str] = Field(default_factory=list, description="Element CSS classes")
    click_position: Dict[str, int] = Field(..., description="X, Y coordinates of click relative to viewport")
    button: str = Field(default="left", description="Mouse button (left, right, middle)")
    click_count: int = Field(default=1, description="Number of clicks (1 for single, 2 for double)")
    screenshot_before_id: Optional[str] = Field(None, description="Screenshot ID before click")
    screenshot_after_id: Optional[str] = Field(None, description="Screenshot ID after click")


class ScrollEvent(InteractionEvent):
    """Scroll interaction event."""
    event_type: EventType = Field(default=EventType.SCROLL)
    scroll_direction: str = Field(..., description="Direction: up, down, left, right")
    scroll_distance: int = Field(..., description="Pixels scrolled")
    scroll_target: Optional[str] = Field(None, description="Target element selector if scrolling to element")
    final_scroll_position: Dict[str, int] = Field(..., description="Final scroll X and Y position")
    screenshot_id: Optional[str] = Field(None, description="Screenshot ID at scroll position")


class NavigationEvent(InteractionEvent):
    """Page navigation event."""
    event_type: EventType = Field(default=EventType.NAVIGATION)
    source_url: str = Field(..., description="URL navigated from")
    target_url: str = Field(..., description="URL navigated to")
    navigation_type: str = Field(..., description="Type: link_click, form_submit, direct, back, forward")
    trigger_event_id: Optional[str] = Field(None, description="ID of event that triggered navigation")
    load_time_ms: Optional[int] = Field(None, description="Page load time in milliseconds")
    screenshot_id: Optional[str] = Field(None, description="Screenshot ID after navigation")


class Screenshot(BaseModel):
    """Screenshot metadata and file reference."""
    screenshot_id: str = Field(..., description="Unique screenshot identifier")
    file_path: str = Field(..., description="Relative path to screenshot file")
    timestamp: datetime = Field(default_factory=datetime.now)
    page_url: str = Field(..., description="URL of the page when screenshot was taken")
    viewport_size: Dict[str, int] = Field(..., description="Viewport width and height")
    scroll_position: Dict[str, int] = Field(..., description="Scroll position when screenshot was taken")
    trigger_event_id: Optional[str] = Field(None, description="ID of event that triggered screenshot")
    trigger_type: str = Field(..., description="Trigger: before_click, after_click, scroll_milestone, page_load, manual")
    full_page: bool = Field(default=False, description="Whether screenshot is full page or viewport only")
    file_size_bytes: int = Field(..., description="Screenshot file size in bytes")


class PatternRule(BaseModel):
    """Individual rule within a navigation pattern."""
    step_number: int = Field(..., description="Step order in the pattern")
    action: str = Field(..., description="Action type: click, scroll, wait, navigate")
    selector: Optional[str] = Field(None, description="Element selector (CSS, XPath, or text)")
    selector_strategy: str = Field(..., description="Selector type: css, xpath, text, position")
    wait_condition: Optional[str] = Field(None, description="Wait condition: element_visible, navigation, timeout, etc.")
    wait_duration_ms: Optional[int] = Field(None, description="Wait duration in milliseconds if timeout")
    scroll_direction: Optional[str] = Field(None, description="Scroll direction if action is scroll")
    scroll_target: Optional[str] = Field(None, description="Scroll target selector if scrolling to element")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional rule metadata")


class NavigationPattern(BaseModel):
    """Extracted navigation pattern from teaching session."""
    pattern_id: str = Field(..., description="Unique pattern identifier")
    pattern_name: str = Field(..., description="Human-readable pattern name")
    description: Optional[str] = Field(None, description="Pattern description")
    session_id: str = Field(..., description="Session ID where pattern was extracted")
    rules: List[PatternRule] = Field(..., description="Ordered list of pattern rules")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    usage_count: int = Field(default=1, description="Number of times pattern was observed")
    verified: bool = Field(default=False, description="Whether pattern has been verified by user")
    created_at: datetime = Field(default_factory=datetime.now)


class TeachingSessionData(BaseModel):
    """Complete teaching session data for storage."""
    version: str = Field(default="1.0", description="Data format version")
    session: TeachingSession
    interactions: List[InteractionEvent] = Field(default_factory=list)
    screenshots: List[Screenshot] = Field(default_factory=list)
    patterns: List[NavigationPattern] = Field(default_factory=list, description="Extracted patterns (after analysis)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")


