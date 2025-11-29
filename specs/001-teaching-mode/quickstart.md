# Quick Start: Teaching Mode

**Feature**: Teaching Mode for Website Navigation  
**Date**: 2025-01-27

## Overview

Teaching mode allows you to interactively teach the crawler how to navigate a website by recording your manual interactions. The system learns from your actions and generates navigation patterns that can be used for automated crawling.

## Prerequisites

- Python 3.9+
- Playwright installed (`playwright install chromium`)
- Project dependencies installed (`pip install -r requirements.txt`)

## Basic Usage

### 1. Start a Teaching Session

```bash
python scripts/teaching_mode.py start https://www.ducati.com --session-name "ducati_navigation"
```

This will:
- Open a browser window
- Start recording your interactions
- Save all clicks, scrolls, and screenshots

### 2. Navigate the Website

In the browser window that opens:
- Click through the website normally
- Navigate to bike pages
- Scroll to find content
- The system records everything automatically

### 3. Stop Recording

Press `Ctrl+C` in the terminal or click the "Stop Recording" button in the browser.

```bash
# Or use the stop command
python scripts/teaching_mode.py stop --session-id <session_id>
```

### 4. Analyze the Session

```bash
python scripts/teaching_mode.py analyze <session_id>
```

This will:
- Analyze your recorded interactions
- Extract navigation patterns
- Generate pattern rules with selectors and actions

### 5. Verify Patterns

```bash
python scripts/teaching_mode.py verify <session_id>
```

This will:
- Replay each learned pattern
- Show side-by-side comparison (original vs. replay)
- Allow you to approve or reject patterns

### 6. Export Configuration

```bash
python scripts/teaching_mode.py export <session_id> --output config/ducati_patterns.yaml
```

This will:
- Export approved patterns to YAML configuration
- Generate crawler-compatible configuration
- Save to specified file

## Example Workflow

### Teaching Navigation to Bike Pages

1. **Start session**:
   ```bash
   python scripts/teaching_mode.py start https://www.ducati.com
   ```

2. **Navigate manually**:
   - Click "Models" dropdown
   - Click "Panigale V4"
   - Scroll down to see specifications
   - Click "View Details"

3. **Stop and analyze**:
   ```bash
   python scripts/teaching_mode.py stop
   python scripts/teaching_mode.py analyze <session_id>
   ```

4. **Review patterns**:
   The system will identify patterns like:
   - "Click Models dropdown → Wait for menu → Click bike name → Wait for navigation"

5. **Verify**:
   ```bash
   python scripts/teaching_mode.py verify <session_id>
   ```
   Review the replay to ensure patterns are correct.

6. **Export**:
   ```bash
   python scripts/teaching_mode.py export <session_id> --output config/ducati_patterns.yaml
   ```

## Using Exported Patterns

The exported configuration can be used with the crawler:

```python
from src.crawler.discovery import PageDiscoveryEngine
from src.teaching.exporter import load_patterns

# Load patterns from config
patterns = load_patterns("config/ducati_patterns.yaml")

# Use with crawler
engine = PageDiscoveryEngine(base_url="https://www.ducati.com")
engine.apply_navigation_patterns(patterns)
```

## Session Management

### List Sessions

```bash
python scripts/teaching_mode.py list
```

### View Session Details

```bash
python scripts/teaching_mode.py info <session_id>
```

### Delete Session

```bash
python scripts/teaching_mode.py delete <session_id>
```

## Tips for Best Results

1. **Be Consistent**: Use the same navigation path multiple times to help the system identify patterns
2. **Clear Actions**: Make deliberate clicks and scrolls - avoid rapid clicking
3. **Complete Flows**: Navigate through complete user flows (e.g., homepage → bike page → specs)
4. **Wait for Loads**: Allow pages to fully load before clicking (helps with timing analysis)
5. **Multiple Sessions**: Create separate sessions for different navigation patterns

## Troubleshooting

### Pattern Not Detected

- Ensure you perform the same navigation multiple times
- Check that element selectors are stable (not randomly generated)
- Verify screenshots show the expected page state

### Replay Fails

- Check that selectors are still valid (site may have changed)
- Verify wait conditions are appropriate
- Review error messages in replay output

### Low Confidence Scores

- Patterns with low confidence (< 0.5) may need manual refinement
- Review selector strategies and adjust if needed
- Consider re-teaching the pattern

## Next Steps

- See `data-model.md` for data structure details
- See `contracts/` for API documentation
- See `plan.md` for implementation details


