"""Metadata writer for bike data."""
import json
from pathlib import Path
import aiofiles
from src.utils.schema import BikeDataWithMetadata
from src.utils.logging import get_logger

logger = get_logger(__name__)

class MetadataWriter:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)

    async def write_metadata(self, bike_data_with_meta: BikeDataWithMetadata) -> str:
        bike_data = bike_data_with_meta.bike_data
        folder = self.output_dir / bike_data.manufacturer / bike_data.model
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"{bike_data.manufacturer}_{bike_data.model}_{bike_data.year}_meta.json"
        filepath = folder / filename
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(bike_data_with_meta.model_dump_json(indent=2))
        logger.info(f"Created metadata: {filepath}")
        return str(filepath)
