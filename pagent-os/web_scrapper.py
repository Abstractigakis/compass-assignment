"""
WebScrapper: A minimalist web scraping class focused on fetching pages with Playwright.

This is a lightweight version of Pagent that only supports fetching pages without
any file system operations or database functionality.
"""

import asyncio
import logging
import random
import time
from typing import Dict, Optional
from urllib.parse import urljoin, urlparse

from fake_useragent import UserAgent

try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class WebScrapper:
    """
    A minimalist web scraper focused on fetching pages with Playwright.

    This class provides basic web scraping functionality without file system
    operations or database storage. Perfect for in-memory web scraping tasks.
    """

    def __init__(self, url: str, log_level: int = logging.INFO, **kwargs):
        """
        Initialize the WebScrapper and automatically fetch the page.

        Args:
            url: URL to fetch automatically upon initialization
            log_level: Logging level (default: logging.INFO)
            **kwargs: Additional arguments for fetch_page (browser_type, headless, etc.)
        """
        # Parse URL to get base_url
        from urllib.parse import urlparse

        parsed = urlparse(url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        self.url = url
        self.html = None  # Store the fetched HTML content

        # Set up logging
        self.logger = logging.getLogger(f"WebScrapper-{id(self)}")
        self.logger.setLevel(log_level)

        # Create console handler if none exists
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # Log Playwright availability
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.warning(
                "Playwright not available. Install with: pip install playwright && playwright install"
            )

        # User agent rotation
        self.ua = UserAgent()

        # Default headers
        self.default_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }

        # Automatically fetch the page
        self.fetch_page(url, **kwargs)

    def _get_headers(self, custom_headers: Optional[Dict] = None) -> Dict:
        """Generate headers with random user agent."""
        headers = self.default_headers.copy()
        headers["User-Agent"] = self.ua.random

        if custom_headers:
            headers.update(custom_headers)

        return headers

    def _resolve_url(self, url: str) -> str:
        """Resolve relative URLs to absolute URLs."""
        if url.startswith(("http://", "https://")):
            return url
        return urljoin(self.base_url, url)

    async def _fetch_with_playwright(
        self,
        url: str,
        browser_type: str = "firefox",
        headless: bool = True,
        wait_until: str = "networkidle",
        timeout: int = 60000,
        **kwargs,
    ) -> Dict:
        """
        Fetch page using Playwright for JavaScript-heavy sites with anti-detection.

        Args:
            url: URL to fetch
            browser_type: Browser to use (chromium, firefox, webkit)
            headless: Whether to run browser in headless mode
            wait_until: When to consider page loaded
            timeout: Page load timeout in milliseconds
            **kwargs: Additional arguments (ignored for compatibility)

        Returns:
            Dict with response data and metadata
        """
        if not PLAYWRIGHT_AVAILABLE:
            return {
                "url": url,
                "method": "playwright",
                "success": False,
                "error": "Playwright not available",
                "content": None,
            }

        url = self._resolve_url(url)

        try:
            self.logger.info(f"Fetching with Playwright: {url}")
            async with async_playwright() as p:
                # Configure browser with optimized settings for better compatibility
                browser_args = []
                if browser_type == "chromium":
                    browser_args = [
                        "--no-first-run",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-web-security",
                        "--ignore-certificate-errors",
                        "--ignore-ssl-errors",
                        "--disable-http2",
                    ]
                    browser = await p.chromium.launch(
                        headless=headless, args=browser_args
                    )
                elif browser_type == "webkit":
                    browser = await p.webkit.launch(headless=headless)
                else:  # firefox
                    browser = await p.firefox.launch(headless=headless)

                # Create context with reasonable settings
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                )

                page = await context.new_page()

                # Additional anti-detection JavaScript (conservative)
                if browser_type == "chromium":
                    await page.add_init_script("""
                        // Remove webdriver property
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined,
                        });
                    """)

                # Set additional headers
                headers = self._get_headers()
                await page.set_extra_http_headers(headers)

                try:
                    # Navigate to the page
                    await page.goto(url, timeout=timeout, wait_until=wait_until)

                    # Wait a bit more for any JavaScript challenges
                    try:
                        await page.wait_for_timeout(2000)
                    except:
                        pass

                    content = await page.content()

                    result = {
                        "url": url,
                        "method": "playwright",
                        "browser_type": browser_type,
                        "content": content,
                        "success": True,
                        "error": None,
                    }

                    return result

                finally:
                    await context.close()
                    await browser.close()

        except Exception as e:
            self.logger.error(f"Error fetching with Playwright: {e}")
            return {
                "url": url,
                "method": "playwright",
                "success": False,
                "error": str(e),
                "content": None,
            }

    def fetch_page(
        self,
        url: str,
        browser_type: str = "firefox",
        headless: bool = True,
        wait_until: str = "networkidle",
        timeout: int = 60000,
        **kwargs,
    ) -> str:
        """
        Fetch a page using Playwright and return the HTML content.

        Args:
            url: URL to fetch
            browser_type: Browser to use (chromium, firefox, webkit)
            headless: Whether to run browser in headless mode
            wait_until: When to consider page loaded
            timeout: Page load timeout in milliseconds
            **kwargs: Additional arguments for playwright

        Returns:
            str: HTML content of the page, or None if failed
        """
        url = self._resolve_url(url)

        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, so we need to run the coroutine differently
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._fetch_with_playwright(
                            url,
                            browser_type=browser_type,
                            headless=headless,
                            wait_until=wait_until,
                            timeout=timeout,
                            **kwargs,
                        ),
                    )
                    result = future.result()
            except RuntimeError:
                # No running event loop, safe to use asyncio.run()
                result = asyncio.run(
                    self._fetch_with_playwright(
                        url,
                        browser_type=browser_type,
                        headless=headless,
                        wait_until=wait_until,
                        timeout=timeout,
                        **kwargs,
                    )
                )

            if result["success"]:
                # Store HTML content in self.html
                self.html = result["content"]
                return self.html
            else:
                self.logger.error(f"Failed to fetch page: {result['error']}")
                self.html = None
                return None

        except Exception as e:
            self.logger.error(f"Error in fetch_page: {e}")
            self.html = None
            return None

    def _set_log_level(self, log_level: int):
        """Set the logging level for the WebScrapper instance."""
        self.logger.setLevel(log_level)
        for handler in self.logger.handlers:
            handler.setLevel(log_level)


if __name__ == "__main__":
    # Example usage
    def main():
        # Create web scrapper - automatically fetches the page
        scrapper = WebScrapper("https://www.costco.ca/electronics.html")

        # HTML is automatically available after initialization
        if scrapper.html:
            with open("scrapper.html", "w", encoding="utf-8") as f:
                f.write(scrapper.html)
            print(f"Successfully fetched {len(scrapper.html)} characters")
            print(
                f"HTML content stored in scrapper.html: {len(scrapper.html)} characters"
            )
        else:
            print("Failed to fetch page")

    # Run example
    main()
