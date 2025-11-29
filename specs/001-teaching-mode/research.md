# Research: Teaching Mode Feature

**Date**: 2025-01-27  
**Feature**: Teaching Mode for Website Navigation  
**Phase**: Phase 0 - Research & Technical Decisions

## Research Questions & Findings

### 1. Playwright Event Recording

**Question**: How to capture user interactions in Playwright without interfering with normal browser behavior?

**Research**:
- Playwright provides `page.on()` API for listening to browser events
- Can listen to: `click`, `dblclick`, `scroll`, `navigation`, `load`, etc.
- Events can be captured without blocking or modifying the original behavior
- Playwright's `page.add_init_script()` can inject listeners that capture events before they're processed

**Decision**: Use Playwright's event listener API with `page.on()` for click, scroll, and navigation events. Inject a script to capture additional metadata (element selectors, positions) that may not be in the standard event object.

**Rationale**: 
- Non-intrusive: Events are captured asynchronously without blocking
- Comprehensive: Can capture all interaction types needed
- Native: Uses Playwright's built-in capabilities

**Alternatives Considered**:
- Browser DevTools Protocol: More complex, requires additional setup
- Selenium: Not used in this project (Playwright is standard)
- Custom browser extension: Would require separate development and distribution

---

### 2. Screenshot Capture Strategies

**Question**: When and how should screenshots be captured to balance information value with storage/performance?

**Research**:
- Playwright supports `page.screenshot()` with options: `full_page`, `viewport`, `clip`
- Full page screenshots are larger but capture complete context
- Viewport screenshots are faster and smaller
- Can capture before/after events or at specific milestones

**Decision**: 
- Capture viewport screenshots by default (faster, smaller)
- Capture full page screenshots optionally (configurable)
- Screenshot timing:
  - Before each click (to see element state)
  - After each click (to see result)
  - At scroll milestones (every 500px or when element comes into view)
  - On page load/navigation

**Rationale**:
- Viewport screenshots provide sufficient context for most use cases
- Before/after click screenshots capture the interaction result
- Milestone-based scrolling reduces screenshot count while maintaining coverage
- Optional full page gives flexibility for complex layouts

**Alternatives Considered**:
- Screenshot every N milliseconds: Too many screenshots, storage intensive
- Screenshot only on errors: Insufficient context for pattern analysis
- Video recording: Much larger storage, harder to analyze programmatically

---

### 3. Pattern Analysis Algorithms

**Question**: How to extract reusable navigation patterns from recorded interactions?

**Research**:
- Pattern recognition in UI interactions is an active research area
- Common approaches: sequence mining, state machine extraction, rule-based analysis
- For web navigation, patterns typically involve:
  - Element selection strategies (CSS selectors, XPath, text matching)
  - Action sequences (click → wait → scroll → click)
  - Timing patterns (delays, wait conditions)

**Decision**: 
- Use rule-based analysis with heuristics:
  1. **Selector Extraction**: For each clicked element, generate multiple selector strategies:
     - CSS selector (id, class, attributes)
     - XPath (position-based, text-based)
     - Text content matching
     - Visual position (if stable)
  2. **Sequence Identification**: Group consecutive interactions that form a logical flow
  3. **Timing Analysis**: Extract wait conditions (element visibility, page load, fixed delays)
  4. **Pattern Generalization**: Identify common patterns across multiple similar interactions

**Rationale**:
- Rule-based approach is interpretable and allows user refinement
- Multiple selector strategies provide fallbacks for robustness
- Sequence identification helps understand navigation flows
- Timing analysis ensures patterns work reliably

**Alternatives Considered**:
- Machine learning approaches: Requires training data, less interpretable
- Simple replay: Doesn't extract reusable patterns
- Manual pattern definition: Defeats the purpose of teaching mode

---

### 4. Data Model Design

**Question**: What structure should interaction data use for storage and analysis?

**Research**:
- JSON is standard for structured data storage
- Pydantic provides validation and type safety
- Need to support versioning for future compatibility
- Should include metadata for session context

**Decision**: 
- Use Pydantic models for type safety and validation
- Store as JSON files (one per session)
- Include version field in data format
- Structure:
  ```python
  {
    "version": "1.0",
    "session": { ... },
    "interactions": [ ... ],
    "screenshots": [ ... ],
    "metadata": { ... }
  }
  ```

