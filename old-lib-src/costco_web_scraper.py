#!/usr/bin/env python3
"""
Costco Web Scraper - A wrapper around Pagent for Costco-specific scraping.
Handles category discovery, product listing, and systematic data storage.
Features AI-powered neuromorphic ETL for intelligent HTML structure discovery.
"""

import json
import time
import random
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from pagent import Pagent

# Import the common category interface
try:
    from category_interface import (
        create_category_extraction_prompt,
        validate_category_output,
        CategoryType,
    )

    CATEGORY_INTERFACE_AVAILABLE = True
except ImportError:
    CATEGORY_INTERFACE_AVAILABLE = False
    print(
        "⚠️ Category interface not available. Categories may have inconsistent structure."
    )

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️ python-dotenv not installed. Environment variables must be set manually.")
    print("Install with: pip install python-dotenv")

# AI-powered imports
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. AI features will be disabled.")
    print("Install with: pip install google-generativeai")


class CostcoWebScraper:
    """
    A web scraper specifically designed for Costco.ca that wraps around Pagent
    for systematic page fetching and organized data storage.
    """

    def __init__(self, db_folder: str = "db", gemini_api_key: str = None):
        """
        Initialize the Costco web scraper.

        Args:
            db_folder: Database folder for storing all scraped data (default: db)
            gemini_api_key: Google Gemini API key for AI-powered extraction
        """
        self.base_url = "https://www.costco.ca"
        self.sitemap_url = "https://www.costco.ca/SiteMapDisplayView"

        # Initialize Pagent for systematic page fetching
        self.pagent = Pagent(base_url=self.base_url, db_folder=db_folder)

        # Categories storage
        self.categories = []
        self.categories_loaded = False

        # AI-powered extraction setup
        self.ai_enabled = GEMINI_AVAILABLE and gemini_api_key
        if self.ai_enabled:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            self.pagent.logger.info("🤖 AI-powered extraction enabled with Gemini")
        elif gemini_api_key and not GEMINI_AVAILABLE:
            self.pagent.logger.warning(
                "⚠️ Gemini API key provided but google-generativeai not installed"
            )
        else:
            self.pagent.logger.info("🔧 Using traditional extraction methods")

    def fetch_sitemap(self) -> Dict:
        """
        Fetch the Costco sitemap page using standard page request strategy.

        Returns:
            Dict with fetch result including success status and content
        """
        self.pagent.logger.info("Fetching Costco sitemap...")

        # Use standard timestamped folder name like all other page requests
        folder_name = f"sitemap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        result = self.pagent.fetch_page(
            self.sitemap_url, method="auto", filename=folder_name
        )

        if result["success"]:
            self.pagent.logger.info(
                f"Sitemap fetched successfully: {len(result['content'])} characters"
            )
        else:
            self.pagent.logger.error(f"Failed to fetch sitemap: {result['error']}")

        return result

    def parse_categories(self, html_content: str) -> List[Dict]:
        """
        Parse categories from the sitemap HTML content.

        Args:
            html_content: HTML content of the sitemap page

        Returns:
            List of category dictionaries with name, href, and children
        """
        soup = BeautifulSoup(html_content, "html.parser")
        categories = []

        self.pagent.logger.info("Parsing categories from sitemap...")

        # Find the main navigation structure
        # Look for common Costco sitemap patterns
        category_sections = soup.find_all(
            ["div", "section"],
            class_=lambda x: x
            and any(
                term in x.lower()
                for term in ["category", "department", "section", "nav"]
            ),
        )

        if not category_sections:
            # Fallback: look for any structured lists with links
            category_sections = soup.find_all(["ul", "ol"])

        for section in category_sections:
            section_categories = self._parse_category_section(section)
            if section_categories:
                categories.extend(section_categories)

        # Remove duplicates based on href
        seen_hrefs = set()
        unique_categories = []
        for cat in categories:
            if cat["href"] not in seen_hrefs:
                seen_hrefs.add(cat["href"])
                unique_categories.append(cat)

        self.pagent.logger.info(f"Found {len(unique_categories)} unique categories")
        return unique_categories

    def _parse_category_section(self, section) -> List[Dict]:
        """Parse a single section for categories."""
        categories = []

        # Find all links in this section
        links = section.find_all("a", href=True)

        for link in links:
            href = link.get("href", "").strip()
            name = link.get_text(strip=True)

            # Filter out non-category links
            if not href or not name:
                continue

            # Skip unwanted links (footer, help, etc.)
            if any(
                skip in href.lower()
                for skip in [
                    "javascript:",
                    "mailto:",
                    "#",
                    "help",
                    "contact",
                    "about",
                    "privacy",
                    "terms",
                    "sitemap",
                    "search",
                ]
            ):
                continue

            # Skip very short names that are likely not categories
            if len(name) < 3:
                continue

            # Ensure href is relative or absolute Costco URL
            if href.startswith("/"):
                href = href
            elif href.startswith("http") and "costco.ca" not in href:
                continue
            elif not href.startswith("http"):
                href = "/" + href.lstrip("/")

            category = {
                "name": name,
                "href": href,
                "children": [],
                "is_leaf": None,  # Will be determined later
                "leaf_status": "unknown",  # "leaf", "non-leaf", or "unknown"
                "is_leaf_determined": False,
            }

            # Look for subcategories in the same area
            parent_element = link.find_parent(["li", "div"])
            if parent_element:
                subcategory_links = parent_element.find_all("a", href=True)
                for sublink in subcategory_links:
                    if sublink == link:  # Skip the parent link
                        continue
                    sub_href = sublink.get("href", "").strip()
                    sub_name = sublink.get_text(strip=True)

                    if sub_href and sub_name and len(sub_name) > 2:
                        if sub_href.startswith("/"):
                            pass  # already relative
                        elif not sub_href.startswith("http"):
                            sub_href = "/" + sub_href.lstrip("/")

                        category["children"].append(
                            {
                                "name": sub_name,
                                "href": sub_href,
                                "children": [],
                                "is_leaf": None,
                                "leaf_status": "unknown",
                                "is_leaf_determined": False,
                            }
                        )

            categories.append(category)

        return categories

    def get_categories(self, use_cache: bool = True) -> List[Dict]:
        """
        Get the list of categories from Costco using page request strategy.

        Args:
            use_cache: Whether to use cached categories if available

        Returns:
            List of category dictionaries
        """
        if self.categories_loaded and use_cache:
            return self.categories

        # Check if we have a cached categories file in the latest sitemap request folder
        if use_cache:
            cached_categories = self._load_cached_categories()
            if cached_categories:
                self.categories = cached_categories
                self.categories_loaded = True
                return self.categories

        # Fetch fresh sitemap using page request strategy
        sitemap_result = self.fetch_sitemap()

        if not sitemap_result["success"]:
            raise Exception(f"Failed to fetch sitemap: {sitemap_result['error']}")

        # Parse categories
        self.categories = self.parse_categories(sitemap_result["content"])

        # Mark H2 categories as non-leaf as per requirements
        self.mark_h2_categories_as_non_leaf()

        # Save categories to the same request folder where sitemap was saved
        if sitemap_result.get("request_folder"):
            self._save_categories_to_request_folder(sitemap_result["request_folder"])

        self.categories_loaded = True
        return self.categories

    def get_category_by_name(self, category_name: str) -> Optional[Dict]:
        """
        Find a category by name.

        Args:
            category_name: Name of the category to find

        Returns:
            Category dictionary if found, None otherwise
        """
        if not self.categories_loaded:
            self.get_categories()

        def search_categories(categories, name):
            for category in categories:
                if category["name"].lower() == name.lower():
                    return category
                if category.get("children"):
                    found = search_categories(category["children"], name)
                    if found:
                        return found
            return None

        return search_categories(self.categories, category_name)

    def fetch_category_page(self, category_name: str, **kwargs) -> Dict:
        """
        Fetch a category page by category name.

        Args:
            category_name: Name of the category to fetch
            **kwargs: Additional arguments for pagent.fetch_page

        Returns:
            Dict with fetch result
        """
        category = self.get_category_by_name(category_name)
        if not category:
            raise ValueError(f"Category '{category_name}' not found")

        category_url = urljoin(self.base_url, category["href"])

        # Generate folder name for this category fetch
        safe_name = category_name.lower().replace(" ", "_").replace("&", "and")
        folder_name = f"category_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.pagent.logger.info(
            f"Fetching category page: {category_name} -> {category_url}"
        )

        result = self.pagent.fetch_page(category_url, filename=folder_name, **kwargs)

        # If fetch was successful, analyze if this is a leaf page
        if result.get("success") and result.get("content"):
            is_leaf_page = self.is_leaf(result["content"])
            result["is_leaf"] = is_leaf_page

            self.pagent.logger.info(
                f"Category page analysis: {'LEAF' if is_leaf_page else 'NON-LEAF'} page detected"
            )

            # Add leaf status to the result for downstream processing
            if is_leaf_page:
                self.pagent.logger.info("This appears to be a product listing page")
            else:
                self.pagent.logger.info("This appears to be a category navigation page")

        return result

    def ai_extract_products_neuromorphic(self, html_content: str) -> List[Dict]:
        """
        AI-powered neuromorphic ETL for product extraction.
        Uses Gemini to intelligently discover HTML structure and extract products.

        Args:
            html_content: Raw HTML content to analyze

        Returns:
            List of extracted product dictionaries
        """
        if not self.ai_enabled:
            self.pagent.logger.warning(
                "🚫 AI extraction not available, falling back to traditional methods"
            )
            return self.parse_products(html_content)

        self.pagent.logger.info(
            "🤖 Starting AI-powered neuromorphic product extraction..."
        )

        try:
            # Step 1: Preprocess HTML for AI analysis
            cleaned_html = self._preprocess_html_for_ai(html_content)

            # Step 2: AI structure discovery
            structure_analysis = self._ai_discover_structure(cleaned_html)

            # Step 3: AI product extraction
            products = self._ai_extract_products(cleaned_html, structure_analysis)

            self.pagent.logger.info(f"🎯 AI extracted {len(products)} products")
            return products

        except Exception as e:
            self.pagent.logger.error(f"💥 AI extraction failed: {e}")
            self.pagent.logger.info("🔄 Falling back to traditional extraction...")
            return self.parse_products(html_content)

    def _preprocess_html_for_ai(self, html_content: str) -> str:
        """
        Preprocess HTML to make it more suitable for AI analysis.
        Removes noise and focuses on content-rich sections.
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script, style, and other noise elements
        for element in soup(["script", "style", "noscript", "meta", "link"]):
            element.decompose()

        # Remove comments
        from bs4 import Comment

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Focus on main content areas
        main_content_selectors = [
            "main",
            ".main",
            "#main",
            ".content",
            "#content",
            ".products",
            ".product-list",
            ".product-grid",
            ".search-results",
            ".catalog",
            "section",
            "article",
        ]

        main_content = None
        for selector in main_content_selectors:
            element = soup.select_one(selector)
            if element:
                main_content = element
                break

        # If no main content found, use body
        if not main_content:
            main_content = soup.find("body") or soup

        # Return cleaned HTML limited to reasonable size for AI
        cleaned = str(main_content)
        if len(cleaned) > 50000:  # Limit to 50KB for AI processing
            # Try to find product containers and limit to those
            product_containers = main_content.find_all(
                attrs={
                    "class": lambda x: x
                    and any(
                        term in str(x).lower()
                        for term in ["product", "item", "tile", "card"]
                    )
                }
            )[:20]  # Limit to first 20 product containers

            if product_containers:
                # Create a focused HTML with just product containers
                focused_soup = BeautifulSoup("<div></div>", "html.parser")
                for container in product_containers:
                    focused_soup.div.append(container.extract())
                cleaned = str(focused_soup)

        return cleaned[:50000]  # Final safety limit

    def _ai_discover_structure(self, html_content: str) -> Dict:
        """
        Use AI to discover the structure of the HTML and identify product patterns.
        """
        prompt = (
            """
