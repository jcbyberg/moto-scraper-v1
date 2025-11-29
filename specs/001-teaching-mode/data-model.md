# Data Model: Teaching Mode

**Date**: 2025-01-27  
**Feature**: Teaching Mode for Website Navigation  
**Phase**: Phase 1 - Design & Contracts

## Overview

This document defines the data models for the teaching mode feature using Pydantic for type safety and validation.

## Core Models

### TeachingSession

Represents a teaching session with metadata and state.

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class SessionStatus(str, Enum):
    RECORDING = "recording"
    PAUSED = "paused"
    COMPLETED = "completed"
    ANALYZED = "analyzed"

class TeachingSession(BaseModel):
    """Teaching session metadata and state."""
    session_id: str = Field(..., description="Unique session identifier")
    target_url: str = Field(..., description="Base URL being taught")
    status: SessionStatus = Field(default=SessionStatus.RECORDING)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    interaction_count: int = Field(default=0, description="Total number of interactions recorded")
    screenshot_count: int = Field(default=0, description="Total number of screenshots captured")
    browser_info: dict = Field(default_factory=dict, description="Browser version, user agent, etc.")
    notes: Optional[str] = Field(None, description="User-provided notes about the session")
```

### InteractionEvent (Base)

Base class for all interaction events.

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class EventType(str, Enum):
    CLICK = "click"
    SCROLL = "scroll"
    NAVIGATION = "navigation"
    KEYBOARD = "keyboard"
    HOVER = "hover"

class InteractionEvent(BaseModel):
    """Base class for all interaction events."""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    page_url: str = Field(..., description="URL of the page where event occurred")
    viewport_size: Dict[str, int] = Field(..., description="Viewport width and height")
    scroll_position: Dict[str, int] = Field(..., description="Scroll X and Y position")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")
```

### ClickEvent

Represents a click interaction.

```python
class ClickEvent(InteractionEvent):
    """Click interaction event."""
    event_type: EventType = Field(default=EventType.CLICK)
    element_selector: str = Field(..., description="CSS selector of clicked element")
    element_xpath: Optional[str] = Field(None, description="XPath of clicked element")
    element_text: Optional[str] = Field(None, description="Text content of clicked element")
    element_tag: str = Field(..., description="HTML tag name (button, a, div, etc.)")
    element_id: Optional[str] = Field(None, description="Element ID if present")
    element_classes: list[str] = Field(default_factory=list, description="Element CSS classes")
    click_position: Dict[str, int] = Field(..., description="X, Y coordinates of click relative to viewport")
    button: str = Field(default="left", description="Mouse button (left, right, middle)")
    click_count: int = Field(default=1, description="Number of clicks (1 for single, 2 for double)")
    screenshot_before_id: Optional[str] = Field(None, description="Screenshot ID before click")
    screenshot_after_id: Optional[str] = Field(None, description="Screenshot ID after click")
```

### ScrollEvent

Represents a scroll interaction.

```python
class ScrollEvent(InteractionEvent):
    """Scroll interaction event."""
    event_type: EventType = Field(default=EventType.SCROLL)
    scroll_direction: str = Field(..., description="Direction: up, down, left, right")
    scroll_distance: int = Field(..., description="Pixels scrolled")
    scroll_target: Optional[str] = Field(None, description="Target element selector if scrolling to element")
    final_scroll_position: Dict[str, int] = Field(..., description="Final scroll X and Y position")
    screenshot_id: Optional[str] = Field(None, description="Screenshot ID at scroll position")
```

### NavigationEvent

Represents a page navigation.

```python
class NavigationEvent(InteractionEvent):
    """Page navigation event."""
    event_type: EventType = Field(default=EventType.NAVIGATION)
    source_url: str = Field(..., description="URL navigated from")
    target_url: str = Field(..., description="URL navigated to")
    navigation_type: str = Field(..., description="Type: link_click, form_submit, direct, back, forward")
    trigger_event_id: Optional[str] = Field(None, description="ID of event that triggered navigation")
    load_time_ms: Optional[int] = Field(None, description="Page load time in milliseconds")
    screenshot_id: Optional[str] = Field(None, description="Screenshot ID after navigation")
```

### Screenshot

Represents a captured screenshot.

```python
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
```

### NavigationPattern

Represents an extracted navigation pattern.

```python
from typing import List

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
```

### TeachingSessionData

Complete session data structure for storage.

```python
class TeachingSessionData(BaseModel):
    """Complete teaching session data for storage."""
    version: str = Field(default="1.0", description="Data format version")
    session: TeachingSession
    interactions: List[InteractionEvent] = Field(default_factory=list)
    screenshots: List[Screenshot] = Field(default_factory=list)
    patterns: List[NavigationPattern] = Field(default_factory=list, description="Extracted patterns (after analysis)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")
```

## Model Relationships

```
TeachingSession (1) ──< (N) InteractionEvent
TeachingSession (1) ──< (N) Screenshot
TeachingSession (1) ──< (N) NavigationPattern
InteractionEvent (1) ──< (0-2) Screenshot (before/after)
NavigationPattern (1) ──< (N) PatternRule
```

## Validation Rules

1. **Session ID**: Must be unique, UUID format recommended
2. **Event IDs**: Must be unique within a session
3. **Screenshot IDs**: Must be unique within a session
4. **Pattern IDs**: Must be unique across all sessions
5. **Timestamps**: Must be in ISO 8601 format
6. **Selectors**: Must be valid CSS selectors or XPath expressions
7. **Confidence Score**: Must be between 0.0 and 1.0
8. **File Paths**: Must be relative paths from session directory

## Data Format Versioning

- Current version: `1.0`
- Version format: `MAJOR.MINOR`
- **MAJOR** increment: Breaking changes (removed fields, changed structure)
- **MINOR** increment: Additive changes (new optional fields, new event types)

## Example Data

### Example TeachingSessionData

```json
{
  "version": "1.0",
  "session": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "target_url": "https://www.ducati.com",
    "status": "completed",
    "started_at": "2025-01-27T10:00:00Z",
    "completed_at": "2025-01-27T10:15:00Z",
    "interaction_count": 45,
    "screenshot_count": 90,
    "browser_info": {
      "name": "chromium",
      "version": "120.0.0.0"
    }
  },
  "interactions": [
    {
      "event_id": "evt_001",
      "event_type": "click",
      "timestamp": "2025-01-27T10:00:05Z",
      "page_url": "https://www.ducati.com",
      "viewport_size": {"width": 1920, "height": 1080},
      "scroll_position": {"x": 0, "y": 0},
      "element_selector": ".models-dropdown",
      "element_text": "Models",
      "element_tag": "button",
      "click_position": {"x": 150, "y": 50},
      "screenshot_before_id": "scr_001",
      "screenshot_after_id": "scr_002"
    }
  ],
  "screenshots": [
    {
      "screenshot_id": "scr_001",
      "file_path": "screenshots/20250127_100005_scr_001.png",
      "timestamp": "2025-01-27T10:00:05Z",
      "page_url": "https://www.ducati.com",
      "viewport_size": {"width": 1920, "height": 1080},
      "scroll_position": {"x": 0, "y": 0},
      "trigger_event_id": "evt_001",
      "trigger_type": "before_click",
      "full_page": false,
      "file_size_bytes": 245678
    }
  ],
  "patterns": []
}
```


