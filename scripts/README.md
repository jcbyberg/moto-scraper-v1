# Test Scripts

## test_site_navigation.py

Test script for navigating motorcycle OEM websites that require cookie consent and JavaScript interactions.

### Usage

```bash
# With URL as argument
python scripts/test_site_navigation.py https://example-oem.com

# Interactive mode (will prompt for URL)
python scripts/test_site_navigation.py
```

### What it does

1. **Navigates to the base URL**
2. **Accepts cookies** - Automatically detects and clicks the cookie consent button (supports OneTrust and other common implementations)
3. **Clicks MODELS dropdown** - Finds and clicks the models navigation menu
4. **Selects first model** - Clicks the first model link in the dropdown
5. **Waits for page load** - Ensures the model page is fully loaded
6. **Takes screenshots** - Saves debug screenshots for troubleshooting

### Output

- `debug_dropdown.png` - Screenshot if dropdown selection fails
- `debug_final_page.png` - Screenshot of the final model page
- `debug_error.png` - Screenshot if an error occurs

### Requirements

```bash
pip install playwright
playwright install chromium
```

### Customization

The script uses the following selectors (can be customized in the code):

- Cookie button: `#onetrust-accept-btn-handler` (OneTrust) or fallback to common patterns
- Models dropdown: `a[data-js-shortcutnav=""]:has-text("MODELS")`
- First model: First link in dropdown menu

### Integration with Crawler

This script demonstrates the UI interaction patterns that will be integrated into the main crawler's `PageDiscoveryEngine` and `UIInteractionHandler` components.


