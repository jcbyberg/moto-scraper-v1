"""
Cookie consent and JavaScript interaction handler for Playwright crawler.
Handles common UI elements like cookie banners, dropdowns, and modals.
"""

from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
import logging

logger = logging.getLogger(__name__)


class CookieHandler:
    """Handle cookie consent dialogs and other common UI blockers."""
    
    # Common cookie consent button selectors
    COOKIE_BUTTON_SELECTORS = [
        "#onetrust-accept-btn-handler",  # OneTrust
        "#accept-cookies",
        "#cookie-accept",
        "button:has-text('Accept')",
        "button:has-text('Accept All')",
        "button:has-text('Accept Cookies')",
        "button:has-text('I Accept')",
        ".cookie-accept",
        ".accept-cookies",
        "[data-cookie-accept]",
        "[id*='accept'][id*='cookie']",
        "[class*='accept'][class*='cookie']",
    ]
    
    def __init__(self, page: Page, timeout: int = 5000):
        """
        Initialize cookie handler.
        
        Args:
            page: Playwright page object
            timeout: Timeout in milliseconds for waiting for elements
        """
        self.page = page
        self.timeout = timeout
    
    async def accept_cookies(
        self,
        custom_selector: Optional[str] = None,
        wait_after: float = 1.0
    ) -> bool:
        """
        Attempt to accept cookies using common selectors or custom selector.
        
        Args:
            custom_selector: Optional custom CSS selector for cookie button
            wait_after: Seconds to wait after clicking (for animations)
            
        Returns:
            True if cookie button was found and clicked, False otherwise
        """
        selectors = [custom_selector] if custom_selector else []
        selectors.extend(self.COOKIE_BUTTON_SELECTORS)
        
        for selector in selectors:
            try:
                # Wait for button to be visible
                button = await self.page.wait_for_selector(
                    selector,
                    state="visible",
                    timeout=self.timeout
                )
                
                if button:
                    await button.click()
                    logger.info(f"Clicked cookie consent button: {selector}")
                    
                    # Wait for any animations/transitions
                    await self.page.wait_for_timeout(int(wait_after * 1000))
                    return True
                    
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        logger.debug("No cookie consent button found")
        return False
    
    async def dismiss_modals(self) -> None:
        """Attempt to dismiss any modals or overlays that might block content."""
        # Common modal close selectors
        close_selectors = [
            ".modal-close",
            ".close-modal",
            "[data-dismiss='modal']",
            "button.close",
            ".overlay-close",
        ]
        
        for selector in close_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    await element.click()
                    logger.info(f"Dismissed modal: {selector}")
                    await self.page.wait_for_timeout(500)
            except Exception as e:
                logger.debug(f"Error dismissing modal {selector}: {e}")


class NavigationHandler:
    """Handle JavaScript-based navigation like dropdowns and menus."""
    
    def __init__(self, page: Page):
        """Initialize navigation handler."""
        self.page = page
    
    async def click_dropdown(
        self,
        selector: str,
        wait_for_visible: bool = True,
        timeout: int = 5000
    ) -> bool:
        """
        Click a dropdown/menu trigger and wait for it to open.
        
        Args:
            selector: CSS selector for dropdown trigger
            wait_for_visible: Whether to wait for dropdown content to become visible
            timeout: Timeout in milliseconds
            
        Returns:
            True if dropdown was clicked successfully
        """
        try:
            element = await self.page.wait_for_selector(
                selector,
                state="visible",
                timeout=timeout
            )
            
            if element:
                await element.click()
                logger.info(f"Clicked dropdown: {selector}")
                
                if wait_for_visible:
                    # Wait a bit for dropdown to open
                    await self.page.wait_for_timeout(500)
                
                return True
                
        except PlaywrightTimeoutError:
            logger.warning(f"Dropdown not found: {selector}")
            return False
        except Exception as e:
            logger.error(f"Error clicking dropdown {selector}: {e}")
            return False
    
    async def select_dropdown_option(
        self,
        dropdown_selector: str,
        option_selector: Optional[str] = None,
        option_index: Optional[int] = None,
        option_text: Optional[str] = None
    ) -> bool:
        """
        Select an option from a dropdown menu.
        
        Args:
            dropdown_selector: Selector for dropdown trigger
            option_selector: CSS selector for specific option
            option_index: Index of option to select (0-based)
            option_text: Text content of option to select
            
        Returns:
            True if option was selected successfully
        """
        # First, open the dropdown
        if not await self.click_dropdown(dropdown_selector):
            return False
        
        try:
            # Wait for dropdown options to appear
            await self.page.wait_for_timeout(300)
            
            # Select by specific selector
            if option_selector:
                option = await self.page.query_selector(option_selector)
                if option:
                    await option.click()
                    logger.info(f"Selected dropdown option: {option_selector}")
                    return True
            
            # Select by index
            elif option_index is not None:
                options = await self.page.query_selector_all(
                    f"{dropdown_selector} + * a, "
                    f"{dropdown_selector} + * [role='menuitem'], "
                    f".dropdown-menu a, "
                    f"[role='menu'] a"
                )
                if options and option_index < len(options):
                    await options[option_index].click()
                    logger.info(f"Selected dropdown option at index {option_index}")
                    return True
            
            # Select by text
            elif option_text:
                # Try various patterns
                text_selectors = [
                    f"a:has-text('{option_text}')",
                    f"[role='menuitem']:has-text('{option_text}')",
                    f"li:has-text('{option_text}') a",
                ]
                
                for selector in text_selectors:
                    try:
                        option = await self.page.wait_for_selector(
                            selector,
                            timeout=2000
                        )
                        if option:
                            await option.click()
                            logger.info(f"Selected dropdown option by text: {option_text}")
                            return True
                    except PlaywrightTimeoutError:
                        continue
            
            logger.warning("Could not find dropdown option")
            return False
            
        except Exception as e:
            logger.error(f"Error selecting dropdown option: {e}")
            return False
    
    async def wait_for_navigation(
        self,
        timeout: int = 10000,
        wait_until: str = "domcontentloaded"
    ) -> None:
        """Wait for page navigation to complete."""
        try:
            await self.page.wait_for_load_state(wait_until, timeout=timeout)
        except Exception as e:
            logger.debug(f"Navigation wait completed or timed out: {e}")