You are an expert HTML structure analyzer. Analyze this HTML page and identify:

1. Is this a product listing page? (Yes/No)
2. What are the main product container patterns? (CSS selectors or element descriptions)
3. What product information is available? (name, price, image, url, etc.)
4. How are products organized in the HTML structure?

Please respond in JSON format:
{
    "is_product_page": boolean,
    "product_container_patterns": ["selector1", "selector2"],
    "available_data_fields": ["name", "price", "image", "url"],
    "structure_notes": "description of how products are organized"
}

HTML to analyze:
"""
            + html_content
        )

        try:
            response = self.gemini_model.generate_content(prompt)

            # Try to extract JSON from response
            response_text = response.text
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

            if json_match:
                structure_data = json.loads(json_match.group())
                self.pagent.logger.debug(f"🔍 AI Structure Analysis: {structure_data}")
                return structure_data
            else:
                self.pagent.logger.warning("⚠️ AI response not in expected JSON format")
                return {
                    "is_product_page": False,
                    "product_container_patterns": [],
                    "available_data_fields": [],
                }

        except Exception as e:
            self.pagent.logger.error(f"💥 AI structure discovery failed: {e}")
            return {
                "is_product_page": False,
                "product_container_patterns": [],
                "available_data_fields": [],
            }

    def _ai_extract_products(
        self, html_content: str, structure_analysis: Dict
    ) -> List[Dict]:
        """
        Use AI to extract actual product data based on the discovered structure.
        """
        if not structure_analysis.get("is_product_page", False):
            self.pagent.logger.info("🚫 AI determined this is not a product page")
            return []

        prompt = (
            f"""
