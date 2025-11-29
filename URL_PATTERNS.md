# Ducati Website URL Patterns

This document describes the URL patterns discovered on the Ducati website to help with systematic crawling and discovery.

## Base URL Structure

All URLs follow the pattern:
```
https://www.ducati.com/{locale}/{language}/{section}/{...}
```

### Locale Prefixes
- `/ww/en/` - Worldwide English (default)
- `/ca/en/` - Canada English
- `/us/en/` - United States English
- `/ww/it/` - Worldwide Italian
- Other locales may exist

## URL Patterns by Page Type

### 1. Main Bike Pages
**Pattern**: `/bikes/{category}/{model-slug}`

**Examples**:
- `https://www.ducati.com/ww/en/bikes/multistrada/multistrada-v4-rally`
- `https://www.ducati.com/ww/en/bikes/panigale/panigale-v4`
- `https://www.ducati.com/ww/en/bikes/monster/monster-v2`

**Structure**:
- Category: `multistrada`, `panigale`, `monster`, `desertx`, `xdiavel`, etc.
- Model slug: lowercase, hyphenated (e.g., `multistrada-v4-rally`, `panigale-v4`)

**Related Pages**:
- Specs: `/bikes/{category}/{model-slug}/specs`
- Gallery: `/bikes/{category}/{model-slug}/gallery`
- Features: `/bikes/{category}/{model-slug}/features`
- Technical: `/bikes/{category}/{model-slug}/technical`

### 2. Heritage Bike Pages
**Pattern**: `/heritage/bikes/{model-slug}`

**Examples**:
- `https://www.ducati.com/ww/en/heritage/bikes/gran-sport-125-marianna`
- `https://www.ducati.com/ww/en/heritage/bikes/cucciolo`
- `https://www.ducati.com/ww/en/heritage/bikes/750-supersport-desmo`

**Listing Page**:
- `https://www.ducati.com/ww/en/heritage/bikes` - Main heritage bikes listing with tabs (ROAD, RACING, etc.)

### 3. Home Page
**Pattern**: `/{locale}/{language}/home`

**Examples**:
- `https://www.ducati.com/ww/en/home`
- `https://www.ducati.com/ca/en/home`
- `https://www.ducati.com/us/en/home`

### 4. Other Sections
- `/configurator` - Bike configurator
- `/compare` - Bike comparison
- `/dealer` - Dealer locator
- `/news` - News and updates
- `/racing` - Racing information

## Discovery Strategy

### For Regular Bikes:
1. Navigate to home page
2. Click hamburger menu → BIKES
3. Expand categories (DESERTX, XDIAVEL, MONSTER, etc.)
4. Extract links from `ul.list` elements
5. Follow links to discover specs/gallery pages

### For Heritage Bikes:
1. Navigate to `/heritage/bikes`
2. Click tabs (ROAD, RACING, etc.)
3. Extract links from images in `div.body`
4. Visit individual heritage bike pages

### Pattern Matching Rules:
- Bike pages: Contains `/bikes/` and not `/compare`, `/configurator`, `/dealer`
- Heritage pages: Contains `/heritage/bikes/` and not just `/heritage/bikes` (listing page)
- Specs pages: Contains `/specs` or `/technical` or `/tech-data`
- Gallery pages: Contains `/gallery` or `/photos` or `/images`

## URL Normalization

When comparing URLs:
1. Remove trailing slashes
2. Convert to lowercase
3. Remove query parameters (unless needed)
4. Normalize locale (all `/ww/en/` variants are equivalent)

## Notes

- Some pages may redirect between locales
- Model slugs are consistent across locales
- Category names match bike families (Multistrada, Panigale, Monster, etc.)
- Heritage bikes use different slug format (often includes year or variant in name)


