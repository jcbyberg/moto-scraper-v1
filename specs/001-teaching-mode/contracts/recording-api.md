# Recording API Contract

**Module**: `src.teaching.recorder`  
**Purpose**: Capture user interactions during teaching sessions

## Classes

### InteractionRecorder

Records browser interactions during teaching mode.

#### Methods

##### `start_recording(session: TeachingSession, page: Page) -> None`

Start recording interactions on a Playwright page.

**Parameters**:
- `session: TeachingSession` - Teaching session to record for
- `page: Page` - Playwright page to record interactions on

**Returns**: `None`

**Side Effects**:
- Attaches event listeners to page
- Begins capturing clicks, scrolls, and navigation events
- Starts screenshot capture triggers

**Raises**:
- `RecordingError` - If recording is already active or page is invalid

---

##### `stop_recording() -> None`

Stop recording interactions.

**Parameters**: None

**Returns**: `None`

**Side Effects**:
- Removes event listeners
- Flushes pending events to storage
- Stops screenshot capture

**Raises**:
- `RecordingError` - If recording is not active

---

##### `record_click(event: dict) -> ClickEvent`

Record a click interaction.

**Parameters**:
- `event: dict` - Playwright click event data

**Returns**: `ClickEvent` - Recorded click event

**Side Effects**:
- Captures screenshot before click (if enabled)
- Records click event to session
- Captures screenshot after click (if enabled)

---

##### `record_scroll(event: dict) -> ScrollEvent`

Record a scroll interaction.

**Parameters**:
- `event: dict` - Playwright scroll event data

**Returns**: `ScrollEvent` - Recorded scroll event

**Side Effects**:
- Records scroll event to session
- May capture screenshot at scroll milestone

---

##### `record_navigation(event: dict) -> NavigationEvent`

Record a page navigation.

**Parameters**:
- `event: dict` - Playwright navigation event data

**Returns**: `NavigationEvent` - Recorded navigation event

**Side Effects**:
- Records navigation event to session
- Captures screenshot after navigation

---

##### `capture_screenshot(trigger: str, event_id: Optional[str] = None) -> Screenshot`

Capture a screenshot at the current page state.

**Parameters**:
- `trigger: str` - Trigger type: "before_click", "after_click", "scroll_milestone", "page_load", "manual"
- `event_id: Optional[str]` - Associated event ID if applicable

**Returns**: `Screenshot` - Captured screenshot metadata

**Side Effects**:
- Saves screenshot file to disk
- Records screenshot metadata to session

**Raises**:
- `ScreenshotError` - If screenshot capture fails

---

## Exceptions

### `RecordingError`

Base exception for recording-related errors.

**Attributes**:
- `message: str` - Error message
- `session_id: Optional[str]` - Associated session ID if applicable

---

### `ScreenshotError`

Exception raised when screenshot capture fails.

**Inherits from**: `RecordingError`

**Attributes**:
- `message: str` - Error message
- `file_path: Optional[str]` - Intended screenshot file path


