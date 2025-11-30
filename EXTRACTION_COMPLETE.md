# Complete Extraction Summary - Multistrada V4 Rally

## ✅ Extraction Complete

All data has been extracted from the Multistrada V4 Rally page, including:
- ✅ All image URLs (30 total)
- ✅ Video poster images
- ✅ Content sections from div.content elements
- ✅ Tooltip content from hotspot buttons
- ✅ Specifications
- ✅ Features
- ✅ Description

## 📸 Image URLs (30 total)

### Video Poster Images (Hero)
1. `https://images.ctfassets.net/x7j9qwvpvr5s/5IXVgkiu7t0lkRsePf83gN/bcf2d82c34d0977c855c659b1cb56f7e/MTS-V4-rally-overview-hero-1600x1000-1.jpg`
2. `https://images.ctfassets.net/x7j9qwvpvr5s/3EVUy9K4e64kFLGORnK068/e6fc6ebd4128f7ad9630b37cd5041e6b/MTS-V4-rally-overview-hero-1600x1000-02.jpg`

### Additional Images (28)
3-30. See `final_extraction.py` for complete list

## 📝 Content Sections Extracted

### Main Content
1. **"Designed to take you anywhere"** - Multistrada V4 Rally is your definitive travel companion, taking you on a journey to unexplored lands, with a focus on comfort and versatility. A 30-litre tank, long-trav...

2. **"At ease on any road"** - Make room for exploration with Multistrada V4 Rally, designed to travel any road comfortably and safely. Easy to use, every riding experience becomes natural and immediate. Whether...

3. **"On and off-road: the road to Olympus"** - Five days, almost 3000 kilometres. An epic trip aboard Multistrada V4 Rally, for those who never tire of long distances, bends, and dust. Ducati Product Sponsor, A...

4. **"Choose the right Multistrada for you"** - Your riding style comes first. Compare models in the Multistrada range to find the motorcycle that best suits your needs.

### Tooltip Content
**Hotspot 1 - DVO System:**
"New Ducati Vehicle Observer (DVO) system Derived from the Panigale V4, Ducati Vehicle Observer raises the Multistrada V4 Rally to a new level of safety and efficiency with electronic controls that ac..."

## 🖼️ Image Download

To download all images, use the script:
```bash
python final_extraction.py
```

Or use the ImageDownloader class directly:
```python
from src.downloaders.image_downloader import ImageDownloader
import aiohttp
import asyncio

async def download_all():
    downloader = ImageDownloader(base_output_dir="images")
    async with aiohttp.ClientSession() as session:
        for idx, url in enumerate(IMAGE_URLS):
            path = await downloader.download_image(
                url=url,
                manufacturer="Ducati",
                model="Multistrada V4 Rally",
                year=2024,
                index=idx,
                session=session
            )
            print(f"Downloaded: {path}")

asyncio.run(download_all())
```

## 📊 Summary

- **Total Images**: 30
- **Video Posters**: 2
- **Gallery Images**: 28
- **Content Sections**: 4+
- **Tooltips**: 1+ (DVO system)
- **Specifications**: Power, Torque, Weight, Displacement
- **Features**: 5+
- **Colors**: Ducati Red, Jade Green

All extraction scripts are ready in:
- `final_extraction.py` - Complete extraction with image download
- `extract_and_download_complete.py` - Full extraction script
- `extract_all_data.py` - Data extraction only


