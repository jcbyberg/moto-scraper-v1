# Analysis API Contract

**Module**: `src.teaching.analyzer`  
**Purpose**: Analyze recorded interactions to extract navigation patterns

## Classes

### PatternAnalyzer

Analyzes interaction data to extract reusable navigation patterns.

#### Methods

##### `analyze_session(session_id: str) -> List[NavigationPattern]`

Analyze a teaching session and extract navigation patterns.

**Parameters**:
- `session_id: str` - ID of the teaching session to analyze

**Returns**: `List[NavigationPattern]` - List of extracted navigation patterns

**Side Effects**:
- Loads session data from storage
- Performs pattern analysis
- Saves extracted patterns to session data

**Raises**:
- `SessionNotFoundError` - If session does not exist
- `AnalysisError` - If analysis fails

---

##### `extract_selectors(click_events: List[ClickEvent]) -> Dict[str, str]`

Extract multiple selector strategies for clicked elements.

**Parameters**:
- `click_events: List[ClickEvent]` - List of click events to analyze

**Returns**: `Dict[str, str]` - Dictionary mapping selector strategies to selectors
  - Keys: "css", "xpath", "text", "id" (if available)
  - Values: Selector strings

**Example**:
```python
{
    "css": ".models-dropdown",
    "xpath": "//button[@class='models-dropdown']",
    "text": "Models",
    "id": None
}
```

---

##### `identify_sequences(events: List[InteractionEvent]) -> List[List[InteractionEvent]]`

Identify interaction sequences that form logical navigation flows.

**Parameters**:
- `events: List[InteractionEvent]` - List of all interaction events

**Returns**: `List[List[InteractionEvent]]` - List of event sequences, each representing a navigation flow

**Algorithm**:
- Groups consecutive interactions that form a logical flow
- Sequences are separated by significant time gaps or navigation events
- Each sequence represents a potential navigation pattern

---

##### `generate_pattern_rules(sequence: List[InteractionEvent]) -> List[PatternRule]`

Generate pattern rules from an interaction sequence.

**Parameters**:
- `sequence: List[InteractionEvent]` - Sequence of interactions

**Returns**: `List[PatternRule]` - List of pattern rules

**Rules Generated**:
- Click events → `click` action with selector
- Scroll events → `scroll` action with direction/target
- Navigation events → `wait` for navigation
- Timing gaps → `wait` with duration

---

##### `calculate_confidence(pattern: NavigationPattern, events: List[InteractionEvent]) -> float`

Calculate confidence score for a navigation pattern.

**Parameters**:
- `pattern: NavigationPattern` - Navigation pattern to score
- `events: List[InteractionEvent]` - Original interaction events

**Returns**: `float` - Confidence score between 0.0 and 1.0

**Factors**:
- Selector stability (how consistent selectors are)
- Sequence frequency (how often pattern appears)
- Timing consistency (how consistent delays are)
- Element visibility (whether elements are reliably present)

---

## Exceptions

### `AnalysisError`

Base exception for analysis-related errors.

**Attributes**:
- `message: str` - Error message
- `session_id: Optional[str]` - Associated session ID

---

### `SessionNotFoundError`

Exception raised when session does not exist.

**Inherits from**: `AnalysisError`

**Attributes**:
- `session_id: str` - Missing session ID


