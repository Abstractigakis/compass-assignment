#!/usr/bin/env python3
"""
Costco Service Layer

High-level service that encapsulates the Costco web scraper and database operations.
Provides a clean API for scraping and storing Costco data with callback integration.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

from costco_database import CostcoDatabase
from category_interface import CategoryItem, CategoryType, validate_category_output
from costco_web_scraper import CostcoWebScraper


class CostcoService:
    """
    High-level service for Costco data extraction and storage.

    This service coordinates between the web scraper and database,
    providing callbacks for real-time data processing and storage.
    """

    def __init__(
        self,
        db_path: str = "db/costco.db",
        output_folder: str = "db/scraping_output",
        ai_enabled: bool = True,
    ):
        """
        Initialize the Costco service.

        Args:
            db_path: Path to SQLite database
            output_folder: Folder for temporary scraping files
            ai_enabled: Whether to use AI for enhanced extraction
        """
        self.db = CostcoDatabase(db_path)
        self.scraper = CostcoWebScraper()
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.ai_enabled = ai_enabled

        # Current session tracking
        self.current_session_id: Optional[str] = None
        self.category_cache: Dict[str, int] = {}  # URL -> category_id mapping

        # Callback hooks
        self.on_category_found: Optional[Callable[[str, CategoryItem], None]] = None
        self.on_product_found: Optional[Callable[[str, Dict], None]] = None
        self.on_page_processed: Optional[Callable[[str, Dict], None]] = None
        self.on_error: Optional[Callable[[str, Exception], None]] = None

    def start_scraping_session(
        self, categories_limit: Optional[int] = None, metadata: Optional[Dict] = None
    ) -> str:
        """
        Start a new scraping session.

        Args:
            categories_limit: Maximum number of categories to process
            metadata: Additional session metadata

        Returns:
            Session ID
        """
        session_metadata = {
            "categories_limit": categories_limit,
            "ai_enabled": self.ai_enabled,
            "scraper_version": "2.0",
            **(metadata or {}),
        }

        self.current_session_id = self.db.start_scraping_session(
            ai_enabled=self.ai_enabled, metadata=session_metadata
        )

        self.category_cache.clear()
        print(f"🚀 Started Costco scraping session: {self.current_session_id}")
        return self.current_session_id

    def end_scraping_session(self, status: str = "completed"):
        """End the current scraping session."""
        if self.current_session_id:
            self.db.end_scraping_session(self.current_session_id, status)
            print(f"✅ Ended scraping session: {self.current_session_id}")

            # Show session summary
            stats = self.db.get_session_stats(self.current_session_id)
            if stats:
                print(f"📊 Session Summary:")
                print(f"   Categories: {stats.get('categories_found', 0)}")
                print(f"   Products: {stats.get('products_found', 0)}")
                print(f"   Leaf Categories: {stats.get('leaf_categories', 0)}")
                print(
                    f"   Navigation Categories: {stats.get('navigation_categories', 0)}"
                )
                if stats.get("avg_product_price"):
                    print(f"   Avg Product Price: ${stats['avg_product_price']:.2f}")

            self.current_session_id = None
            self.category_cache.clear()

    def _setup_scraper_callbacks(self):
        """Setup callback functions for the web scraper."""

        def category_callback(
            categories_data: List[Dict], page_url: str, page_type: str
        ):
            """Handle category extraction callback."""
            try:
                # Validate and convert to standard format
                validated_categories = validate_category_output(categories_data)

                for category in validated_categories:
                    category_id = self._store_category(category, page_url)

                    # Trigger user callback if set
                    if self.on_category_found:
                        self.on_category_found(self.current_session_id, category)

                    print(f"  📁 Stored category: {category.name} (ID: {category_id})")

            except Exception as e:
                print(f"❌ Error processing categories from {page_url}: {e}")
                if self.on_error:
                    self.on_error(page_url, e)

        def product_callback(
            products_data: List[Dict], category_url: str, category_name: str
        ):
            """Handle product extraction callback."""
            try:
                category_id = self.category_cache.get(category_url)

                for product_data in products_data:
                    product_id = self._store_product(product_data)

                    # Link to category if we have it
                    if category_id:
                        position = products_data.index(product_data)
                        self.db.link_category_product(
                            category_id,
                            product_id,
                            position=position,
                            featured=product_data.get("featured", False),
                        )

                    # Trigger user callback if set
                    if self.on_product_found:
                        self.on_product_found(self.current_session_id, product_data)

                    print(
                        f"    🛍️  Stored product: {product_data.get('name', 'Unknown')} (ID: {product_id})"
                    )

            except Exception as e:
                print(f"❌ Error processing products from {category_url}: {e}")
                if self.on_error:
                    self.on_error(category_url, e)

        def page_callback(page_info: Dict):
            """Handle page processing callback."""
            try:
                if self.on_page_processed:
                    self.on_page_processed(self.current_session_id, page_info)

                print(
                    f"  📄 Processed page: {page_info.get('url', 'Unknown')} "
                    f"({page_info.get('categories_count', 0)} categories, "
                    f"{page_info.get('products_count', 0)} products)"
                )

            except Exception as e:
                print(f"❌ Error in page callback: {e}")
                if self.on_error:
                    self.on_error("page_callback", e)

        # Set callbacks on scraper
        self.scraper.on_categories_extracted = category_callback
        self.scraper.on_products_extracted = product_callback
        self.scraper.on_page_processed = page_callback

    def _store_category(
        self, category: CategoryItem, page_url: str, parent_id: Optional[int] = None
    ) -> int:
        """Store a category in the database."""
        if not self.current_session_id:
            raise RuntimeError("No active scraping session")

        category_id = self.db.save_category(
            self.current_session_id, category, parent_id
        )

        # Cache the category for product linking
        if category.url:
            self.category_cache[category.url] = category_id
        self.category_cache[page_url] = category_id

        return category_id

    def _store_product(self, product_data: Dict) -> int:
        """Store a product in the database."""
        if not self.current_session_id:
            raise RuntimeError("No active scraping session")

        return self.db.save_product(self.current_session_id, product_data)

    def scrape_categories(
        self,
        categories_limit: Optional[int] = None,
        specific_categories: Optional[List[str]] = None,
    ) -> str:
        """
        Scrape Costco categories and store in database.

        Args:
            categories_limit: Maximum number of categories to process
            specific_categories: List of specific category names to scrape

        Returns:
            Session ID
        """
        # Start session if not already active
        if not self.current_session_id:
            self.start_scraping_session(categories_limit=categories_limit)

        # Setup callbacks
        self._setup_scraper_callbacks()

        try:
            print(f"🔍 Starting Costco category scraping...")

            # Use the existing scraper's run method
            if specific_categories:
                # Filter categories in the scraper
                self.scraper.target_categories = specific_categories

            if categories_limit:
                self.scraper.categories_limit = categories_limit

            # Run the scraper with database storage
            session_folder = self.output_folder / f"session_{self.current_session_id}"
            session_folder.mkdir(exist_ok=True)

            result = self.scraper.run(
                output_folder=str(session_folder), use_ai=self.ai_enabled
            )

            print(f"✅ Scraping completed successfully")
            return self.current_session_id

        except Exception as e:
            print(f"❌ Scraping failed: {e}")
            self.end_scraping_session(status="failed")
            raise

    def get_session_data(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive data for a session."""
        target_session = session_id or self.current_session_id
        if not target_session:
            raise ValueError("No session specified and no active session")

        # Get session stats
        stats = self.db.get_session_stats(target_session)

        # Get category hierarchy
        categories = self.db.get_category_hierarchy(target_session)

        # Get top-level categories with product counts
        root_categories = self.db.get_categories(target_session, parent_id=None)

        return {
            "session_id": target_session,
            "stats": stats,
            "categories": categories,
            "root_categories": root_categories,
        }

    def search_products(
        self, query: str, session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for products across sessions."""
        target_session = session_id or self.current_session_id
        if not target_session:
            # Search across all sessions
            recent_sessions = self.db.get_recent_sessions(limit=1)
            if recent_sessions:
                target_session = recent_sessions[0]["session_id"]
            else:
                return []

        return self.db.search_products(target_session, query)

    def export_session_data(
        self, session_id: Optional[str] = None, export_format: str = "json"
    ) -> str:
        """Export session data to file."""
        target_session = session_id or self.current_session_id
        if not target_session:
            raise ValueError("No session specified and no active session")

        data = self.get_session_data(target_session)

        # Export to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if export_format == "json":
            export_file = (
                self.output_folder / f"export_{target_session}_{timestamp}.json"
            )
            with open(export_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")

        print(f"📁 Exported session data to: {export_file}")
        return str(export_file)

    def cleanup_old_data(self, keep_days: int = 30):
        """Clean up old scraping data."""
        self.db.cleanup_old_sessions(keep_days)

    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics."""
        recent_sessions = self.db.get_recent_sessions(limit=5)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Overall counts
            cursor.execute("SELECT COUNT(*) FROM scraping_sessions")
            total_sessions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM categories")
            total_categories = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]

            # Database size
            cursor.execute(
                "SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()"
            )
            db_size = cursor.fetchone()[0]

        return {
            "total_sessions": total_sessions,
            "total_categories": total_categories,
            "total_products": total_products,
            "database_size_bytes": db_size,
            "recent_sessions": recent_sessions,
        }


