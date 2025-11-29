"""Storage utilities for teaching session data."""

import json
from pathlib import Path
from typing import Optional, List
import aiofiles
import logging

from .models import TeachingSessionData, Screenshot

logger = logging.getLogger(__name__)


class TeachingStorage:
    """Handles storage and retrieval of teaching session data."""
    
    def __init__(self, base_dir: Path):
        """Initialize storage with base directory.
        
        Args:
            base_dir: Base directory for teaching data (e.g., teaching_data/)
        """
        self.base_dir = Path(base_dir)
        self.sessions_dir = self.base_dir / "sessions"
        self.patterns_dir = self.base_dir / "patterns"
        
        # Create directories if they don't exist
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
    
    def get_session_dir(self, session_id: str) -> Path:
        """Get directory path for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Path to session directory
        """
        return self.sessions_dir / session_id
    
    def get_screenshots_dir(self, session_id: str) -> Path:
        """Get screenshots directory for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Path to screenshots directory
        """
        screenshots_dir = self.get_session_dir(session_id) / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        return screenshots_dir
    
    async def save_session_data(self, session_data: TeachingSessionData) -> None:
        """Save session data to disk.
        
        Args:
            session_data: Complete session data to save
        """
        session_dir = self.get_session_dir(session_data.session.session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        
        data_file = session_dir / "session_data.json"
        
        # Convert to dict and serialize datetime
        data_dict = session_data.model_dump(mode="json")
        
        async with aiofiles.open(data_file, "w") as f:
            await f.write(json.dumps(data_dict, indent=2, default=str))
        
        logger.info(f"Saved session data to {data_file}")
    
    async def load_session_data(self, session_id: str) -> Optional[TeachingSessionData]:
        """Load session data from disk.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data if found, None otherwise
        """
        data_file = self.get_session_dir(session_id) / "session_data.json"
        
        if not data_file.exists():
            logger.warning(f"Session data file not found: {data_file}")
            return None
        
        async with aiofiles.open(data_file, "r") as f:
            content = await f.read()
        
        data_dict = json.loads(content)
        return TeachingSessionData(**data_dict)
    
    def get_screenshot_path(self, session_id: str, screenshot_id: str, extension: str = "png") -> Path:
        """Get file path for a screenshot.
        
        Args:
            session_id: Session identifier
            screenshot_id: Screenshot identifier
            extension: File extension (default: png)
            
        Returns:
            Path to screenshot file
        """
        screenshots_dir = self.get_screenshots_dir(session_id)
        return screenshots_dir / f"{screenshot_id}.{extension}"
    
    def list_sessions(self) -> List[str]:
        """List all session IDs.
        
        Returns:
            List of session IDs
        """
        if not self.sessions_dir.exists():
            return []
        
        return [
            d.name for d in self.sessions_dir.iterdir()
            if d.is_dir() and (d / "session_data.json").exists()
        ]


