# Replay API Contract

**Module**: `src.teaching.replayer`  
**Purpose**: Replay learned navigation patterns for user verification

## Classes

### PatternReplayer

Replays navigation patterns in an automated browser for verification.

#### Methods

##### `replay_pattern(pattern: NavigationPattern, browser: Browser, base_url: str) -> ReplayResult`

Replay a navigation pattern in an automated browser.

**Parameters**:
- `pattern: NavigationPattern` - Navigation pattern to replay
- `browser: Browser` - Playwright browser instance
- `base_url: str` - Base URL to start navigation from

**Returns**: `ReplayResult` - Result of replay including success status and screenshots

**Side Effects**:
- Opens new browser page
- Executes pattern rules in order
- Captures screenshots at each step
- Provides visual feedback (element highlighting)

**Raises**:
- `ReplayError` - If replay fails (selector not found, timeout, etc.)

---

##### `demonstrate_pattern(pattern: NavigationPattern, browser: Browser, base_url: str) -> Demonstration`

Demonstrate a pattern with visual feedback and comparison screenshots.

**Parameters**:
- `pattern: NavigationPattern` - Navigation pattern to demonstrate
- `browser: Browser` - Playwright browser instance
- `base_url: str` - Base URL to start navigation from

**Returns**: `Demonstration` - Demonstration result with original and replay screenshots

**Side Effects**:
- Replays pattern with visual highlighting
- Captures comparison screenshots
- Generates step-by-step demonstration data

---

##### `highlight_element(page: Page, selector: str, duration_ms: int = 1000) -> None`

Highlight an element on the page for visual feedback.

**Parameters**:
- `page: Page` - Playwright page
- `selector: str` - Element selector
- `duration_ms: int` - Highlight duration in milliseconds

**Returns**: `None`

**Side Effects**:
- Injects CSS to highlight element (green border, pulsing animation)
- Removes highlight after duration

**Raises**:
- `ElementNotFoundError` - If element is not found

---

## Data Classes

### ReplayResult

Result of pattern replay.

**Attributes**:
- `success: bool` - Whether replay completed successfully
- `steps_completed: int` - Number of steps successfully completed
- `total_steps: int` - Total number of steps in pattern
- `screenshots: List[Screenshot]` - Screenshots captured during replay
- `errors: List[str]` - List of error messages if any
- `duration_ms: int` - Total replay duration in milliseconds

---

### Demonstration

Demonstration result with comparison data.

**Attributes**:
- `pattern: NavigationPattern` - Pattern that was demonstrated
- `original_screenshots: List[Screenshot]` - Screenshots from original teaching session
- `replay_screenshots: List[Screenshot]` - Screenshots from replay
- `step_comparisons: List[StepComparison]` - Step-by-step comparisons
- `success: bool` - Whether demonstration completed successfully

---

### StepComparison

Comparison of a single step between original and replay.

**Attributes**:
- `step_number: int` - Step number in pattern
- `rule: PatternRule` - Pattern rule for this step
- `original_screenshot: Screenshot` - Screenshot from original session
- `replay_screenshot: Screenshot` - Screenshot from replay
- `match_score: float` - Visual similarity score (0.0 to 1.0)

---

## Exceptions

### `ReplayError`

Base exception for replay-related errors.

**Attributes**:
- `message: str` - Error message
- `pattern_id: Optional[str]` - Associated pattern ID
- `step_number: Optional[int]` - Step number where error occurred

---

### `ElementNotFoundError`

Exception raised when element selector is not found during replay.

**Inherits from**: `ReplayError`

**Attributes**:
- `selector: str` - Selector that was not found
- `page_url: str` - URL of page where element was searched

---

### `TimeoutError`

Exception raised when a wait condition times out.

**Inherits from**: `ReplayError`

**Attributes**:
- `wait_condition: str` - Wait condition that timed out
- `timeout_ms: int` - Timeout duration in milliseconds