# Example usage and callbacks
def example_usage():
    """Example of how to use the Costco service with callbacks."""

    service = CostcoService()

    # Set up custom callbacks
    def on_category_found(session_id: str, category: CategoryItem):
        print(
            f"🎯 New category found: {category.name} ({category.category_type.value})"
        )

    def on_product_found(session_id: str, product: Dict):
        price = product.get("price", "N/A")
        print(f"🛒 New product found: {product.get('name')} - ${price}")

    def on_error(location: str, error: Exception):
        print(f"⚠️  Error at {location}: {error}")

    # Register callbacks
    service.on_category_found = on_category_found
    service.on_product_found = on_product_found
    service.on_error = on_error

    # Run scraping
    try:
        session_id = service.scrape_categories(categories_limit=5)

        # Get results
        data = service.get_session_data()
        print(f"\n📊 Final Results:")
        print(f"   Session: {data['session_id']}")
        print(f"   Categories: {data['stats'].get('categories_found', 0)}")
        print(f"   Products: {data['stats'].get('products_found', 0)}")

        # Export data
        export_file = service.export_session_data()
        print(f"   Exported to: {export_file}")

        # End session
        service.end_scraping_session()

    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        service.end_scraping_session(status="failed")


if __name__ == "__main__":
    example_usage()
