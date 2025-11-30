# Tasks: Teaching Mode

**Input**: Design documents from `/specs/001-teaching-mode/`  
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create teaching module directory structure in src/teaching/
- [X] T002 [P] Create teaching_data directory structure (sessions/, patterns/)
- [X] T003 [P] Add teaching mode dependencies to requirements.txt (Pillow, rich if needed)
- [X] T004 Create scripts/teaching_mode.py CLI entry point skeleton
- [X] T005 [P] Create tests/teaching/ directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Implement Pydantic models in src/teaching/models.py (TeachingSession, InteractionEvent, ClickEvent, ScrollEvent, NavigationEvent, Screenshot, NavigationPattern, PatternRule, TeachingSessionData)
- [X] T007 [P] Implement TeachingSession manager in src/teaching/session.py (create, load, save, update session state)
- [X] T008 [P] Create teaching_data storage utilities in src/teaching/storage.py (save/load session data, screenshot paths)
- [X] T009 Configure logging for teaching mode in src/teaching/__init__.py
- [X] T010 [P] Add teaching_data/ to .gitignore

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Recording Session with Interaction & Screenshot Capture (Priority: P1) 🎯 MVP

**Goal**: User can start a teaching session, navigate a website manually, and have all interactions (clicks, scrolls, navigation) and screenshots automatically recorded and saved.

**Independent Test**: Start a recording session, perform 5 clicks and 2 scrolls, stop session, verify all interactions and screenshots are saved in teaching_data/sessions/{session_id}/

### Implementation for User Story 1

- [X] T011 [US1] Implement InteractionRecorder class in src/teaching/recorder.py with start_recording() method
- [X] T012 [US1] Implement click event capture in src/teaching/recorder.py record_click() method
- [X] T013 [US1] Implement scroll event capture in src/teaching/recorder.py record_scroll() method
- [X] T014 [US1] Implement navigation event capture in src/teaching/recorder.py record_navigation() method
- [X] T015 [US1] Implement screenshot capture in src/teaching/recorder.py capture_screenshot() method (viewport screenshots)
- [X] T016 [US1] Integrate Playwright event listeners in src/teaching/recorder.py (page.on() for click, scroll, navigation)
- [X] T017 [US1] Implement screenshot timing logic in src/teaching/recorder.py (before click, after click, scroll milestones, page load)
- [X] T018 [US1] Implement element metadata extraction in src/teaching/recorder.py (selector, xpath, text, tag, id, classes)
- [X] T019 [US1] Implement stop_recording() method in src/teaching/recorder.py with data persistence
- [X] T020 [US1] Implement CLI start command in scripts/teaching_mode.py (start subcommand)
- [X] T021 [US1] Implement CLI stop command in scripts/teaching_mode.py (stop subcommand)
- [X] T022 [US1] Add error handling for recording failures in src/teaching/recorder.py
- [X] T023 [US1] Add auto-save functionality in src/teaching/recorder.py (periodic saves during recording)
- [X] T024 [US1] Implement visual recording indicator (optional: terminal UI with rich library)
- [ ] T066 [US1] Implement crash recovery in src/teaching/recorder.py (detect and recover from browser crashes, restore session state)
- [ ] T067 [US1] Add error recovery for failed interactions in src/teaching/recorder.py (retry logic, skip failed events, continue recording)

**Checkpoint**: At this point, User Story 1 should be fully functional - user can record a session with all interactions and screenshots saved

---

## Phase 4: User Story 2 - Data Analysis (Priority: P2)

**Goal**: System analyzes recorded interactions to extract navigation patterns with selectors, actions, and timing rules.

**Independent Test**: Load a recorded session with 20+ interactions, run analysis, verify patterns are extracted with confidence scores and rules.

### Implementation for User Story 2

