# Teaching Mode Usage Guide

## Overview

Teaching mode allows you to interactively teach the crawler how to navigate a website by recording your manual interactions (clicks, scrolls, navigation) in a browser window.

## Requirements

- **Display/X Server**: Teaching mode requires a visible browser window for user interaction
- **Python 3.9+**
- **Playwright** installed (`playwright install chromium`)
- **Dependencies**: See `requirements.txt`

## Running on a Server Without Display

If you're running on a headless server (no X server), you have several options:

### Option 1: Use xvfb (Virtual Display) - Recommended

```bash
# Install xvfb if not already installed
sudo apt-get install xvfb

# Run teaching mode with virtual display
xvfb-run -a python3 scripts/teaching_mode.py start https://www.ducati.com
```

### Option 2: Use X11 Forwarding

```bash
# Connect to server with X11 forwarding
ssh -X user@server

# Then run normally
python3 scripts/teaching_mode.py start https://www.ducati.com
```

### Option 3: Use VNC or Remote Desktop

Set up a VNC server or remote desktop solution, then run teaching mode normally.

### Option 4: Headless Mode (Limited)

```bash
# Run in headless mode (not recommended)
python3 scripts/teaching_mode.py start --headless https://www.ducati.com
```

**Note**: Headless mode is not ideal for teaching mode as it requires real user interaction. The browser won't be visible, making it difficult to navigate and teach the system.

## Basic Usage

### Start a Teaching Session

```bash
python3 scripts/teaching_mode.py start https://www.ducati.com --session-name "ducati_navigation"
```

This will:
- Open a browser window
- Start recording all interactions
- Save data to `teaching_data/sessions/{session_id}/`

### During Recording

- **Click** on elements to navigate
- **Scroll** to find content
- **Navigate** between pages
- All interactions are automatically recorded

### Stop Recording

Press `Ctrl+C` in the terminal to stop recording and save the session.

### View Session Information

```bash
# List all sessions
python3 scripts/teaching_mode.py list

# Show session details
python3 scripts/teaching_mode.py info <session_id>
```

### Analyze Session (Future)

```bash
# Analyze recorded interactions to extract patterns
python3 scripts/teaching_mode.py analyze <session_id>
```

### Verify Patterns (Future)

```bash
# Verify learned navigation patterns
python3 scripts/teaching_mode.py verify <session_id>
```

### Export Patterns (Future)

```bash
# Export patterns to crawler configuration
python3 scripts/teaching_mode.py export <session_id> --output config/patterns.yaml
```

## Session Data Structure

```
teaching_data/
└── sessions/
    └── {session_id}/
        ├── session_data.json      # Complete session data
        └── screenshots/
            ├── scr_xxxxx.png       # Screenshot files
            └── ...
```

## Troubleshooting

### "No X server (DISPLAY) available"

**Solution**: Use one of the options above (xvfb, X11 forwarding, VNC, or headless mode)

### Browser doesn't open

- Check that DISPLAY is set: `echo $DISPLAY`
- Try using xvfb: `xvfb-run -a python3 scripts/teaching_mode.py start <url>`
- Check Playwright installation: `playwright install chromium`

### Interactions not being recorded

- Ensure you're clicking/scroll in the browser window (not programmatically)
- Check that the browser window is focused
- Verify session data is being saved: `python3 scripts/teaching_mode.py list`

## Next Steps

After recording a session:
1. Analyze the session to extract navigation patterns (Phase 4 - coming soon)
2. Verify the patterns work correctly (Phase 5 - coming soon)
3. Export patterns to crawler configuration (Phase 5 - coming soon)


