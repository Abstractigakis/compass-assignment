#!/usr/bin/env python3
"""
Database Manager for Costco Web Scraper

Handles SQLite database operations for storing categories, products, and relationships.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager

from category_interface import CategoryItem, CategoryType


class CostcoDatabase:
    """SQLite database manager for Costco scraping data."""

    def __init__(self, db_path: str = "db/costco.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database with schema if it doesn't exist."""
        schema_path = Path(__file__).parent / "database_schema.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"Database schema not found at {schema_path}")

        with open(schema_path, "r") as f:
            schema_sql = f.read()

        with self.get_connection() as conn:
            # Check if tables exist
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='scraping_sessions'
            """)

            if not cursor.fetchone():
                # Database is empty, initialize with schema
                conn.executescript(schema_sql)
                print(f"Initialized database at {self.db_path}")

    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        try:
            yield conn
        finally:
            conn.close()

    def start_scraping_session(
        self, ai_enabled: bool = True, metadata: Optional[Dict] = None
    ) -> str:
        """
        Start a new scraping session.

        Args:
            ai_enabled: Whether AI extraction is enabled
            metadata: Additional session metadata

        Returns:
            Session ID
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO scraping_sessions (session_id, ai_enabled, metadata)
                VALUES (?, ?, ?)
            """,
                (session_id, ai_enabled, json.dumps(metadata or {})),
            )
            conn.commit()

        print(f"Started scraping session: {session_id}")
        return session_id

    def end_scraping_session(self, session_id: str, status: str = "completed"):
        """
        End a scraping session and update statistics.

        Args:
            session_id: Session to end
            status: Final status (completed, failed, cancelled)
        """
        with self.get_connection() as conn:
            # Update session end time and status
            conn.execute(
                """
                UPDATE scraping_sessions 
                SET end_time = CURRENT_TIMESTAMP,
                    status = ?,
                    total_categories = (
                        SELECT COUNT(*) FROM categories WHERE session_id = ?
                    ),
                    total_products = (
                        SELECT COUNT(*) FROM products WHERE session_id = ?
                    ),
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """,
                (status, session_id, session_id, session_id),
            )
            conn.commit()

        print(f"Ended scraping session {session_id} with status: {status}")

    def save_category(
        self, session_id: str, category: CategoryItem, parent_id: Optional[int] = None
    ) -> int:
        """
        Save a category to the database.

        Args:
            session_id: Current scraping session
            category: CategoryItem to save
            parent_id: ID of parent category if any

        Returns:
            Category ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Calculate category level and path
            level = 0
            path = category.name

            if parent_id:
                cursor.execute(
                    "SELECT level, path FROM categories WHERE id = ?", (parent_id,)
                )
                parent_data = cursor.fetchone()
                if parent_data:
                    level = parent_data["level"] + 1
                    path = f"{parent_data['path']} > {category.name}"

            # Insert category
            cursor.execute(
                """
                INSERT OR REPLACE INTO categories 
                (session_id, name, url, category_type, description, parent_category_id, 
                 is_leaf, level, path, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    category.name,
                    category.url,
                    category.category_type.value,
                    category.description,
                    parent_id,
                    category.is_leaf_category(),
                    level,
                    path,
                    json.dumps(category.metadata),
                ),
            )

            category_id = cursor.lastrowid
            conn.commit()

            return category_id

    def save_product(self, session_id: str, product_data: Dict[str, Any]) -> int:
        """
        Save a product to the database.

        Args:
            session_id: Current scraping session
            product_data: Product information dictionary

        Returns:
            Product ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO products 
                (session_id, name, item_number, price, original_price, currency,
                 description, brand, model, availability, rating, review_count,
                 image_url, product_url, warehouse_only, online_only, member_exclusive, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    product_data.get("name", ""),
                    product_data.get("item_number"),
                    product_data.get("price"),
                    product_data.get("original_price"),
                    product_data.get("currency", "CAD"),
                    product_data.get("description"),
                    product_data.get("brand"),
                    product_data.get("model"),
                    product_data.get("availability"),
                    product_data.get("rating"),
                    product_data.get("review_count", 0),
                    product_data.get("image_url"),
                    product_data.get("product_url"),
                    product_data.get("warehouse_only", False),
                    product_data.get("online_only", False),
                    product_data.get("member_exclusive", False),
                    json.dumps(product_data.get("metadata", {})),
                ),
            )

            product_id = cursor.lastrowid
            conn.commit()

            return product_id

    def link_category_product(
        self,
        category_id: int,
        product_id: int,
        position: Optional[int] = None,
        featured: bool = False,
    ):
        """
        Create relationship between category and product.

        Args:
            category_id: Category ID
            product_id: Product ID
            position: Position within category
            featured: Is this a featured product
        """
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO category_products 
                (category_id, product_id, position, featured)
                VALUES (?, ?, ?, ?)
            """,
                (category_id, product_id, position, featured),
            )
            conn.commit()

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a scraping session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM session_stats WHERE session_id = ?", (session_id,)
            )
            row = cursor.fetchone()

            if row:
                return dict(row)
            return {}

    def get_categories(
        self, session_id: str, parent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get categories for a session, optionally filtered by parent."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if parent_id is not None:
                cursor.execute(
                    """
                    SELECT * FROM categories 
                    WHERE session_id = ? AND parent_category_id = ?
                    ORDER BY name
                """,
                    (session_id, parent_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM categories 
                    WHERE session_id = ? AND parent_category_id IS NULL
                    ORDER BY name
                """,
                    (session_id,),
                )

            return [dict(row) for row in cursor.fetchall()]

    def get_category_hierarchy(self, session_id: str) -> List[Dict[str, Any]]:
        """Get full category hierarchy for a session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM category_hierarchy 
                WHERE session_id = ?
                ORDER BY level, path
            """,
                (session_id,),
            )

            return [dict(row) for row in cursor.fetchall()]

    def get_products_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        """Get all products in a category."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.*, cp.position, cp.featured
                FROM products p
                JOIN category_products cp ON p.id = cp.product_id
                WHERE cp.category_id = ?
                ORDER BY cp.position, p.name
            """,
                (category_id,),
            )

            return [dict(row) for row in cursor.fetchall()]

    def search_products(
        self, session_id: str, query: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search products by name, brand, or description."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM products 
                WHERE session_id = ? AND (
                    name LIKE ? OR 
                    brand LIKE ? OR 
                    description LIKE ?
                )
                ORDER BY name
                LIMIT ?
            """,
                (session_id, f"%{query}%", f"%{query}%", f"%{query}%", limit),
            )

            return [dict(row) for row in cursor.fetchall()]

    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent scraping sessions."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM session_stats 
                ORDER BY start_time DESC 
                LIMIT ?
            """,
                (limit,),
            )

            return [dict(row) for row in cursor.fetchall()]

    def cleanup_old_sessions(self, keep_days: int = 30):
        """Clean up old scraping sessions and their data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Find old sessions
            cursor.execute(
                """
                SELECT session_id FROM scraping_sessions 
                WHERE start_time < datetime('now', '-{} days')
            """.format(keep_days)
            )

            old_sessions = [row[0] for row in cursor.fetchall()]

            if old_sessions:
                placeholders = ",".join("?" * len(old_sessions))

                # Delete in correct order due to foreign keys
                cursor.execute(
                    f"""
                    DELETE FROM category_products 
                    WHERE category_id IN (
                        SELECT id FROM categories WHERE session_id IN ({placeholders})
                    )
                """,
                    old_sessions,
                )

                cursor.execute(
                    f"DELETE FROM products WHERE session_id IN ({placeholders})",
                    old_sessions,
                )
                cursor.execute(
                    f"DELETE FROM categories WHERE session_id IN ({placeholders})",
                    old_sessions,
                )
                cursor.execute(
                    f"DELETE FROM scraping_sessions WHERE session_id IN ({placeholders})",
                    old_sessions,
                )

                conn.commit()
                print(f"Cleaned up {len(old_sessions)} old sessions")


if __name__ == "__main__":
    # Test the database
    db = CostcoDatabase()

    # Start a test session
    session_id = db.start_scraping_session(ai_enabled=True, metadata={"test": True})

    # Add test category
    test_category = CategoryItem(
        name="Test Electronics",
        url="/electronics",
        category_type=CategoryType.NON_LEAF_NAV,
        description="Test category for electronics",
    )

    cat_id = db.save_category(session_id, test_category)
    print(f"Saved category with ID: {cat_id}")

    # Add test product
    test_product = {
        "name": "Test iPhone",
        "item_number": "TEST123",
        "price": 999.99,
        "brand": "Apple",
        "availability": "in_stock",
    }

    prod_id = db.save_product(session_id, test_product)
    print(f"Saved product with ID: {prod_id}")

    # Link them
    db.link_category_product(cat_id, prod_id, featured=True)

    # End session
    db.end_scraping_session(session_id)

    # Show stats
    stats = db.get_session_stats(session_id)
    print(f"Session stats: {stats}")