- [ ] T025 [US2] Implement PatternAnalyzer class in src/teaching/analyzer.py with analyze_session() method
- [ ] T026 [US2] Implement selector extraction in src/teaching/analyzer.py extract_selectors() method (CSS, XPath, text strategies)
- [ ] T027 [US2] Implement sequence identification in src/teaching/analyzer.py identify_sequences() method (group consecutive interactions)
- [ ] T028 [US2] Implement pattern rule generation in src/teaching/analyzer.py generate_pattern_rules() method (convert sequences to rules)
- [ ] T029 [US2] Implement confidence score calculation in src/teaching/analyzer.py calculate_confidence() method
- [ ] T030 [US2] Implement timing pattern analysis in src/teaching/analyzer.py (extract delays, wait conditions)
- [ ] T031 [US2] Implement pattern naming and description generation in src/teaching/analyzer.py
- [ ] T032 [US2] Implement CLI analyze command in scripts/teaching_mode.py (analyze subcommand)
- [ ] T033 [US2] Add pattern storage to session data in src/teaching/analyzer.py (save patterns to TeachingSessionData)
- [ ] T034 [US2] Add progress reporting during analysis in src/teaching/analyzer.py

**Checkpoint**: At this point, User Story 2 should be fully functional - system can analyze sessions and extract navigation patterns

---

## Phase 5: User Story 3 - Verification & Export (Priority: P2)

**Goal**: System demonstrates learned patterns to user for verification, allows approval/rejection, and exports approved patterns to crawler configuration.

**Independent Test**: Load a session with extracted patterns, replay a pattern, verify visual feedback and comparison screenshots, approve pattern, export to YAML config.

### Implementation for User Story 3

- [ ] T035 [US3] Implement PatternReplayer class in src/teaching/replayer.py with replay_pattern() method
- [ ] T036 [US3] Implement element highlighting in src/teaching/replayer.py highlight_element() method (CSS injection for visual feedback)
- [ ] T037 [US3] Implement pattern demonstration in src/teaching/replayer.py demonstrate_pattern() method (replay with comparison)
- [ ] T038 [US3] Implement screenshot comparison capture in src/teaching/replayer.py (original vs replay screenshots)
- [ ] T039 [US3] Implement ReplayResult and Demonstration data classes in src/teaching/replayer.py
- [ ] T040 [US3] Implement pattern verification UI in scripts/verify_patterns.py (approve/reject/refine patterns)
- [ ] T041 [US3] Implement ConfigExporter class in src/teaching/exporter.py with export_patterns() method
- [ ] T042 [US3] Implement YAML export in src/teaching/exporter.py export_to_file() method
- [ ] T043 [US3] Implement JSON export in src/teaching/exporter.py export_to_file() method
- [ ] T044 [US3] Implement crawler config generation in src/teaching/exporter.py generate_crawler_config() method
- [ ] T045 [US3] Implement pattern validation in src/teaching/exporter.py validate_pattern() method
- [ ] T046 [US3] Implement CLI verify command in scripts/teaching_mode.py (verify subcommand)
- [ ] T047 [US3] Implement CLI export command in scripts/teaching_mode.py (export subcommand)
- [ ] T048 [US3] Add pattern approval/rejection tracking in src/teaching/models.py (update NavigationPattern.verified field)

