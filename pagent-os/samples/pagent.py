"""
Pagent: Your intelligent Page Agent for systematic web scraping.

The name "Pagent" is a play on "Page Agent" - representing an intelligent agent
that systematically fetches, processes, and stores web pages with extensible
callback functionality.

This module provides the core Pagent class for comprehensive web scraping with:
- Playwright-first fetching backend for full JavaScript support
- Systematic storage organization
- Extensible callback system for post-processing
- Comprehensive error handling and logging
"""

import asyncio
import json
import os
import time
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class Pagent:
    """
    Pagent: A comprehensive web scraping agent for systematic page fetching and HTML storage.

    The name "Pagent" is a play on "Page Agent" - your intelligent agent for systematic
    web page collection, processing, and storage with extensible callback functionality.

    Uses Playwright as the primary fetching method for full JavaScript support.

    Key Features:
    - Systematic storage: Each request gets its own timestamped folder
    - Callback system: Extensible post-processing with automatic file saving
    - Playwright-first: Full browser automation with JavaScript execution
    - Organized database: Configurable folder structure for all scraped data
    - Metadata tracking: Complete request history with timestamps and status
    """

    def __init__(
        self,
        base_url: str = "",
        db_folder: str = "scrapes",
        log_level: int = logging.INFO,
    ):
        """
        Initialize the Pagent (Page Agent).

        Args:
            base_url: Base URL for relative URL resolution
            db_folder: Database folder to save HTML files and metadata (default: "scrapes")
            log_level: Logging level (default: logging.INFO)

        The Pagent creates a systematic database structure under db_folder/page_requests/
        where each web page request gets its own timestamped folder containing:
        - page.html: The fetched HTML content
        - meta.json: Request metadata (URL, timestamp, status, etc.)
        - Additional files: Created by callbacks for processed data
        """
        self.base_url = base_url.rstrip("/")
        self.db_folder = Path(db_folder)
        self.db_folder.mkdir(parents=True, exist_ok=True)

        # Create page_requests subfolder for organized storage
        self.page_requests_dir = self.db_folder / "page_requests"
        self.page_requests_dir.mkdir(parents=True, exist_ok=True)

        # Set up logging
        self.logger = logging.getLogger(f"Pagent-{id(self)}")
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

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.default_headers)

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

    def _generate_request_folder_name(self, url: str) -> str:
        """Generate a systematic folder name from URL with timestamp."""
        parsed = urlparse(url)

        # Create a safe folder name from the URL
        domain = parsed.netloc.replace(".", "_")
        path = parsed.path.strip("/").replace("/", "_").replace(".", "_")

        # If path is empty, use index
        if not path:
            path = "index"

        # Add query parameters if they exist
        if parsed.query:
            query_safe = (
                parsed.query.replace("=", "_").replace("&", "_").replace("?", "_")
            )
            path = f"{path}_{query_safe}"

        # Add timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{domain}_{path}_{timestamp}"

        # Remove any remaining unsafe characters and ensure it's not too long
        folder_name = "".join(c for c in folder_name if c.isalnum() or c in "._-")

        # Truncate if too long
        if len(folder_name) > 200:
            # Keep the timestamp part (15 chars)
            name_part = folder_name[:-15]  # Remove _timestamp
            folder_name = name_part[:185] + folder_name[-15:]  # Add back _timestamp

        return folder_name

    def _save_html(
        self,
        html_content: str,
        url: str,
        method: str,
        custom_folder_name: Optional[str] = None,
    ) -> tuple[str, str]:
        """Save HTML content and metadata to organized page request folder.

        Returns:
            Tuple of (html_filepath, request_folder_path)
        """
        # Generate folder name for this page request
        if custom_folder_name:
            folder_name = custom_folder_name
        else:
            folder_name = self._generate_request_folder_name(url)

        # Create the page request folder
        request_folder = self.page_requests_dir / folder_name
        request_folder.mkdir(parents=True, exist_ok=True)

        # Save HTML content as page.html
        html_filepath = request_folder / "page.html"
        with open(html_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Create metadata for this request
        metadata = {
            "url": url,
            "folder_name": folder_name,
            "html_filepath": str(html_filepath.absolute()),
            "request_folder": str(request_folder.absolute()),
            "method": method,
            "timestamp": datetime.now().isoformat(),
            "content_length": len(html_content),
            "status": "success",
        }

        # Save metadata as meta.json in the same folder
        meta_filepath = request_folder / "meta.json"
        with open(meta_filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return str(html_filepath.absolute()), str(request_folder.absolute())

    def _add_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Add random delay between requests to be respectful."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def fetch_with_requests(
        self,
        url: str,
        custom_headers: Optional[Dict] = None,
        timeout: int = 30,
        save_html: bool = True,
        filename: Optional[str] = None,
    ) -> Dict:
        """
        Fetch page using standard requests library.

        Args:
            url: URL to fetch
            custom_headers: Additional headers to use
            timeout: Request timeout in seconds
            save_html: Whether to save HTML to file
            filename: Custom filename for saved HTML

        Returns:
            Dict with response data and metadata
        """
        url = self._resolve_url(url)
        headers = self._get_headers(custom_headers)

        try:
            self.logger.info(f"Fetching with requests: {url}")
            response = self.session.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            result = {
                "url": url,
                "method": "requests",
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text,
                "success": True,
                "error": None,
            }

            if save_html:
                filepath, request_folder = self._save_html(
                    response.text, url, "requests", filename
                )
                result["filepath"] = filepath
                result["request_folder"] = request_folder
                self.logger.info(f"Saved HTML to: {filepath}")

            return result

        except Exception as e:
            self.logger.error(f"Error fetching with requests: {e}")
            return {
                "url": url,
                "method": "requests",
                "success": False,
                "error": str(e),
                "content": None,
            }

    async def fetch_with_playwright(
        self,
        url: str,
        browser_type: str = "firefox",
        headless: bool = True,
        wait_until: str = "networkidle",
        timeout: int = 60000,
        save_html: bool = True,
        filename: Optional[str] = None,
        screenshot: bool = False,
    ) -> Dict:
        """
        Fetch page using Playwright for JavaScript-heavy sites with anti-detection.

        Args:
            url: URL to fetch
            browser_type: Browser to use (chromium, firefox, webkit)
            headless: Whether to run browser in headless mode
            wait_until: When to consider page loaded
            timeout: Page load timeout in milliseconds
            save_html: Whether to save HTML to file
            filename: Custom filename for saved HTML
            screenshot: Whether to take a screenshot

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
                    # Conservative arguments for better server compatibility
                    browser_args = [
                        "--no-first-run",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-web-security",
                        "--ignore-certificate-errors",
                        "--ignore-ssl-errors",
                        "--disable-http2",  # Disable HTTP/2 to avoid protocol errors
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
                        await page.wait_for_timeout(3000)  # 3 seconds
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

                    if save_html:
                        filepath, request_folder = self._save_html(
                            content, url, "playwright", filename
                        )
                        result["filepath"] = filepath
                        result["request_folder"] = request_folder
                        self.logger.info(f"Saved HTML to: {filepath}")

                    if screenshot:
                        # Save screenshot in the same request folder
                        if save_html:
                            # Use the same request folder
                            screenshot_path = Path(request_folder) / "screenshot.png"
                        else:
                            # Create a temporary request folder just for the screenshot
                            folder_name = self._generate_request_folder_name(url)
                            request_folder_path = self.page_requests_dir / folder_name
                            request_folder_path.mkdir(parents=True, exist_ok=True)
                            screenshot_path = request_folder_path / "screenshot.png"

                        await page.screenshot(path=screenshot_path)
                        result["screenshot_path"] = str(screenshot_path.absolute())
                        self.logger.info(f"Screenshot saved to: {screenshot_path}")

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
        method: str = "playwright",
        on_complete: Optional[callable] = None,
        **kwargs,
    ) -> Dict:
        """
        Fetch a page using the specified method, with Playwright as the default.

        Args:
            url: URL to fetch
            method: Fetching method ('requests', 'playwright', 'auto')
            on_complete: Optional callback function to run after successful fetch.
                        Function signature: on_complete(result_dict, request_folder_path)
                        where result_dict contains the fetch result and request_folder_path
                        is the Path object to the request folder for saving additional files.
            **kwargs: Additional arguments for specific methods

        Returns:
            Dict with response data and metadata
        """
        url = self._resolve_url(url)

        if method == "auto":
            # For auto mode, prefer Playwright first, then requests as fallback
            methods = (
                ["playwright", "requests"] if PLAYWRIGHT_AVAILABLE else ["requests"]
            )
        else:
            methods = [method]

        last_error = None

        for method_name in methods:
            try:
                if method_name == "requests":
                    result = self.fetch_with_requests(url, **kwargs)
                elif method_name == "playwright":
                    result = asyncio.run(self.fetch_with_playwright(url, **kwargs))
                else:
                    continue

                if result["success"]:
                    # Execute callback if provided and fetch was successful
                    if on_complete and callable(on_complete):
                        try:
                            # Get the request folder path from the result
                            request_folder = None
                            if result.get("filepath"):
                                # Extract folder path from the HTML file path
                                request_folder = Path(result["filepath"]).parent

                            # Call the callback with result and folder path
                            on_complete(result, request_folder)

                        except Exception as callback_error:
                            self.logger.warning(
                                f"Callback function failed: {callback_error}"
                            )
                            # Don't fail the entire request if callback fails

                    return result
                else:
                    last_error = result["error"]

            except Exception as e:
                last_error = str(e)
                continue

            # Add delay between method attempts
            self._add_delay(0.5, 1.0)

        return {
            "url": url,
            "method": method,
            "success": False,
            "error": f"All methods failed. Last error: {last_error}",
            "content": None,
        }

    def fetch_multiple_pages(
        self,
        urls: List[str],
        method: str = "auto",
        delay_range: tuple = (1.0, 3.0),
        **kwargs,
    ) -> List[Dict]:
        """
        Fetch multiple pages with delay between requests.

        Args:
            urls: List of URLs to fetch
            method: Fetching method to use
            delay_range: Min and max delay between requests
            **kwargs: Additional arguments for fetch methods

        Returns:
            List of result dictionaries
        """
        results = []

        for i, url in enumerate(urls):
            self.logger.info(f"Fetching page {i+1}/{len(urls)}: {url}")

            result = self.fetch_page(url, method=method, **kwargs)
            results.append(result)

            # Add delay between requests (except for last request)
            if i < len(urls) - 1:
                self._add_delay(delay_range[0], delay_range[1])

        return results

    def parse_html(
        self, html_content: str, parser: str = "html.parser"
    ) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup."""
        return BeautifulSoup(html_content, parser)

    def extract_links(
        self,
        html_content: str,
        base_url: Optional[str] = None,
        internal_only: bool = False,
    ) -> List[str]:
        """
        Extract all links from HTML content.

        Args:
            html_content: HTML content to parse
            base_url: Base URL for resolving relative links
            internal_only: Whether to return only internal links

        Returns:
            List of URLs
        """
        soup = self.parse_html(html_content)
        links = []

        base_url = base_url or self.base_url
        parsed_base = urlparse(base_url)

        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Resolve relative URLs
            if not href.startswith(("http://", "https://")):
                if base_url:
                    href = urljoin(base_url, href)
                else:
                    continue

            # Filter internal links only if requested
            if internal_only:
                parsed_href = urlparse(href)
                if parsed_href.netloc != parsed_base.netloc:
                    continue

            links.append(href)

        return list(set(links))  # Remove duplicates

    def get_stats(self) -> Dict:
        """Get statistics about fetched pages by scanning the page_requests directory."""
        if not self.page_requests_dir.exists():
            return {"total_pages": 0}

        # Scan page_requests directory for folders
        request_folders = [d for d in self.page_requests_dir.iterdir() if d.is_dir()]

        if not request_folders:
            return {"total_pages": 0}

        total = len(request_folders)
        successful = 0
        methods = {}

        # Read metadata from each request folder
        for folder in request_folders:
            meta_file = folder / "meta.json"
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)

                    if metadata.get("status") == "success":
                        successful += 1

                    method = metadata.get("method", "unknown")
                    methods[method] = methods.get(method, 0) + 1
                except:
                    # Skip if metadata file is corrupted
                    continue

        return {
            "total_pages": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0,
            "methods_used": methods,
            "db_folder": str(self.db_folder.absolute()),
            "page_requests_directory": str(self.page_requests_dir.absolute()),
        }

    def set_log_level(self, log_level: int):
        """Set the logging level for the Pagent instance."""
        self.logger.setLevel(log_level)
        for handler in self.logger.handlers:
            handler.setLevel(log_level)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


if __name__ == "__main__":
    # Example usage
    async def main():
        # Create page agent
        agent = Pagent(base_url="https://www.costco.ca", db_folder="scrapes")

        # Test single page fetch
        result = agent.fetch_page("https://www.costco.ca/electronics.html")

        if result["success"]:
            print(f"Successfully fetched page: {result['url']}")
            print(f"Content length: {len(result['content'])}")

            # Extract links
            links = agent.extract_links(result["content"], internal_only=True)
            print(f"Found {len(links)} internal links")

        # Print stats
        stats = agent.get_stats()
        print(f"Stats: {stats}")

    # Run example
    asyncio.run(main())
