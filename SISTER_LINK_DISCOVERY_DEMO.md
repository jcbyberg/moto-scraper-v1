# Sister Link Discovery - Enhanced Navigation Demo

## What the Enhanced Code Does

### Step 1: Menu Navigation (Existing)
1. ✅ Clicks hamburger menu
2. ✅ Clicks BIKES
3. ✅ Expands all categories (DESERTX, XDIAVEL, MONSTER, etc.)
4. ✅ Collects initial bike links from menu

### Step 2: Sister Link Discovery (NEW) 🆕

After collecting links from the menu, the crawler now **visits each bike page** to find related links:

#### A. Tab/Navigation Links
Finds links to related pages:
- **Specs pages**: `/specs`, `/technical`, `/tech-data`
- **Gallery pages**: `/gallery`
- **Features pages**: `/features`, `/equipment`
- **Configurator**: `/configurator`

**Example from Panigale V4 page:**
- Main page: `/ca/en/bikes/panigale/panigale-v4`
- Specs: `/ca/en/bikes/panigale/panigale-v4/specs` (if exists)
- Gallery: `/ca/en/bikes/panigale/panigale-v4/gallery` (if exists)

#### B. Variant Links
Finds model variants that might not be in the main menu:
- **V2, V4 variants**: `/panigale-v2`, `/panigale-v4`
- **SP, RS, R variants**: `/panigale-v4-sp`, `/panigale-v4-rs`
- **Model selector links**: Links in dropdowns or selectors

**Example:**
- From Panigale V4 page, finds:
  - Panigale V2
  - Panigale V4 S
  - Panigale V4 SP
  - Panigale V4 R

#### C. Related Bikes Section
Finds "You may also like" or "Related models" sections:
- Similar bikes
- Same family bikes
- Recommended bikes

#### D. "View All" Links
Finds expansion links:
- "View all models"
- "See all variants"
- "Explore family"

#### E. Hover-Revealed Links
Hovers over dropdown elements to reveal hidden links that only appear on hover.

#### F. Pagination/Load More
Clicks "Load more" buttons to reveal additional content and links.

## Example Discovery Flow

### Before Enhancement:
```
Menu → Collect 50 bike links → Done
```

### After Enhancement:
```
Menu → Collect 50 bike links
  ↓
Visit Bike Page 1 (Panigale V4)
  ├─ Find tabs: specs, gallery, features
  ├─ Find variants: V2, V4 S, V4 SP, V4 R
  ├─ Find related: Panigale V2, Streetfighter V4
  └─ Total: +10 sister links
  ↓
Visit Bike Page 2 (DesertX)
  ├─ Find tabs: specs, gallery
  ├─ Find variants: DesertX Rally, DesertX V2
  └─ Total: +8 sister links
  ↓
... (continues for 30 pages)
  ↓
Final: 50 initial + 200+ sister links = 250+ total links
```

## Code Implementation

The new method `_discover_sister_links_from_page()`:
1. Navigates to bike page
2. Scrolls to trigger lazy loading
3. Searches for:
   - Tab links (specs, gallery, features)
   - Variant links (V2, V4, SP, etc.)
   - Related bike sections
   - "View all" links
   - Hover-revealed links
   - Pagination links
4. Adds all found links to discovered set
5. Moves to next bike page

## Expected Results

**Before:** ~50-100 links from menu
**After:** ~200-500+ links including:
- All bike model pages
- All variant pages
- All specs pages
- All gallery pages
- All features pages
- Related model pages

## Testing

The enhanced code will be tested when:
1. Proxy access is working (or site allows access)
2. Crawler runs and visits bike pages
3. Sister links are discovered and logged

All discovered links are logged with their source (menu vs. sister link discovery).