**Checkpoint**: At this point, User Story 3 should be fully functional - user can verify patterns and export them to crawler configuration

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T049 [P] Add comprehensive error handling across all teaching modules
- [ ] T050 [P] Add structured logging throughout teaching mode (all operations)
- [ ] T051 [P] Implement session management CLI commands in scripts/teaching_mode.py (list, info, delete subcommands)
- [ ] T052 [P] Add screenshot compression option in src/teaching/recorder.py (optional Pillow compression)
- [ ] T053 [P] Add full page screenshot option in src/teaching/recorder.py (configurable viewport vs full page)
- [ ] T054 [P] Implement data format versioning support in src/teaching/models.py (TeachingSessionData.version)
- [ ] T055 [P] Add session resume functionality in src/teaching/session.py (resume paused sessions)
- [ ] T056 [P] Create unit tests for models in tests/teaching/test_models.py
- [ ] T057 [P] Create unit tests for recorder in tests/teaching/test_recorder.py
- [ ] T058 [P] Create unit tests for analyzer in tests/teaching/test_analyzer.py
- [ ] T059 [P] Create unit tests for replayer in tests/teaching/test_replayer.py
- [ ] T060 [P] Create unit tests for exporter in tests/teaching/test_exporter.py
- [ ] T061 [P] Create integration tests for full teaching workflow in tests/teaching/test_integration.py
- [ ] T062 [P] Update README.md with teaching mode usage instructions
- [ ] T063 [P] Validate quickstart.md examples work correctly
- [ ] T064 [P] Add type hints to all functions (per constitution requirement)
- [ ] T065 [P] Code cleanup and refactoring (remove TODOs, optimize imports)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed sequentially in priority order (US1 → US2 → US3)
  - US2 depends on US1 (needs recorded data to analyze)
  - US3 depends on US2 (needs analyzed patterns to verify/export)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs recorded session data to analyze)
- **User Story 3 (P2)**: Depends on US2 completion (needs analyzed patterns to verify/export)

### Within Each User Story

- Models before services (models in Phase 2, used by all stories)
- Core recording before analysis (US1 before US2)
- Analysis before verification (US2 before US3)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002, T003, T005 can run in parallel
- **Phase 2**: T006, T007, T008, T010 can run in parallel
- **Phase 3**: T011-T018 can be worked on in parallel (different methods in same file, but can be implemented incrementally)
- **Phase 4**: T025-T031 can be worked on in parallel (different methods)
- **Phase 5**: T035-T048 can be worked on in parallel (different components)
- **Phase 6**: All tasks marked [P] can run in parallel

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch all foundational tasks together:
Task: "Implement Pydantic models in src/teaching/models.py"
Task: "Implement TeachingSession manager in src/teaching/session.py"
Task: "Create teaching_data storage utilities in src/teaching/storage.py"
Task: "Add teaching_data/ to .gitignore"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Recording with interactions and screenshots)
4. **STOP and VALIDATE**: Test User Story 1 independently - record a session, verify data is saved
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP - can record sessions!)
3. Add User Story 2 → Test independently → Deploy/Demo (can analyze patterns!)
4. Add User Story 3 → Test independently → Deploy/Demo (can verify and export!)
5. Add Polish → Finalize and optimize

### Sequential Strategy (Recommended)

Since US2 depends on US1 and US3 depends on US2:

1. Team completes Setup + Foundational together
2. Complete User Story 1 (recording)
3. Complete User Story 2 (analysis)
4. Complete User Story 3 (verification & export)
5. Complete Polish phase

---

## Task Summary

- **Total Tasks**: 67 (added T066, T067 for crash/error recovery)
- **Phase 1 (Setup)**: 5 tasks
- **Phase 2 (Foundational)**: 5 tasks
- **Phase 3 (US1 - Recording)**: 16 tasks (added T066, T067)
- **Phase 4 (US2 - Analysis)**: 10 tasks
- **Phase 5 (US3 - Verification)**: 14 tasks
- **Phase 6 (Polish)**: 17 tasks

### MVP Scope (User Story 1)

- **MVP Tasks**: Phases 1, 2, and 3 (26 tasks total, including T066-T067)
- **MVP Deliverable**: User can record teaching sessions with all interactions and screenshots saved
- **MVP Test**: Record a session, verify data persistence

### Independent Test Criteria

- **US1**: Start recording, perform interactions, stop recording, verify all data saved in teaching_data/sessions/{session_id}/
- **US2**: Load recorded session, run analysis, verify patterns extracted with rules and confidence scores
- **US3**: Load analyzed patterns, replay one pattern, verify visual feedback, approve pattern, export to YAML config

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All code must follow project constitution (Python, type hints, structured logging, error handling)