**Rationale**:
- Pydantic ensures data integrity and provides IDE support
- JSON is human-readable and easy to debug
- Versioning allows future format evolution
- Separate files per session enable parallel processing

**Alternatives Considered**:
- SQLite database: More complex, overkill for this use case
- Binary format: Not human-readable, harder to debug
- Single monolithic file: Harder to manage, slower to process

---

### 5. Replay & Verification UI

**Question**: How to demonstrate learned patterns to users for verification?

**Research**:
- Playwright can programmatically execute actions
- Can highlight elements before clicking (inject CSS)
- Can show progress indicators
- Can capture screenshots during replay for comparison

**Decision**:
- Replay patterns in automated browser with visual feedback:
  - Highlight target elements before clicking (green border, pulsing animation)
  - Show scroll animations (smooth scrolling to target position)
  - Display progress indicator (step X of Y)
  - Capture comparison screenshots
- Side-by-side view: Original screenshot | Replay screenshot
- Allow step-by-step or continuous replay
- Show pattern details (selectors, actions, timing)

**Rationale**:
- Visual feedback makes verification intuitive
- Side-by-side comparison shows accuracy
- Step-by-step allows detailed inspection
- Pattern details enable user refinement

**Alternatives Considered**:
- Text-only verification: Not intuitive, hard to verify accuracy
- Video comparison: Larger files, harder to implement
- Automated testing only: Doesn't provide user verification

---

### 6. Configuration Export

**Question**: How to convert learned patterns into crawler configuration?

**Research**:
- Existing crawler uses YAML configuration (planned feature)
- Navigation patterns need to be serializable
- Should integrate with existing crawler's configuration system
- Need to support multiple pattern types (click, scroll, wait, navigate)

**Decision**:
- Export as YAML configuration file with structure:
  ```yaml
  navigation_patterns:
    - name: "navigate_to_bike_page"
      steps:
        - action: "click"
          selector: ".models-dropdown"
          wait: "element_visible"
        - action: "click"
          selector: "text=Panigale V4"
          wait: "navigation"
        - action: "wait"
          duration: 2000
  ```
- Also support JSON export for programmatic use
- Include metadata: pattern name, description, confidence score

**Rationale**:
- YAML is human-readable and aligns with existing crawler plans
- JSON provides programmatic access
- Structured format enables validation
- Metadata helps users understand pattern quality

**Alternatives Considered**:
- Direct code generation: Less flexible, harder to modify
- Binary format: Not human-readable
- Database storage: More complex, not needed for this use case

---

## Technology Choices Summary

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Event Recording | Playwright `page.on()` API | Native, non-intrusive |
| Screenshot Format | PNG (viewport) | Good quality, reasonable size |
| Data Storage | JSON + Pydantic | Type-safe, human-readable |
| Pattern Analysis | Rule-based heuristics | Interpretable, refinable |
| Replay | Playwright automation | Native, reliable |
| Export Format | YAML/JSON | Human-readable, structured |

## Open Questions Resolved

1. ✅ **Event capture granularity**: Capture all clicks, scrolls, navigations (filter noise in analysis)
2. ✅ **Screenshot frequency**: Milestone-based (before/after clicks, scroll milestones)
3. ✅ **Pattern storage**: JSON files per session, YAML for exported patterns
4. ✅ **Replay visualization**: Side-by-side comparison with visual feedback
5. ✅ **Integration approach**: Optional module, no changes to existing crawler

## Dependencies to Add

- **rich** (optional): For terminal UI during teaching mode
  - Rationale: Better user experience for CLI interface
  - Alternative: Use basic print statements (acceptable but less polished)

## Performance Considerations

- **Event capture**: Async handlers, minimal overhead (< 10ms per event)
- **Screenshot capture**: Async writes, optional compression, ~100-200ms per screenshot
- **Pattern analysis**: Batch processing, can run in background
- **Replay**: Real-time with visual feedback, similar to normal Playwright automation

## Security & Privacy

- All data stored locally by default
- No network transmission of teaching data
- User controls what data is saved
- Option to clear/delete teaching sessions
- Screenshots may contain sensitive data - user should be aware

## Next Steps

1. Proceed to Phase 1: Design data models and API contracts
2. Create Pydantic schemas for interaction data
3. Design API interfaces for recording, analysis, replay, export
4. Create quickstart guide for using teaching mode


