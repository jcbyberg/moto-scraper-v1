# Teaching Mode Feature Specification

## Overview

A teaching mode system that allows users to interactively teach the AI how to navigate a website. The user performs manual navigation (clicks, scrolls) while the system records all interactions, captures screenshots, and analyzes the collected data to learn navigation patterns. The learned patterns are then demonstrated back to the user for verification.

## User Stories

### Primary User Story
**As a** user configuring the crawler for a new website  
**I want to** teach the AI how to navigate the site by clicking through it myself  
**So that** the crawler can learn the correct navigation patterns and apply them automatically

### Detailed User Stories

1. **Recording Session**
   - **As a** user  
   - **I want to** start a teaching session where my browser interactions are recorded  
   - **So that** the system can learn from my navigation patterns

2. **Interaction Capture**
   - **As a** user  
   - **I want** all my clicks, scrolls, and page navigations to be automatically captured  
   - **So that** the system has complete data about how I navigate the site

3. **Screenshot Capture**
   - **As a** user  
   - **I want** screenshots to be taken at key interaction points  
   - **So that** the system can see the visual context of my actions

4. **Data Analysis**
   - **As a** user  
   - **I want** the system to analyze my recorded interactions  
   - **So that** it can identify patterns and extract navigation rules

5. **Verification**
   - **As a** user  
   - **I want** to see the system demonstrate the learned navigation patterns  
   - **So that** I can verify the AI understood my teaching correctly

## Functional Requirements

### FR1: Teaching Session Management
- System must provide a way to start/stop a teaching session
- Session state must be persistent (can be resumed)
- Session metadata must be saved (start time, duration, target URL)

### FR2: Interaction Recording
- **Clicks**: Record all mouse clicks including:
  - Element selector (CSS/XPath)
  - Element text/content
  - Element type (button, link, dropdown, etc.)
  - Timestamp
  - Page URL at time of click
  - Scroll position
- **Scrolls**: Record all scroll events including:
  - Scroll direction (up/down/left/right)
  - Scroll distance
  - Final scroll position
  - Timestamp
  - Page URL
- **Navigation**: Record page transitions including:
  - Source URL
  - Target URL
  - Navigation method (click, form submit, direct URL, etc.)
  - Timestamp

### FR3: Screenshot Capture
- Capture screenshots at:
  - Start of each page load
  - Before each click
  - After each click
  - At scroll milestones (every N pixels or at element visibility changes)
  - End of page load
- Screenshots must include:
  - Full page or viewport (configurable)
  - Timestamp
  - Associated interaction event ID
  - Page URL

### FR4: Data Storage
- Store all recorded data in structured format (JSON)
- Organize by session ID
- Include metadata: session info, browser info, timestamps
- Support export/import of teaching data

### FR5: Pattern Analysis
- Analyze recorded interactions to identify:
  - Common navigation paths
  - Element selection patterns (how user identifies clickable elements)
  - Scroll patterns (when/why user scrolls)
  - Timing patterns (delays between actions)
  - Page structure patterns (common layouts, element hierarchies)
- Generate navigation rules from patterns:
  - Selector strategies (CSS selectors, XPath, text matching)
  - Wait conditions (element visibility, page load, custom delays)
  - Action sequences (click → wait → scroll → click)

### FR6: Demonstration & Verification
- Replay learned navigation patterns:
  - Execute actions in automated browser
  - Show visual feedback (highlight clicked elements, show scrolls)
  - Display screenshots from original teaching session alongside replay
- Allow user to:
  - Approve patterns (mark as correct)
  - Reject patterns (mark as incorrect, re-teach)
  - Refine patterns (adjust selectors, timing, sequences)
- Generate navigation configuration from approved patterns

### FR7: Integration with Crawler
- Convert approved navigation patterns into crawler configuration
- Export patterns as:
  - Site-specific configuration file (YAML/JSON)
  - Playwright script snippets
  - Custom navigation functions for crawler

## Technical Requirements

### TR1: Browser Integration
- Must use Playwright for browser automation
- Support both recording (user-controlled) and replay (automated) modes
- Handle browser events (clicks, scrolls, navigation) in real-time

### TR2: Performance
- Recording must not significantly impact browser performance
- Screenshot capture must be efficient (async, optional compression)
- Analysis should complete within reasonable time (< 5 minutes for typical session)

### TR3: Data Format
- Use structured JSON for interaction data
- Use standard image formats (PNG/JPEG) for screenshots
- Support versioning of data format for future compatibility

### TR4: User Interface
- Provide visual indicators during recording (recording indicator, interaction counter)
- Show progress during analysis
- Display verification interface with side-by-side comparison

## Non-Functional Requirements

### NFR1: Usability
- Teaching mode must be easy to start/stop
- Clear visual feedback during recording
- Intuitive verification interface

### NFR2: Reliability
- Must not lose recorded data if browser crashes
- Periodic auto-save during recording
- Error recovery for failed interactions

### NFR3: Privacy
- All data stored locally by default
- User controls what data is saved
- Option to clear teaching data

## Constraints

- Must work with existing Playwright-based crawler architecture
- Must not break existing crawler functionality
- Must follow project constitution (Python, metric units for any measurements, etc.)

## Out of Scope

- Multi-user teaching sessions
- Cloud-based teaching data storage
- Real-time collaboration on teaching
- Automatic pattern improvement from multiple sessions (future enhancement)

## Success Criteria

1. User can successfully record a navigation session
2. System captures all clicks, scrolls, and screenshots accurately
3. System analyzes patterns and generates navigation rules
4. System can replay learned patterns for user verification
5. User can approve patterns and generate crawler configuration
6. Generated configuration works with existing crawler


