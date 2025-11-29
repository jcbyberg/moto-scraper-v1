"""Markdown writer for bike data."""
import os
import re
from pathlib import Path
from typing import List
import aiofiles
from src.utils.schema import BikeData
from src.utils.logging import get_logger

logger = get_logger(__name__)

class MarkdownWriter:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def write_bike_markdown(
        self, bike_data: BikeData, image_paths: List[str]
    ) -> str:
        safe_name = self._sanitize_filename(f"{bike_data.manufacturer}_{bike_data.model}_{bike_data.year}")
        folder = self.output_dir / bike_data.manufacturer / bike_data.model
        folder.mkdir(parents=True, exist_ok=True)
        filepath = folder / f"{safe_name}.md"
        md_content = self._generate_markdown(bike_data, image_paths, filepath)
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(md_content)
        logger.info(f"Created markdown: {filepath}")
        return str(filepath)

    def _generate_markdown(self, bike_data: BikeData, image_paths: List[str], md_file: Path) -> str:
        lines = [f"# {bike_data.manufacturer} {bike_data.model} ({bike_data.year})\n"]
        if bike_data.description:
            lines.append("## Overview\n")
            lines.append(f"{bike_data.description}\n")
        
        # Add structured content sections if available
        if bike_data.content_sections:
            lines.append("\n## Content Sections\n")
            if bike_data.content_sections.get('header'):
                lines.append(f"### Header\n{bike_data.content_sections['header']}\n")
            if bike_data.content_sections.get('title'):
                lines.append(f"### Title\n{bike_data.content_sections['title']}\n")
            if bike_data.content_sections.get('top'):
                lines.append(f"### Top\n{bike_data.content_sections['top']}\n")
            if bike_data.content_sections.get('text'):
                lines.append(f"### Text\n{bike_data.content_sections['text']}\n")
            if bike_data.content_sections.get('content'):
                lines.append(f"### Content\n{bike_data.content_sections['content']}\n")
            if bike_data.content_sections.get('description'):
                lines.append(f"### Description\n{bike_data.content_sections['description']}\n")
            if bike_data.content_sections.get('tooltips'):
                lines.append(f"### Tooltips\n{bike_data.content_sections['tooltips']}\n")
            if bike_data.content_sections.get('tabs'):
                lines.append("\n### Insights Tabs\n")
                tabs = bike_data.content_sections['tabs']
                if isinstance(tabs, dict):
                    for tab_name, tab_content in tabs.items():
                        lines.append(f"#### {tab_name}\n")
                        if isinstance(tab_content, dict):
                            if tab_content.get('content'):
                                lines.append(f"{tab_content['content']}\n")
                            if tab_content.get('text'):
                                lines.append(f"{tab_content['text']}\n")
                        else:
                            lines.append(f"{tab_content}\n")
                else:
                    lines.append(f"{tabs}\n")
            if bike_data.content_sections.get('story'):
                lines.append("\n### Story Content\n")
                if bike_data.content_sections.get('story_title'):
                    lines.append(f"**{bike_data.content_sections['story_title']}**\n")
                if bike_data.content_sections.get('story_intro'):
                    lines.append(f"{bike_data.content_sections['story_intro']}\n\n")
                lines.append(f"{bike_data.content_sections['story']}\n")
            if bike_data.content_sections.get('disclaimer'):
                lines.append(f"\n### Disclaimer\n{bike_data.content_sections['disclaimer']}\n")
        if bike_data.specifications:
            lines.append("## Specifications\n")
            if bike_data.specifications.engine and any(getattr(bike_data.specifications.engine, f) for f in bike_data.specifications.engine.model_fields.keys()):
                lines.append("### Engine")
                for field, value in bike_data.specifications.engine.model_dump().items():
                    if value: lines.append(f"- **{field.replace('_', ' ').title()}**: {value}")
            if bike_data.specifications.dimensions and any(getattr(bike_data.specifications.dimensions, f) for f in bike_data.specifications.dimensions.model_fields.keys()):
                lines.append("\n### Dimensions")
                for field, value in bike_data.specifications.dimensions.model_dump().items():
                    if value: lines.append(f"- **{field.replace('_', ' ').title()}**: {value}")
        if bike_data.features:
            lines.append("\n## Features\n")
            for feature in bike_data.features[:20]:
                lines.append(f"- {feature}")
        if image_paths:
            lines.append("\n## Images\n")
            for img_path in image_paths[:10]:
                rel_path = os.path.relpath(self.output_dir / img_path, md_file.parent)
                lines.append(f"![Image]({rel_path})")
        lines.append(f"\n## Source\n- **URLs**: {', '.join(bike_data.source_urls[:3])}")
        lines.append(f"- **Extracted**: {bike_data.extraction_timestamp.isoformat()}\n")
        return "\n".join(lines)

    def _sanitize_filename(self, text: str) -> str:
        return re.sub(r'[^\w\s-]', '', text).strip().replace(' ', '_')
