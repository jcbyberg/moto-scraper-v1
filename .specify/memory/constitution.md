# Motorcycle OEM Web-Crawler Constitution

## Core Principles

### I. Python-First Development (MUST)
All code MUST be written in Python 3.9+. No exceptions. This ensures consistency, maintainability, and alignment with the existing codebase.

### II. Type Safety & Code Quality (MUST)
- All function signatures MUST have type hints
- Use Pydantic for data validation and schema enforcement
- Follow Python typing best practices (typing module, Optional, List, Dict, etc.)

### III. Metric Units Requirement (MUST)
All measurements MUST be in metric units:
- Length/dimensions: millimeters (mm)
- Weight: kilograms (kg)
- Displacement: cubic centimeters (cc)
- Power: kilowatts (kW) - convert from hp: 1 hp ≈ 0.7457 kW
- Torque: Newton-meters (Nm)
- Speed: kilometers per hour (km/h)
- Volume: liters (L)
- Fuel consumption: liters per 100 kilometers (L/100km)

### IV. Data Quality (MUST)
- **NO guessing values**: If a specification is not found, use `None` or omit the field
- **Preserve precision**: Maintain original precision when converting units
- **Type validation**: Ensure numeric fields are properly typed (int vs float)
- **Required fields**: Manufacturer, model, and year are mandatory; all others optional

### V. Async-First Architecture (MUST)
All I/O operations MUST use async/await:
- File operations: Use aiofiles
- HTTP requests: Use aiohttp or Playwright async API
- Database operations: Use async drivers
- Browser automation: Use Playwright async API exclusively

### VI. Structured Logging (MUST)
- All operations MUST use structured logging
- Use the project's logging utilities (src/utils/logging.py)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include context (URLs, session IDs, operation names) in log messages

### VII. Error Handling (MUST)
- All operations MUST have try/except blocks with graceful degradation
- Never crash the entire crawler due to a single page failure
- Log errors with full context
- Continue processing other items when one fails

### VIII. Rate Limiting & Respectful Crawling (MUST)
- Minimum 2-3 seconds between requests (configurable via rate_limit parameter)
- Respect robots.txt directives
- Use descriptive, honest user-agent strings
- Limit retries to 3 attempts with exponential backoff
- Save state frequently for resumable crawls

### IX. Output Organization (MUST)
- One markdown file per bike/year: `{manufacturer}_{model}_{year}.md`
- Images organized: `images/{manufacturer}/{model}/{year}/`
- Semantic image naming: `{manufacturer}_{model}_{year}_{type}_{index}.{ext}`
- Relative paths in markdown files
- Metadata files: JSON per bike with normalized data

### X. Multi-Page Data Merging (MUST)
When a bike is described across multiple pages:
- Merge data from all pages for the same bike/year
- Track source attribution
- Conflict resolution: Prefer specs page > main page > gallery page
- Combine and deduplicate feature lists
- Aggregate all source URLs in output

## Additional Constraints

### Technology Stack
- **Primary Language**: Python 3.9+
- **Browser Automation**: Playwright (>=1.40.0)
- **Async HTTP**: aiohttp (>=3.9.0)
- **File Operations**: aiofiles (>=23.0.0)
- **Data Validation**: Pydantic (>=2.0)
- **HTML Parsing**: BeautifulSoup4 (>=4.12.0), lxml (>=4.9.0)

### Performance Standards
- Page discovery: Complete within reasonable time (< 30 minutes for typical site)
- Data extraction: < 5 seconds per page
- Image download: < 2 seconds per image (network dependent)
- State persistence: < 100ms per save operation

### Security Requirements
- No hardcoded credentials
- Respect robots.txt and site terms
- Use secure HTTP practices (HTTPS where available)
- Store sensitive data securely (if any)

## Development Workflow

### Code Review Requirements
- All code must follow constitution principles
- Type hints required on all functions
- Logging must be structured
- Error handling must be comprehensive
- Tests should be added for new functionality

### Quality Gates
- Code must pass type checking (mypy)
- Code must be formatted (black)
- All tests must pass (pytest)
- Constitution compliance verified before merge

### Testing Requirements
- Unit tests for utility functions (unit conversion, schema validation)
- Integration tests for end-to-end workflows
- Test data: Mock HTML pages with various structures
- Error scenarios must be tested

## Governance

**Constitution Authority**: This constitution supersedes all other practices and documentation. Any conflicts must be resolved by updating the conflicting document, not by diluting or ignoring constitutional principles.

**Amendments**: Constitution changes require:
1. Documentation of the change rationale
2. Approval process
3. Migration plan for existing code
4. Update to all dependent documentation

**Compliance**: All PRs and code reviews must verify constitution compliance. Complexity must be justified. Use CLAUDE.md and project documentation for runtime development guidance.

**Version**: 1.0.0 | **Ratified**: 2025-01-27 | **Last Amended**: 2025-11-29
