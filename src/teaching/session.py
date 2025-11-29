"""Teaching session management."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

from playwright.async_api import Browser, BrowserContext, Page
from .models import TeachingSession, SessionStatus
from .storage import TeachingStorage

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages teaching session lifecycle."""
    
    def __init__(self, storage: TeachingStorage):
        """Initialize session manager.
        
        Args:
            storage: Storage instance for session data
        """
        self.storage = storage
        self.current_session: Optional[TeachingSession] = None
    
    def create_session(
        self,
        target_url: str,
        session_name: Optional[str] = None,
        browser_info: Optional[dict] = None
    ) -> TeachingSession:
        """Create a new teaching session.
        
        Args:
            target_url: Target URL to teach navigation for
            session_name: Optional name for the session
            browser_info: Optional browser information dict
            
        Returns:
            Created teaching session
        """
        session_id = str(uuid.uuid4())
        
        session = TeachingSession(
            session_id=session_id,
            target_url=target_url,
            status=SessionStatus.RECORDING,
            started_at=datetime.now(),
            browser_info=browser_info or {},
            notes=session_name
        )
        
        self.current_session = session
        logger.info(f"Created new teaching session: {session_id} for {target_url}")
        
        return session
    
    async def load_session(self, session_id: str) -> Optional[TeachingSession]:
        """Load a session by ID (async).
        
        Args:
            session_id: Session identifier
            
        Returns:
            Teaching session if found, None otherwise
        """
        # Load from storage
        session_data = await self.storage.load_session_data(session_id)
        if session_data:
            self.current_session = session_data.session
            return session_data.session
        
        logger.warning(f"Session not found: {session_id}")
        return None
    
    def update_session_status(self, status: SessionStatus) -> None:
        """Update current session status.
        
        Args:
            status: New status
        """
        if not self.current_session:
            raise ValueError("No active session")
        
        self.current_session.status = status
        if status == SessionStatus.COMPLETED:
            self.current_session.completed_at = datetime.now()
        
        logger.info(f"Updated session {self.current_session.session_id} status to {status}")
    
    def update_interaction_count(self, count: int) -> None:
        """Update interaction count for current session.
        
        Args:
            count: New interaction count
        """
        if not self.current_session:
            raise ValueError("No active session")
        
        self.current_session.interaction_count = count
    
    def update_screenshot_count(self, count: int) -> None:
        """Update screenshot count for current session.
        
        Args:
            count: New screenshot count
        """
        if not self.current_session:
            raise ValueError("No active session")
        
        self.current_session.screenshot_count = count
    
    def get_current_session(self) -> Optional[TeachingSession]:
        """Get current active session.
        
        Returns:
            Current session or None
        """
        return self.current_session

