# Implementation Plan: Teaching Mode

**Branch**: `001-teaching-mode` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-teaching-mode/spec.md`

## Summary

Implement a teaching mode system that allows users to interactively teach the AI how to navigate websites by recording their manual interactions (clicks, scrolls, navigation) along with screenshots. The system analyzes the recorded data to extract navigation patterns, then demonstrates the learned patterns back to the user for verification. Approved patterns are converted into crawler configuration for automated use.

**Technical Approach**: Extend the existing Playwright-based crawler with a recording mode that captures browser events, stores interaction data in structured JSON format, performs pattern analysis to generate navigation rules, and provides a verification interface for user approval. The system integrates seamlessly with the existing crawler architecture.

## Technical Context

**Language/Version**: Python 3.9+ (per project constitution)  
**Primary Dependencies**: 
- Playwright (>=1.40.0) - Browser automation and event recording
- asyncio - Asynchronous event handling
- aiofiles (>=23.0.0) - Async file operations for saving interaction data
- Pydantic (>=2.0) - Schema validation for interaction data models
- Pillow (>=10.0) - Image processing for screenshots
- rich - Terminal UI for teaching mode interface (optional)

**Storage**: 
- JSON files for interaction data (one per teaching session)
- Image files (PNG/JPEG) for screenshots organized by session
- YAML/JSON configuration files for exported navigation patterns

**Testing**: pytest with async support, pytest-playwright for browser testing  
**Target Platform**: Linux (primary), cross-platform (Windows, macOS)  
**Project Type**: Single project - extension to existing crawler  
**Performance Goals**: 
- Recording overhead: < 50ms per interaction event
- Screenshot capture: < 200ms per screenshot
- Pattern analysis: < 5 minutes for typical session (100-200 interactions)
- Replay demonstration: Real-time with visual feedback

**Constraints**: 
- Must not break existing crawler functionality
- Must follow project constitution (Python, metric units, no guessing values)
- Recording must be non-intrusive (minimal performance impact)
- Data must be stored locally by default
- Must work with existing Playwright browser context management

**Scale/Scope**: 
- Support teaching sessions with 50-500 interactions
- Handle 10-100 screenshots per session
- Generate navigation rules for 1-10 distinct navigation patterns per session
- Support multiple teaching sessions per site (can merge/refine patterns)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Compliance Check

1. **Python Language**: ✅ Feature will be implemented in Python
2. **Playwright Usage**: ✅ Uses Playwright for browser automation (existing requirement)
3. **Rate Limiting**: ✅ Teaching mode respects user's natural pace (no automated rate limiting needed during teaching)
4. **Data Quality**: ✅ No guessing - all data comes from actual user interactions
5. **Error Handling**: ✅ Must handle recording failures gracefully
6. **Logging**: ✅ Structured logging for all recording and analysis operations
7. **Type Hints**: ✅ All functions must have type hints
8. **Metric Units**: ✅ N/A for this feature (no measurements to convert)

### ⚠️ Considerations

- **New Component**: This adds a new major component (teaching mode) but doesn't violate architecture principles
- **Storage**: Uses file-based storage (JSON, images) which aligns with existing crawler's file-based approach
- **Integration**: Must integrate cleanly with existing crawler without breaking changes

**Gate Status**: ✅ **PASS** - No constitution violations (see `.specify/memory/constitution.md` for full principles)

## Project Structure

### Documentation (this feature)

```text
specs/001-teaching-mode/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── teaching/            # New module for teaching mode
│   ├── __init__.py
│   ├── recorder.py      # InteractionRecorder - captures browser events
│   ├── analyzer.py      # PatternAnalyzer - analyzes interactions to extract patterns
│   ├── replayer.py      # PatternReplayer - demonstrates learned patterns
│   ├── session.py       # TeachingSession - manages session state
│   ├── models.py        # Pydantic models for interaction data
│   └── exporter.py      # ConfigExporter - converts patterns to crawler config
├── crawler/             # Existing (no changes)
├── extractors/          # Existing (no changes)
├── processors/          # Existing (no changes)
├── downloaders/         # Existing (no changes)
├── writers/             # Existing (no changes)
└── utils/               # Existing (no changes)

scripts/
├── teaching_mode.py     # CLI entry point for teaching mode
└── verify_patterns.py   # CLI for pattern verification

tests/
├── teaching/            # New test module
│   ├── test_recorder.py
│   ├── test_analyzer.py
│   ├── test_replayer.py
│   ├── test_session.py
│   └── test_exporter.py
├── crawler/             # Existing tests (no changes)
└── ...                  # Other existing tests

teaching_data/           # New directory for teaching session data
├── sessions/            # Per-session interaction data
│   └── {session_id}/
│       ├── interactions.json
│       ├── metadata.json
│       └── screenshots/
│           └── {timestamp}_{event_id}.png
└── patterns/           # Exported navigation patterns
    └── {site_name}_patterns.yaml
