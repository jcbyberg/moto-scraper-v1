"""Image downloader with SHA-256 deduplication and semantic naming."""
import hashlib
import re
from pathlib import Path
from typing import Optional, Set
import aiohttp
import aiofiles
from src.utils.logging import get_logger

logger = get_logger(__name__)

class ImageDownloader:
    def __init__(self, base_output_dir: str, max_size_mb: float = 10.0):
        self.base_output_dir = Path(base_output_dir)
        self.max_size_mb = max_size_mb
        self.image_hashes: Set[str] = set()

    async def download_image(
        self, url: str, manufacturer: str, model: str, year: int,
        index: int, session: aiohttp.ClientSession
    ) -> Optional[str]:
        try:
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    return None
                image_data = await response.read()
                image_hash = hashlib.sha256(image_data).hexdigest()
                if image_hash in self.image_hashes:
                    return None
                self.image_hashes.add(image_hash)
                ext = 'jpg'
                if '.png' in url.lower(): ext = 'png'
                elif '.webp' in url.lower(): ext = 'webp'
                safe_name = self._sanitize_filename(f"{manufacturer}_{model}_{year}")
                filename = f"{safe_name}_{index:03d}.{ext}"
                folder = self.base_output_dir / manufacturer / model / str(year)
                folder.mkdir(parents=True, exist_ok=True)
                filepath = folder / filename
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(image_data)
                return str(filepath.relative_to(self.base_output_dir))
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None

    def _sanitize_filename(self, text: str) -> str:
        return re.sub(r'[^\w\s-]', '', text).strip().replace(' ', '_')
