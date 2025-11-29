# Export API Contract

**Module**: `src.teaching.exporter`  
**Purpose**: Export learned patterns to crawler configuration

## Classes

### ConfigExporter

Exports navigation patterns to crawler configuration formats.

#### Methods

##### `export_patterns(patterns: List[NavigationPattern], format: str = "yaml") -> str`

Export navigation patterns to configuration format.

**Parameters**:
- `patterns: List[NavigationPattern]` - List of patterns to export
- `format: str` - Export format: "yaml" or "json"

**Returns**: `str` - Configuration file content as string

**Raises**:
- `ExportError` - If export fails (invalid format, etc.)

---

##### `export_to_file(patterns: List[NavigationPattern], file_path: str, format: str = "yaml") -> None`

Export navigation patterns to a file.

**Parameters**:
- `patterns: List[NavigationPattern]` - List of patterns to export
- `file_path: str` - Path to output file
- `format: str` - Export format: "yaml" or "json" (inferred from file extension if not specified)

**Returns**: `None`

**Side Effects**:
- Creates or overwrites configuration file
- Writes pattern data in specified format

**Raises**:
- `ExportError` - If file write fails
- `InvalidFormatError` - If format is not supported

---

##### `generate_crawler_config(patterns: List[NavigationPattern]) -> Dict`

Generate crawler configuration dictionary from patterns.

**Parameters**:
- `patterns: List[NavigationPattern]` - List of verified patterns

**Returns**: `Dict` - Configuration dictionary compatible with crawler

**Configuration Structure**:
```python
{
    "navigation_patterns": [
        {
            "name": "navigate_to_bike_page",
            "description": "Navigate from homepage to bike model page",
            "steps": [
                {
                    "action": "click",
                    "selector": ".models-dropdown",
                    "selector_strategy": "css",
                    "wait": "element_visible",
                    "wait_duration_ms": 500
                },
                {
                    "action": "click",
                    "selector": "text=Panigale V4",
                    "selector_strategy": "text",
                    "wait": "navigation",
                    "wait_duration_ms": 2000
                }
            ]
        }
    ],
    "metadata": {
        "exported_at": "2025-01-27T10:30:00Z",
        "pattern_count": 1,
        "source_sessions": ["session_id_1"]
    }
}
```

---

##### `validate_pattern(pattern: NavigationPattern) -> bool`

Validate that a pattern can be exported (all required fields present).

**Parameters**:
- `pattern: NavigationPattern` - Pattern to validate

**Returns**: `bool` - True if pattern is valid for export

**Validation Rules**:
- Pattern must have at least one rule
- All rules must have valid selectors
- All rules must have valid actions
- Wait conditions must be valid

---

## Configuration Format

### YAML Format

```yaml
navigation_patterns:
  - name: "navigate_to_bike_page"
    description: "Navigate from homepage to bike model page"
    steps:
      - step_number: 1
        action: "click"
        selector: ".models-dropdown"
        selector_strategy: "css"
        wait_condition: "element_visible"
        wait_duration_ms: 500
      - step_number: 2
        action: "click"
        selector: "text=Panigale V4"
        selector_strategy: "text"
        wait_condition: "navigation"
        wait_duration_ms: 2000
metadata:
  exported_at: "2025-01-27T10:30:00Z"
  pattern_count: 1
  source_sessions:
    - "550e8400-e29b-41d4-a716-446655440000"
```

### JSON Format

Same structure as YAML, but in JSON format.

---

## Exceptions

### `ExportError`

Base exception for export-related errors.

**Attributes**:
- `message: str` - Error message
- `pattern_ids: List[str]` - Associated pattern IDs

---

### `InvalidFormatError`

Exception raised when export format is not supported.

**Inherits from**: `ExportError`

**Attributes**:
- `format: str` - Unsupported format
- `supported_formats: List[str]` - List of supported formats

---

### `ValidationError`

Exception raised when pattern validation fails.

**Inherits from**: `ExportError`

**Attributes**:
- `pattern_id: str` - Pattern that failed validation
- `validation_errors: List[str]` - List of validation error messages