```

**Structure Decision**: Single project structure with new `teaching/` module. Teaching mode is integrated as an optional feature that extends the existing crawler without modifying core components. Teaching data is stored separately from crawler output to maintain clear separation.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - all complexity is justified by feature requirements.

## Phase 0: Outline & Research

### Research Tasks

1. **Playwright Event Recording**
   - Research Playwright's event listener API for capturing user interactions
   - Investigate best practices for non-intrusive event recording
   - Determine optimal event capture granularity (all events vs. filtered)

2. **Screenshot Capture Strategies**
   - Research efficient screenshot capture in Playwright (full page vs. viewport)
   - Investigate screenshot compression and storage optimization
   - Determine optimal screenshot timing (before/after events, milestones)

3. **Pattern Analysis Algorithms**
   - Research pattern recognition approaches for UI interaction sequences
   - Investigate selector generation strategies (CSS, XPath, text matching)
   - Study timing pattern analysis (delays, wait conditions)

4. **Data Model Design**
   - Research structured formats for interaction data (JSON schema)
   - Investigate versioning strategies for interaction data format
   - Study metadata requirements for teaching sessions

5. **Replay & Verification UI**
   - Research Playwright's programmatic interaction API for replay
   - Investigate visual feedback techniques (element highlighting, progress indicators)
   - Study comparison interfaces (side-by-side original vs. replay)

6. **Configuration Export**
   - Research YAML/JSON schema for navigation patterns
   - Investigate integration points with existing crawler configuration
   - Study pattern serialization and deserialization

**Output**: `research.md` with all technical decisions and rationale

## Phase 1: Design & Contracts

### Data Model

**Entities to Model**:
- `TeachingSession` - Session metadata, state, timestamps
- `InteractionEvent` - Base class for all interaction types
  - `ClickEvent` - Click interactions with element details
  - `ScrollEvent` - Scroll interactions with direction/distance
  - `NavigationEvent` - Page navigation events
- `Screenshot` - Screenshot metadata and file reference
- `NavigationPattern` - Extracted pattern with selectors, actions, timing
- `PatternRule` - Individual rule within a pattern (selector, action, wait condition)

**Relationships**:
- Session → Events (1:N)
- Event → Screenshot (1:1 or 1:N, depending on capture strategy)
- Session → Patterns (1:N, after analysis)
- Pattern → Rules (1:N)

### API Contracts

**Recording API**:
- `start_session(url: str) -> TeachingSession`
- `stop_session(session_id: str) -> None`
- `record_interaction(event: InteractionEvent) -> None`
- `capture_screenshot(event_id: str, trigger: str) -> Screenshot`

**Analysis API**:
- `analyze_session(session_id: str) -> List[NavigationPattern]`
- `extract_selectors(events: List[ClickEvent]) -> Dict[str, str]`
- `identify_patterns(events: List[InteractionEvent]) -> List[NavigationPattern]`

**Replay API**:
- `replay_pattern(pattern: NavigationPattern, browser: Browser) -> ReplayResult`
- `demonstrate_pattern(pattern: NavigationPattern) -> Demonstration`

**Export API**:
- `export_patterns(patterns: List[NavigationPattern], format: str) -> str`
- `generate_crawler_config(patterns: List[NavigationPattern]) -> Dict`

**Output**: 
- `data-model.md` - Complete data model with Pydantic schemas
- `contracts/` - API contracts (OpenAPI/JSON schema)
- `quickstart.md` - Quick start guide for using teaching mode

## Phase 2: Implementation Planning

*Note: Phase 2 (task breakdown) is handled by `/speckit.tasks` command, not this plan.*

The implementation will be broken down into tasks covering:
- Core recording infrastructure
- Event capture and storage
- Screenshot management
- Pattern analysis algorithms
- Replay and verification
- Configuration export
- Integration with existing crawler
- Testing and documentation

## Dependencies

### External Dependencies
- Playwright (existing)
- Pydantic (existing)
- aiofiles (existing)
- Pillow (may need to add if not present)

### Internal Dependencies
- Existing crawler architecture (no modifications needed)
- Existing configuration system (for pattern export integration)

## Risks & Mitigations

### Risk 1: Performance Impact During Recording
**Mitigation**: Use async event handlers, batch screenshot writes, optional compression

### Risk 2: Pattern Analysis Accuracy
**Mitigation**: Start with simple patterns, allow user refinement, iterative improvement

### Risk 3: Integration Complexity
**Mitigation**: Design as optional feature, use dependency injection, comprehensive testing

### Risk 4: Data Storage Growth
**Mitigation**: Optional screenshot compression, cleanup utilities, configurable retention

## Success Metrics

1. User can record a 50-interaction session with < 5% performance impact
2. Pattern analysis identifies at least 80% of navigation patterns correctly
3. Replay demonstrates patterns with visual accuracy matching original
4. Exported configuration successfully works with existing crawler
5. Teaching mode can be enabled/disabled without affecting normal crawler operation