You are an expert product data extractor. Based on the structure analysis, extract ALL products from this HTML.

Structure Analysis:
{json.dumps(structure_analysis, indent=2)}

Please extract products and return them in this JSON format:
[
    {{
        "name": "Product Name",
        "price": "$X.XX",
        "url": "relative or absolute URL",
        "image_url": "image URL",
        "product_id": "ID if available",
        "description": "short description if available"
    }}
]

Rules:
1. Extract ALL products found on the page
2. Use relative URLs for Costco.ca links
3. Include price with currency symbol if available
4. Set fields to null if not found
5. Focus on actual products, not navigation items

HTML to extract from:
"""
            + html_content
        )

        try:
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text

            # Try to extract JSON array from response
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)

            if json_match:
                products_data = json.loads(json_match.group())

                # Post-process and validate products
                validated_products = []
                for product in products_data:
                    if isinstance(product, dict) and product.get("name"):
                        # Clean and validate product data
                        clean_product = self._clean_ai_extracted_product(product)
                        if clean_product:
                            validated_products.append(clean_product)

                self.pagent.logger.info(
                    f"✅ AI extracted {len(validated_products)} valid products"
                )
                return validated_products
            else:
                self.pagent.logger.warning(
                    "⚠️ AI product extraction response not in expected JSON format"
                )
                return []

        except Exception as e:
            self.pagent.logger.error(f"💥 AI product extraction failed: {e}")
            return []

    def _clean_ai_extracted_product(self, product: Dict) -> Optional[Dict]:
        """
        Clean and validate AI-extracted product data.
        """
        try:
            cleaned = {}

            # Name is required
            if not product.get("name") or not isinstance(product["name"], str):
                return None
            cleaned["name"] = product["name"].strip()

            # Clean price
            price = product.get("price")
            if price and isinstance(price, str):
                cleaned["price"] = price.strip()

            # Clean URLs
            url = product.get("url")
            if url and isinstance(url, str):
                url = url.strip()
                if url.startswith("/"):
                    cleaned["url"] = urljoin(self.base_url, url)
                elif url.startswith("http"):
                    cleaned["url"] = url
                elif url and not url.startswith(("javascript:", "mailto:", "#")):
                    cleaned["url"] = urljoin(self.base_url, "/" + url.lstrip("/"))

            # Clean image URL
            image_url = product.get("image_url")
            if image_url and isinstance(image_url, str):
                image_url = image_url.strip()
                if image_url.startswith("/"):
                    cleaned["image_url"] = urljoin(self.base_url, image_url)
                elif image_url.startswith("http"):
                    cleaned["image_url"] = image_url

            # Other fields
            if product.get("product_id"):
                cleaned["product_id"] = str(product["product_id"]).strip()

            if product.get("description"):
                cleaned["description"] = str(product["description"]).strip()

            return cleaned

        except Exception as e:
            self.pagent.logger.debug(f"⚠️ Failed to clean product: {e}")
            return None

    def ai_is_leaf_page(self, html_content: str) -> bool:
        """
        AI-powered leaf page detection. Uses Gemini to determine if a page contains products.
        """
        if not self.ai_enabled:
            return self.is_leaf(html_content)

        try:
            # Use a shorter sample for quick analysis
            sample_html = self._preprocess_html_for_ai(html_content)[:10000]

            prompt = f"""
Analyze this HTML page and determine if it's a PRODUCT LISTING page or a NAVIGATION page.

A PRODUCT LISTING page contains actual products with names, prices, and purchase options.
A NAVIGATION page contains links to categories or subcategories, but no actual products.

Respond with only: "PRODUCT_LISTING" or "NAVIGATION"

HTML to analyze:
{sample_html}
"""

            response = self.gemini_model.generate_content(prompt)
            result = response.text.strip().upper()

            is_product_page = "PRODUCT_LISTING" in result
            self.pagent.logger.debug(
                f"🤖 AI leaf detection: {'LEAF' if is_product_page else 'NON-LEAF'}"
            )

            return is_product_page

        except Exception as e:
            self.pagent.logger.error(f"💥 AI leaf detection failed: {e}")
            return self.is_leaf(html_content)

    def parse_products(self, html_content: str) -> List[Dict]:
        """
        Parse products from a category page HTML content.
        Uses AI-powered extraction when available, falls back to traditional methods.

        Args:
            html_content: HTML content of the category page

        Returns:
            List of product dictionaries
        """
        if self.ai_enabled:
            self.pagent.logger.info(
                "🤖 Using AI-powered neuromorphic product extraction..."
            )
            return self.ai_extract_products_neuromorphic(html_content)
        else:
            self.pagent.logger.info("🔧 Using traditional product extraction...")
            return self._traditional_parse_products(html_content)

    def _traditional_parse_products(self, html_content: str) -> List[Dict]:
        """
        Traditional product parsing using static selectors (fallback method).

        Args:
            html_content: HTML content of the category page

        Returns:
            List of product dictionaries
        """
        soup = BeautifulSoup(html_content, "html.parser")
        products = []

        self.pagent.logger.info("Parsing products from category page...")

        # Try different product container patterns used by Costco
        product_selectors = [
            # Common product tile selectors
            ".product-tile",
            ".product-item",
            ".product-card",
            '[data-automation-id*="product"]',
            ".productTileContainer",
            # Grid-based selectors
            ".product-grid .product",
            ".products-grid .product",
            # Search result patterns
            ".search-results .product",
            ".product-list-item",
        ]

        product_elements = []
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                product_elements = elements
                self.pagent.logger.info(
                    f"Found {len(elements)} products using selector: {selector}"
                )
                break

        if not product_elements:
            # Fallback: look for any elements with product-like patterns
            product_elements = soup.find_all(
                ["div", "article"],
                class_=lambda x: x
                and any(term in x.lower() for term in ["product", "item", "tile"]),
            )
            self.pagent.logger.info(
                f"Fallback: found {len(product_elements)} potential product elements"
            )

        for element in product_elements:
            product = self._parse_single_product(element)
            if product:
                products.append(product)

        self.pagent.logger.info(f"Successfully parsed {len(products)} products")
        return products

    def _parse_single_product(self, element) -> Optional[Dict]:
        """Parse a single product element."""
        try:
            product = {}

            # Product name
            name_selectors = [
                ".product-title",
                ".product-name",
                "h3",
                "h4",
                '[data-automation-id*="product-title"]',
                ".productTitleDescription a",
            ]

            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    product["name"] = name_elem.get_text(strip=True)
                    break

            # Product URL
            link_elem = element.find("a", href=True)
            if link_elem:
                href = link_elem.get("href")
                if href:
                    if href.startswith("/"):
                        product["url"] = urljoin(self.base_url, href)
                    elif href.startswith("http"):
                        product["url"] = href

            # Price
            price_selectors = [
                ".price",
                ".product-price",
                ".sale-price",
                '[data-automation-id*="price"]',
                ".sr-only + span",  # Sometimes price is in span after screen reader text
            ]

            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    if "$" in price_text:
                        product["price"] = price_text
                        break

            # Product ID (often in data attributes)
            product_id = element.get("data-product-id") or element.get("data-item-id")
            if product_id:
                product["product_id"] = product_id

            # Image URL
            img_elem = element.find("img")
            if img_elem:
                img_src = img_elem.get("src") or img_elem.get("data-src")
                if img_src:
                    if img_src.startswith("/"):
                        product["image_url"] = urljoin(self.base_url, img_src)
                    elif img_src.startswith("http"):
                        product["image_url"] = img_src

            # Only return products with at least a name
            if product.get("name"):
                return product

        except Exception as e:
            self.pagent.logger.debug(f"Error parsing product element: {e}")

        return None

    def get_products_by_category(
        self, category_name: str, save_products: bool = True, **fetch_kwargs
    ) -> Dict:
        """
        Get products from a specific category.

        Args:
            category_name: Name of the category to scrape
            save_products: Whether to save parsed products to JSON file
            **fetch_kwargs: Additional arguments for page fetching

        Returns:
            Dict with category info, fetch result, and parsed products
        """
        # Fetch the category page
        fetch_result = self.fetch_category_page(category_name, **fetch_kwargs)

        if not fetch_result["success"]:
            return {
                "category_name": category_name,
                "success": False,
                "error": fetch_result["error"],
                "products": [],
            }

        # Check if this is a leaf page and handle accordingly
        is_leaf_page = fetch_result.get("is_leaf", False)

        if is_leaf_page:
            # Parse products from the leaf page
            products = self.parse_products(fetch_result["content"])
            self.pagent.logger.info(f"Parsed {len(products)} products from leaf page")
        else:
            # Non-leaf page - log that no products were parsed
            products = []
            self.pagent.logger.info("Non-leaf page detected - no products to parse")

        result = {
            "category_name": category_name,
            "success": True,
            "fetch_result": fetch_result,
            "products": products,
            "product_count": len(products),
            "is_leaf": is_leaf_page,
        }

        # Save products to the same request folder
        if save_products and fetch_result.get("request_folder"):
            products_file = Path(fetch_result["request_folder"]) / "products.json"
            try:
                with open(products_file, "w", encoding="utf-8") as f:
                    json.dump(products, f, indent=2, ensure_ascii=False)
                self.pagent.logger.info(f"Products saved to: {products_file}")
                result["products_file"] = str(products_file)
            except Exception as e:
                self.pagent.logger.warning(f"Failed to save products: {e}")

        return result

    def fetch_product_page(self, product_url: str, **kwargs) -> Dict:
        """
        Fetch a specific product page.

        Args:
            product_url: URL of the product page
            **kwargs: Additional arguments for pagent.fetch_page

        Returns:
            Dict with fetch result
        """
        # Extract product identifier from URL for folder naming
        parsed_url = urlparse(product_url)
        path_parts = parsed_url.path.strip("/").split("/")
        product_id = path_parts[-1] if path_parts else "unknown"

        folder_name = f"product_{product_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.pagent.logger.info(f"Fetching product page: {product_url}")

        result = self.pagent.fetch_page(product_url, filename=folder_name, **kwargs)

        return result

    def get_stats(self) -> Dict:
        """Get comprehensive statistics about scraping activity."""
        pagent_stats = self.pagent.get_stats()

        # Add Costco-specific stats
        stats = {
            **pagent_stats,
            "categories_loaded": self.categories_loaded,
            "total_categories": len(self.categories) if self.categories_loaded else 0,
        }

        # Count different types of requests
        if self.pagent.page_requests_dir.exists():
            request_folders = [
                d for d in self.pagent.page_requests_dir.iterdir() if d.is_dir()
            ]

            request_types = {"sitemap": 0, "category": 0, "product": 0, "other": 0}

            for folder in request_folders:
                folder_name = folder.name.lower()
                if "sitemap" in folder_name:
                    request_types["sitemap"] += 1
                elif "category" in folder_name:
                    request_types["category"] += 1
                elif "product" in folder_name:
                    request_types["product"] += 1
                else:
                    request_types["other"] += 1

            stats["request_types"] = request_types

        return stats

    def is_leaf(self, html_content: str) -> bool:
        """
        Determine if a category page is a leaf page (contains product listings)
        or a non-leaf page (contains subcategory navigation).
        Uses AI-powered detection when available.

        Args:
            html_content: HTML content of the category page

        Returns:
            True if the page is a leaf page (contains product listings),
            False if it's a non-leaf page (subcategory navigation)
        """
        if self.ai_enabled:
            return self.ai_is_leaf_page(html_content)
        else:
            return self._traditional_is_leaf(html_content)

    def _traditional_is_leaf(self, html_content: str) -> bool:
        """
        Traditional leaf page detection using static patterns (fallback method).
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Count product tiles with data-testid="ProductTile_" pattern (strongest indicator)
        product_tiles = soup.find_all(
            attrs={"data-testid": lambda x: x and x.startswith("ProductTile_")}
        )

        # Count product tile sets (could be featured products or actual listings)
        product_tile_sets = soup.select(".product-tile-set")

        # Look for pagination (very strong indicator of product listings)
        pagination_elements = soup.select(
            ".pagination, .page-numbers, .pager, .slick-dots"
        )

        # Look for product count/results indicators
        product_count_elements = soup.select(
            "[class*='product-count'], [class*='results-count'], [class*='showing']"
        )

        # Look for main content areas that suggest product listings
        main_product_areas = soup.select(
            "#product-results, .product-list-container, .search-results"
        )

        # Log for debugging
        self.pagent.logger.debug(f"ProductTile_ elements: {len(product_tiles)}")
        self.pagent.logger.debug(f"Product tile sets: {len(product_tile_sets)}")
        self.pagent.logger.debug(f"Pagination elements: {len(pagination_elements)}")
        self.pagent.logger.debug(f"Main product areas: {len(main_product_areas)}")

        # Primary decision: Many ProductTile_ elements indicate a leaf page
        if len(product_tiles) >= 20:
            self.pagent.logger.debug(
                "Many ProductTile_ elements found - definitely a leaf page"
            )
            return True
        elif len(product_tiles) >= 10:
            self.pagent.logger.debug(
                "Moderate ProductTile_ elements found - likely a leaf page"
            )
            return True
        elif len(product_tiles) >= 5:
            # Could be leaf with few products or non-leaf with featured products
            # Check for other strong indicators
            if len(pagination_elements) > 0 or len(main_product_areas) > 0:
                self.pagent.logger.debug(
                    "Few ProductTile_ but has pagination/main areas - leaf page"
                )
                return True
            else:
                self.pagent.logger.debug(
                    "Few ProductTile_ without pagination - likely non-leaf"
                )
                return False
        else:
            # Very few or no ProductTile_ elements
            if len(product_tile_sets) >= 10 and len(pagination_elements) > 0:
                self.pagent.logger.debug(
                    "Many product tile sets with pagination - leaf page"
                )
                return True
            else:
                self.pagent.logger.debug("Few/no ProductTile_ elements - non-leaf page")
                return False

    def update_category_leaf_status(
        self, category_name: str, is_leaf: bool = None
    ) -> bool:
        """
        Update the leaf status of a category in the categories data structure.

        Args:
            category_name: Name of the category to update
            is_leaf: Leaf status to set. If None, will be determined by fetching the page

        Returns:
            True if category was found and updated, False otherwise
        """

        def update_in_categories(categories, name, leaf_status):
            for category in categories:
                if category["name"].lower() == name.lower():
                    if leaf_status is None:
                        # Fetch and determine leaf status
                        try:
                            fetch_result = self.fetch_category_page(name)
                            if fetch_result["success"]:
                                leaf_status = fetch_result.get("is_leaf", False)
                            else:
                                leaf_status = (
                                    False  # Default to non-leaf if fetch fails
                                )
                        except Exception as e:
                            self.pagent.logger.warning(
                                f"Failed to determine leaf status for {name}: {e}"
                            )
                            leaf_status = False

                    category["is_leaf"] = leaf_status
                    category["leaf_status"] = "leaf" if leaf_status else "non-leaf"
                    category["is_leaf_determined"] = True
                    return True

                # Check children recursively
                if category.get("children"):
                    if update_in_categories(category["children"], name, leaf_status):
                        return True
            return False

        return update_in_categories(self.categories, category_name, is_leaf)

    def mark_h2_categories_as_non_leaf(self) -> int:
        """
        Mark all H2-level categories as non-leaf (as specified in requirements).

        Returns:
            Number of categories marked as non-leaf
        """
        count = 0
        for category in self.categories:
            if not category.get("is_leaf_determined", False):
                category["is_leaf"] = False
                category["leaf_status"] = "non-leaf"
                category["is_leaf_determined"] = True
                count += 1
                self.pagent.logger.debug(
                    f"Marked H2 category '{category['name']}' as non-leaf"
                )

        self.pagent.logger.info(f"Marked {count} H2 categories as non-leaf")
        return count

    def get_unknown_leaf_categories(self) -> List[Dict]:
        """
        Get all categories that don't have a determined leaf status.

        Returns:
            List of categories with unknown leaf status
        """
        unknown_categories = []

        def collect_unknown(categories):
            for category in categories:
                if (
                    not category.get("is_leaf_determined", False)
                    and category.get("is_leaf") is None
                ):
                    unknown_categories.append(category)

                # Check children recursively
                if category.get("children"):
                    collect_unknown(category["children"])

        collect_unknown(self.categories)
        return unknown_categories

    def get_all_products_for_all_categories(
        self, max_categories: int = None, delay_between_requests: float = 1.0
    ) -> Dict:
        """
        Get all products for all categories using the leaf detection strategy.
        This method will:
        1. Load all categories
        2. Iterate through each category and subcategory
        3. Determine if each is a leaf page (contains products)
        4. Scrape products from leaf pages only
        5. Skip non-leaf pages (navigation pages)

        Args:
            max_categories: Maximum number of categories to process (for testing/limiting)
            delay_between_requests: Delay in seconds between requests to be respectful

        Returns:
            Dict with comprehensive results including all products found
        """
        self.pagent.logger.info(
            "🚀 Starting comprehensive product scraping for all categories..."
        )

        # Load all categories first
        categories = self.get_categories()
        if not categories:
            return {
                "success": False,
                "error": "No categories found",
                "categories_processed": 0,
                "total_products": 0,
                "results": [],
            }

        # Flatten all categories (including subcategories) into a single list
        all_categories = self._flatten_categories(categories)

        if max_categories:
            all_categories = all_categories[:max_categories]
            self.pagent.logger.info(
                f"🔍 Limited to processing {max_categories} categories for testing"
            )

        self.pagent.logger.info(
            f"📋 Found {len(all_categories)} total categories to process"
        )

        results = []
        total_products = 0
        categories_processed = 0
        leaf_pages_found = 0
        non_leaf_pages_found = 0
        errors = []

        for i, category in enumerate(all_categories):
            category_name = category["name"]
            self.pagent.logger.info(
                f"🔄 Processing category {i+1}/{len(all_categories)}: {category_name}"
            )

            try:
                # Add delay between requests to be respectful
                if i > 0 and delay_between_requests > 0:
                    time.sleep(delay_between_requests)

                # Scrape this category
                result = self.get_products_by_category(category_name)

                if result["success"]:
                    categories_processed += 1

                    if result["is_leaf"]:
                        leaf_pages_found += 1
                        product_count = result["product_count"]
                        total_products += product_count

                        self.pagent.logger.info(
                            f"✅ LEAF page: Found {product_count} products in '{category_name}'"
                        )

                        # Update category status in our data structure
                        self.update_category_leaf_status(category_name, True)
                    else:
                        non_leaf_pages_found += 1
                        self.pagent.logger.info(
                            f"🔗 NON-LEAF page: '{category_name}' is a navigation page"
                        )

                        # Update category status in our data structure
                        self.update_category_leaf_status(category_name, False)

                    results.append(result)
                else:
                    error_msg = f"Failed to process category '{category_name}': {result.get('error', 'Unknown error')}"
                    self.pagent.logger.error(f"❌ {error_msg}")
                    errors.append(error_msg)
                    results.append(result)

            except Exception as e:
                error_msg = f"Exception processing category '{category_name}': {str(e)}"
                self.pagent.logger.error(f"💥 {error_msg}")
                errors.append(error_msg)

                # Add failed result
                results.append(
                    {
                        "category_name": category_name,
                        "success": False,
                        "error": str(e),
                        "products": [],
                        "product_count": 0,
                        "is_leaf": False,
                    }
                )

        # Final summary
        self.pagent.logger.info(f"""
🎉 COMPREHENSIVE SCRAPING COMPLETE!
📊 Summary:
   • Categories processed: {categories_processed}/{len(all_categories)}
   • Leaf pages (with products): {leaf_pages_found}
   • Non-leaf pages (navigation): {non_leaf_pages_found}
   • Total products found: {total_products}
   • Errors encountered: {len(errors)}
        """)

        if errors:
            self.pagent.logger.warning(f"⚠️  Errors encountered:")
            for error in errors[:5]:  # Show first 5 errors
                self.pagent.logger.warning(f"   • {error}")
            if len(errors) > 5:
                self.pagent.logger.warning(
                    f"   • ... and {len(errors) - 5} more errors"
                )

        return {
            "success": True,
            "categories_processed": categories_processed,
            "total_categories": len(all_categories),
            "leaf_pages_found": leaf_pages_found,
            "non_leaf_pages_found": non_leaf_pages_found,
            "total_products": total_products,
            "errors": errors,
            "results": results,
            "summary": {
                "completion_rate": f"{categories_processed}/{len(all_categories)} ({(categories_processed/len(all_categories)*100):.1f}%)",
                "products_per_leaf_page": total_products / max(leaf_pages_found, 1),
                "leaf_page_ratio": f"{leaf_pages_found}/{categories_processed} ({(leaf_pages_found/max(categories_processed, 1)*100):.1f}%)",
            },
        }

    def test_comprehensive_scraping(self, max_categories: int = 5) -> Dict:
        """
        Test the comprehensive scraping strategy with a limited number of categories.

        Args:
            max_categories: Number of categories to test with (default: 5)

        Returns:
            Dict with test results
        """
        self.pagent.logger.info(
            f"🧪 Testing comprehensive scraping with {max_categories} categories..."
        )

        return self.get_all_products_for_all_categories(
            max_categories=max_categories,
            delay_between_requests=0.5,  # Shorter delay for testing
        )

    def scrape_all_categories_with_ai_extraction(
        self, max_categories: int = None, delay_between_requests: float = 2.0
    ) -> Dict:
        """
        Scrape all categories using AI-powered entity extraction callbacks.

        This method applies the AI callback to each category, generating custom
        extraction functions and extracting all discoverable entities.

        Args:
            max_categories: Maximum number of categories to process
            delay_between_requests: Delay between requests (default 2.0 seconds)

        Returns:
            Dict with comprehensive AI extraction results
        """
        if not self.ai_enabled:
            return {"success": False, "error": "AI features not enabled"}

        self.pagent.logger.info(
            "🚀 Starting AI-powered entity extraction for all categories..."
        )

        # Load all categories
        categories = self.get_categories()
        if not categories:
            return {"success": False, "error": "No categories found"}

        # Flatten categories
        all_categories = self._flatten_categories(categories)

        if max_categories:
            all_categories = all_categories[:max_categories]
            self.pagent.logger.info(
                f"🔍 Limited to {max_categories} categories for testing"
            )

        self.pagent.logger.info(
            f"📋 Processing {len(all_categories)} categories with AI extraction"
        )

        results = []
        total_entities_found = set()
        total_files_created = []
        successful_extractions = 0
        failed_extractions = 0

        for i, category in enumerate(all_categories):
            category_name = category["name"]
            self.pagent.logger.info(
                f"🔄 AI extraction {i+1}/{len(all_categories)}: {category_name}"
            )

            try:
                # Add delay between requests
                if i > 0 and delay_between_requests > 0:
                    time.sleep(delay_between_requests)

                # Apply AI extraction callback
                result = self.scrape_category_with_ai_callback(category_name)

                if result["success"] and result.get("ai_extraction", {}).get("success"):
                    successful_extractions += 1
                    entities = result.get("entities_found", [])
                    files = result.get("files_created", [])

                    total_entities_found.update(entities)
                    total_files_created.extend(files)

                    self.pagent.logger.info(
                        f"✅ {category_name}: {len(entities)} entity types, {len(files)} files"
                    )
                else:
                    failed_extractions += 1
                    error = result.get("error") or result.get("ai_extraction", {}).get(
                        "error", "Unknown"
                    )
                    self.pagent.logger.warning(f"⚠️ {category_name}: {error}")

                results.append(result)

            except Exception as e:
                failed_extractions += 1
                error_msg = f"Exception in AI extraction for {category_name}: {e}"
                self.pagent.logger.error(f"💥 {error_msg}")

                results.append(
                    {
                        "category_name": category_name,
                        "success": False,
                        "error": str(e),
                        "ai_extraction": {"success": False, "error": str(e)},
                    }
                )

        # Final summary
        self.pagent.logger.info(f"""
🎉 AI ENTITY EXTRACTION COMPLETE!
📊 Summary:
   • Categories processed: {len(all_categories)}
   • Successful extractions: {successful_extractions}
   • Failed extractions: {failed_extractions}
   • Unique entity types found: {len(total_entities_found)}
   • Total files created: {len(total_files_created)}
   • Entity types: {', '.join(sorted(total_entities_found)) if total_entities_found else 'None'}
        """)

        return {
            "success": True,
            "categories_processed": len(all_categories),
            "successful_extractions": successful_extractions,
            "failed_extractions": failed_extractions,
            "unique_entity_types": list(total_entities_found),
            "total_files_created": len(total_files_created),
            "results": results,
            "summary": {
                "success_rate": f"{successful_extractions}/{len(all_categories)} ({(successful_extractions/len(all_categories)*100):.1f}%)",
                "entity_types_discovered": len(total_entities_found),
                "avg_files_per_category": len(total_files_created)
                / max(len(all_categories), 1),
            },
        }

    def _flatten_categories(self, categories: List[Dict]) -> List[Dict]:
        """
        Flatten the nested category structure into a single list.

        Args:
            categories: Nested category structure

        Returns:
            Flat list of all categories
        """
        flattened = []

        def flatten_recursive(cats):
            for cat in cats:
                flattened.append(cat)
                if cat.get("children"):
                    flatten_recursive(cat["children"])

        flatten_recursive(categories)
        return flattened

    def scrape_category_with_ai_callback(self, category_name: str) -> Dict:
        """
        Scrape a category using AI callback that generates custom extraction functions.

        Args:
            category_name: Name of the category to scrape

        Returns:
            Dict with scraping results and AI extraction details
        """
        if not self.ai_enabled:
            return {
                "success": False,
                "error": "AI features not enabled",
                "category_name": category_name,
            }

        try:
            # Fetch the category page
            fetch_result = self.fetch_category_page(category_name)

            if not fetch_result["success"]:
                return {
                    "category_name": category_name,
                    "success": False,
                    "error": fetch_result["error"],
                    "ai_extraction": {"success": False, "error": "Page fetch failed"},
                }

            # Apply AI callback to generate and execute extraction function
            ai_result = self.ai_callback_generate_and_execute_extractor(
                fetch_result["content"], fetch_result.get("request_folder")
            )

            return {
                "category_name": category_name,
                "success": True,
                "fetch_result": fetch_result,
                "ai_extraction": ai_result,
                "entities_found": ai_result.get("entities_found", []),
                "files_created": ai_result.get("files_created", []),
            }

        except Exception as e:
            return {
                "category_name": category_name,
                "success": False,
                "error": str(e),
                "ai_extraction": {"success": False, "error": str(e)},
            }

    def ai_callback_generate_and_execute_extractor(
        self, html_content: str, request_folder: str = None
    ) -> Dict:
        """
        AI callback that generates a custom Python extraction function and executes it.

        This is the revolutionary approach where AI:
        1. Analyzes HTML to discover entities
        2. Generates a Python function to extract those entities
        3. Saves the function as extract_data.py
        4. Executes the function to create organized JSON files

        Args:
            html_content: HTML content to analyze
            request_folder: Folder to save extraction function and results

        Returns:
            Dict with AI extraction results
        """
        if not self.ai_enabled:
            return {"success": False, "error": "AI not enabled"}

        try:
            self.pagent.logger.info("🤖 Starting AI function generation...")

            # Step 1: Generate extraction function using AI
            function_result = self._generate_extractor_function(html_content)
            if not function_result["success"]:
                return function_result

            # Step 2: Save the generated function
            if request_folder:
                function_path = Path(request_folder) / "extract_data.py"
                try:
                    with open(function_path, "w", encoding="utf-8") as f:
                        f.write(function_result["function_code"])
                    self.pagent.logger.info(
                        f"💾 Saved extraction function: {function_path}"
                    )
                except Exception as e:
                    self.pagent.logger.warning(f"⚠️ Failed to save function: {e}")

            # Step 3: Execute the generated function
            execution_result = self._execute_extractor_function(
                function_result["function_code"], html_content, request_folder
            )

            return {
                "success": True,
                "function_generated": True,
                "function_code": function_result["function_code"],
                "execution_result": execution_result,
                "entities_found": execution_result.get("entities_found", []),
                "files_created": execution_result.get("files_created", []),
            }

        except Exception as e:
            self.pagent.logger.error(f"💥 AI callback failed: {e}")
            return {"success": False, "error": str(e)}

    def _generate_extractor_function(self, html_content: str) -> Dict:
        """
        Use AI to generate a custom Python extraction function with standardized category interface.
        """
        # Preprocess HTML for AI analysis
        cleaned_html = self._preprocess_html_for_ai(html_content)

        # Determine page type hint for better category classification
        page_type_hint = self._determine_page_type_hint(cleaned_html)

        prompt = f"""
You are an expert Python developer creating data extraction functions for Costco.ca pages.

CRITICAL: Use the STANDARDIZED CATEGORY INTERFACE for all category extractions:

For categories.json, each category MUST use this exact structure:
```json
{{
    "name": "Category Display Name",
    "url": "/relative-url-path", 
    "category_type": "leaf_product|leaf_service|leaf_location|non_leaf_navigation|non_leaf_hub|unknown",
    "description": "Brief description if available",
    "parent_category": "Parent category name if applicable",
    "subcategories": ["list", "of", "subcategory", "names"],
    "is_leaf": true/false,
    "metadata": {{"additional": "data"}}
}}
```

CATEGORY TYPE DEFINITIONS:
- leaf_product: Contains actual products for purchase
- leaf_service: Contains services (insurance, photo, travel, etc.)
- leaf_location: Store locations/warehouses
- non_leaf_navigation: Navigation to subcategories
- non_leaf_hub: Hub page with mixed content
- unknown: Cannot determine type

PAGE TYPE: {page_type_hint}

Create a Python function that:
1. Discovers ALL entities (products, categories, services, promotions, etc.)
2. For CATEGORIES: Use the standardized interface above
3. For OTHER entities: Use appropriate structures
4. Saves each entity type to separate JSON files
5. Returns dict with entities_found list and files_created list

CRITICAL RETURN FORMAT:
```python
return {{
    "entities_found": ["categories", "products", "services"],  # List of ENTITY TYPE NAMES (strings)
    "files_created": ["/path/to/categories.json", "/path/to/products.json"]  # List of file paths
}}
```

Requirements:
- Function named `extract_data(html_content, output_folder=None)`
- Use BeautifulSoup for parsing
- Handle errors gracefully
- Determine category_type based on URL patterns and context
- Set is_leaf correctly based on category_type
- entities_found must contain ONLY string names of entity types, NOT the actual objects
- Only include entity types in entities_found if you actually found and saved data for them

HTML to analyze:
{cleaned_html[:20000]}

Return ONLY the complete Python function code, no explanations.
"""

        try:
            response = self.gemini_model.generate_content(prompt)
            function_code = response.text.strip()

            # Clean up the response to extract just the Python code
            if "```python" in function_code:
                function_code = function_code.split("```python")[1].split("```")[0]
            elif "```" in function_code:
                function_code = function_code.split("```")[1].split("```")[0]

            # Ensure proper imports including category interface
            required_imports = """from bs4 import BeautifulSoup
import json
from pathlib import Path

# Standardized category structure for Costco pages
def create_standard_category(name, url=None, category_type="unknown", description=None, 
                           parent_category=None, subcategories=None, metadata=None):
    \"\"\"Create a category using the standard interface.\"\"\"
    if subcategories is None:
        subcategories = []
    if metadata is None:
        metadata = {}
    
    is_leaf = category_type in ["leaf_product", "leaf_service", "leaf_location"]
    
    return {
        "name": name,
        "url": url,
        "category_type": category_type,
        "description": description,
        "parent_category": parent_category,
        "subcategories": subcategories,
        "is_leaf": is_leaf,
        "metadata": metadata
    }

def determine_category_type(url, name, context=""):
    \"\"\"Determine category type based on URL patterns and context.\"\"\"
    if not url:
        return "unknown"
    
    url_lower = url.lower()
    name_lower = name.lower()
    context_lower = context.lower()
    
    # Product indicators
    if any(indicator in url_lower for indicator in ["product", "catalog", ".product.", "item"]):
        return "leaf_product"
    
    # Service indicators  
    if any(indicator in url_lower + name_lower for indicator in 
           ["insurance", "photo", "travel", "optical", "pharmacy", "service"]):
        return "leaf_service"
    
    # Location indicators
    if any(indicator in url_lower + name_lower for indicator in 
           ["warehouse", "location", "store", "address"]):
        return "leaf_location"
    
    # Navigation indicators
    if any(indicator in url_lower for indicator in 
           ["category", "department", "browse", "sitemap"]):
        return "non_leaf_navigation"
    
    # Hub indicators (mixed content)
    if any(indicator in url_lower + name_lower for indicator in 
           ["home", "main", "index", "hub"]):
        return "non_leaf_hub"
    
    return "unknown"

"""

            if not any(
                required_import in function_code
                for required_import in [
                    "from bs4 import BeautifulSoup",
                    "import json",
                    "from pathlib import Path",
                ]
            ):
                function_code = required_imports + "\n\n" + function_code

            return {
                "success": True,
                "function_code": function_code.strip(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate function: {e}",
            }

    def _execute_extractor_function(
        self, function_code: str, html_content: str, output_folder: str = None
    ) -> Dict:
        """
        Execute the AI-generated extraction function.
        """
        try:
            # Create a safe execution environment
            exec_globals = {
                "__builtins__": __builtins__,
                "BeautifulSoup": BeautifulSoup,
                "json": json,
                "Path": Path,
            }

            # Execute the function code
            exec(function_code, exec_globals)

            # Call the extract_data function
            if "extract_data" in exec_globals:
                result = exec_globals["extract_data"](html_content, output_folder)
                self.pagent.logger.info(f"✅ Function executed successfully")
                return result
            else:
                return {
                    "success": False,
                    "error": "extract_data function not found in generated code",
                }

        except Exception as e:
            self.pagent.logger.error(f"💥 Function execution failed: {e}")
            return {
                "success": False,
                "error": f"Execution failed: {e}",
                "entities_found": [],
                "files_created": [],
            }

    def _load_cached_categories(self) -> Optional[List[Dict]]:
        """
        Load cached categories from the most recent sitemap request folder.
        """
        try:
            if not self.pagent.page_requests_dir.exists():
                return None

            # Find the most recent sitemap folder
            sitemap_folders = [
                d
                for d in self.pagent.page_requests_dir.iterdir()
                if d.is_dir() and "sitemap" in d.name.lower()
            ]

            if not sitemap_folders:
                return None

            # Sort by creation time, get most recent
            latest_folder = max(sitemap_folders, key=lambda x: x.stat().st_ctime)
            categories_file = latest_folder / "categories.json"

            if categories_file.exists():
                with open(categories_file, "r", encoding="utf-8") as f:
                    categories = json.load(f)
                self.pagent.logger.info(
                    f"Loaded {len(categories)} cached categories from {categories_file}"
                )
                return categories

        except Exception as e:
            self.pagent.logger.debug(f"Failed to load cached categories: {e}")

        return None

    def _save_categories_to_request_folder(self, request_folder: str):
        """
        Save categories to the specified request folder.
        """
        try:
            categories_file = Path(request_folder) / "categories.json"
            with open(categories_file, "w", encoding="utf-8") as f:
                json.dump(self.categories, f, indent=2, ensure_ascii=False)
            self.pagent.logger.info(f"Categories saved to: {categories_file}")
        except Exception as e:
            self.pagent.logger.warning(f"Failed to save categories: {e}")

    def _determine_page_type_hint(self, html_content: str) -> str:
        """
        Analyze HTML to provide a hint about the page type for better category classification.
        """
        html_lower = html_content.lower()

        # Check for product indicators
        product_indicators = [
            "product-tile",
            "product-grid",
            "add-to-cart",
            "price",
            "buy-now",
        ]
        if any(indicator in html_lower for indicator in product_indicators):
            return "product_listing"

        # Check for service indicators
        service_indicators = [
            "insurance",
            "photo",
            "travel",
            "optical",
            "pharmacy",
            "gas",
        ]
        if any(indicator in html_lower for indicator in service_indicators):
            return "service_page"

        # Check for location indicators
        location_indicators = [
            "warehouse",
            "store-hours",
            "address",
            "phone",
            "directions",
        ]
        if any(indicator in html_lower for indicator in location_indicators):
            return "location_page"

        # Check for navigation indicators
        nav_indicators = ["sitemap", "category", "department", "browse", "menu"]
        if any(indicator in html_lower for indicator in nav_indicators):
            return "navigation_page"

        return "unknown"


# Example usage and convenience functions
def create_costco_scraper(
    db_folder: str = "db", gemini_api_key: str = None
) -> CostcoWebScraper:
    """
    Factory function to create a CostcoWebScraper instance.

    Args:
        db_folder: Database folder for storing scraped data
        gemini_api_key: Google Gemini API key for AI-powered extraction
    """
    if not gemini_api_key:
        # Try to get from environment variable
        gemini_api_key = os.getenv("GEMINI_API_KEY")

    return CostcoWebScraper(db_folder=db_folder, gemini_api_key=gemini_api_key)


if __name__ == "__main__":
    """
    Main execution: Loop through categories, get all products, and learn from functions.
    Limited to 10 categories for initial testing.
    """
    print("🚀 Starting Costco Web Scraper - Learning Mode")
    print("📋 Processing 10 categories to extract products and learn functions...")

    try:
        # Create scraper instance with AI capabilities
        scraper = create_costco_scraper()

        if not scraper.ai_enabled:
            print("⚠️  AI features not available - check GEMINI_API_KEY in .env file")
            print("🔄 Proceeding with traditional extraction methods...")
        else:
            print("🤖 AI-powered extraction enabled!")

        # Test with 10 categories using AI extraction
        print("\n🧪 Starting AI-powered extraction test with 10 categories...")
        results = scraper.scrape_all_categories_with_ai_extraction(
            max_categories=10,
            delay_between_requests=1.5,  # Be respectful to the server
        )

        if results["success"]:
            print(f"\n🎉 Extraction Complete!")
            print(
                f"✅ Successfully processed: {results['successful_extractions']}/{results['categories_processed']} categories"
            )
            print(
                f"🔍 Entity types discovered: {', '.join(results['unique_entity_types']) if results['unique_entity_types'] else 'None'}"
            )
            print(f"📁 Total files created: {results['total_files_created']}")
            print(f"📊 Success rate: {results['summary']['success_rate']}")

            # Show detailed results for first few categories
            print("\n📋 Detailed Results (first 5):")
            for i, result in enumerate(results["results"][:5]):
                status = (
                    "✅" if result.get("ai_extraction", {}).get("success") else "❌"
                )
                entities = result.get("entities_found", [])
                files = result.get("files_created", [])
                print(
                    f"  {status} {result['category_name']}: {len(entities)} entity types, {len(files)} files"
                )
        else:
            print(f"❌ Extraction failed: {results.get('error', 'Unknown error')}")

    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback

        traceback.print_exc()

    print("\n🏁 Scraper execution completed")
