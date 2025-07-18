"""
Test suite for the Costco Database functionality
Tests database operations, schema, and data integrity
"""

import unittest
import sys
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from costco_database import CostcoDatabase
from category_interface import CategoryItem, CategoryType


class TestCostcoDatabase(unittest.TestCase):
    """Test suite for CostcoDatabase functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db = CostcoDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up after tests"""
        self.db.close()
        Path(self.temp_db.name).unlink(missing_ok=True)
    
    def test_database_initialization(self):
        """Test database initialization and schema creation"""
        # Check that database file exists
        self.assertTrue(Path(self.temp_db.name).exists())
        
        # Check that tables were created
        tables = self.db._get_table_names()
        expected_tables = ['sessions', 'categories', 'products']
        for table in expected_tables:
            self.assertIn(table, tables)
    
    def test_start_scraping_session(self):
        """Test starting a new scraping session"""
        metadata = {"test": True, "version": "1.0"}
        session_id = self.db.start_scraping_session(metadata=metadata)
        
        self.assertIsNotNone(session_id)
        self.assertTrue(session_id.startswith("session_"))
        
        # Verify session was saved
        sessions = self.db.get_recent_sessions(1)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]['session_id'], session_id)
        self.assertEqual(sessions[0]['status'], 'running')
    
    def test_end_scraping_session(self):
        """Test ending a scraping session"""
        session_id = self.db.start_scraping_session()
        
        # End the session
        self.db.end_scraping_session(session_id)
        
        # Verify session status changed
        sessions = self.db.get_recent_sessions(1)
        self.assertEqual(sessions[0]['status'], 'completed')
        self.assertIsNotNone(sessions[0]['end_time'])
    
    def test_save_category(self):
        """Test saving category data"""
        session_id = self.db.start_scraping_session()
        
        category = CategoryItem(
            name="Test Electronics",
            url="/test-electronics",
            category_type=CategoryType.LEAF_PRODUCT,
            description="Test electronics category",
            is_leaf=True,
            level=1,
            path="Electronics > Test Electronics",
            parent_id=None,
            metadata={"test": True}
        )
        
        category_id = self.db.save_category(session_id, category)
        self.assertIsNotNone(category_id)
        self.assertIsInstance(category_id, int)
        
        # Verify category was saved
        categories = self.db.get_categories_by_session(session_id)
        self.assertEqual(len(categories), 1)
        saved_category = categories[0]
        
        self.assertEqual(saved_category['name'], "Test Electronics")
        self.assertEqual(saved_category['url'], "/test-electronics")
        self.assertEqual(saved_category['category_type'], "leaf_product")
        self.assertEqual(saved_category['is_leaf'], True)
    
    def test_save_product(self):
        """Test saving product data"""
        session_id = self.db.start_scraping_session()
        
        # Create and save a category first
        category = CategoryItem(
            name="Test Electronics",
            url="/test-electronics",
            category_type=CategoryType.LEAF_PRODUCT
        )
        category_id = self.db.save_category(session_id, category)
        
        # Create product data
        product_data = {
            "name": "Test MacBook Pro",
            "item_number": "TEST001",
            "price": 2499.99,
            "currency": "CAD",
            "brand": "Apple",
            "availability": "in_stock",
            "rating": 4.5,
            "review_count": 150,
            "description": "Test MacBook Pro description",
            "image_url": "https://example.com/image.jpg",
            "features": ["Feature 1", "Feature 2"],
            "specifications": {"RAM": "16GB", "Storage": "512GB"}
        }
        
        product_id = self.db.save_product(session_id, category_id, product_data)
        self.assertIsNotNone(product_id)
        self.assertIsInstance(product_id, int)
        
        # Verify product was saved
        products = self.db.get_products_by_session(session_id)
        self.assertEqual(len(products), 1)
        saved_product = products[0]
        
        self.assertEqual(saved_product['name'], "Test MacBook Pro")
        self.assertEqual(saved_product['price'], 2499.99)
        self.assertEqual(saved_product['brand'], "Apple")
        self.assertEqual(saved_product['category_id'], category_id)
    
    def test_get_categories_by_session(self):
        """Test retrieving categories by session"""
        session_id = self.db.start_scraping_session()
        
        # Save multiple categories
        categories = [
            CategoryItem("Electronics", "/electronics", CategoryType.NON_LEAF_NAVIGATION),
            CategoryItem("Computers", "/computers", CategoryType.LEAF_PRODUCT),
            CategoryItem("Phones", "/phones", CategoryType.LEAF_PRODUCT)
        ]
        
        for category in categories:
            self.db.save_category(session_id, category)
        
        # Retrieve and verify
        saved_categories = self.db.get_categories_by_session(session_id)
        self.assertEqual(len(saved_categories), 3)
        
        names = [cat['name'] for cat in saved_categories]
        self.assertIn("Electronics", names)
        self.assertIn("Computers", names)
        self.assertIn("Phones", names)
    
    def test_get_products_by_category(self):
        """Test retrieving products by category"""
        session_id = self.db.start_scraping_session()
        
        # Create category
        category = CategoryItem("Electronics", "/electronics", CategoryType.LEAF_PRODUCT)
        category_id = self.db.save_category(session_id, category)
        
        # Save multiple products
        products = [
            {"name": "MacBook Pro", "price": 2499.99, "brand": "Apple"},
            {"name": "Dell XPS", "price": 1999.99, "brand": "Dell"},
            {"name": "Surface Pro", "price": 1799.99, "brand": "Microsoft"}
        ]
        
        for product in products:
            self.db.save_product(session_id, category_id, product)
        
        # Retrieve and verify
        saved_products = self.db.get_products_by_category(category_id)
        self.assertEqual(len(saved_products), 3)
        
        names = [prod['name'] for prod in saved_products]
        self.assertIn("MacBook Pro", names)
        self.assertIn("Dell XPS", names)
        self.assertIn("Surface Pro", names)
    
    def test_search_products(self):
        """Test product search functionality"""
        session_id = self.db.start_scraping_session()
        
        # Create category
        category = CategoryItem("Electronics", "/electronics", CategoryType.LEAF_PRODUCT)
        category_id = self.db.save_category(session_id, category)
        
        # Save products with different names and brands
        products = [
            {"name": "MacBook Pro 16", "brand": "Apple", "price": 2499.99},
            {"name": "MacBook Air", "brand": "Apple", "price": 1299.99},
            {"name": "Dell XPS 13", "brand": "Dell", "price": 1999.99},
            {"name": "Surface Laptop", "brand": "Microsoft", "price": 1799.99}
        ]
        
        for product in products:
            self.db.save_product(session_id, category_id, product)
        
        # Test search by name
        results = self.db.search_products("MacBook")
        self.assertEqual(len(results), 2)
        
        # Test search by brand
        results = self.db.search_products("Apple")
        self.assertEqual(len(results), 2)
        
        # Test search with no results
        results = self.db.search_products("Nintendo")
        self.assertEqual(len(results), 0)
    
    def test_get_database_stats(self):
        """Test database statistics collection"""
        session_id1 = self.db.start_scraping_session()
        session_id2 = self.db.start_scraping_session()
        
        # Add some test data
        category = CategoryItem("Electronics", "/electronics", CategoryType.LEAF_PRODUCT)
        category_id = self.db.save_category(session_id1, category)
        
        product = {"name": "Test Product", "price": 99.99}
        self.db.save_product(session_id1, category_id, product)
        
        # Get stats
        stats = self.db.get_database_stats()
        
        self.assertIn("total_sessions", stats)
        self.assertIn("total_categories", stats)
        self.assertIn("total_products", stats)
        self.assertIn("database_size_bytes", stats)
        
        self.assertEqual(stats["total_sessions"], 2)
        self.assertEqual(stats["total_categories"], 1)
        self.assertEqual(stats["total_products"], 1)
        self.assertGreater(stats["database_size_bytes"], 0)
    
    def test_cleanup_old_sessions(self):
        """Test cleanup of old sessions"""
        # Create some sessions
        session1 = self.db.start_scraping_session()
        session2 = self.db.start_scraping_session()
        
        # Manually update one session to be old
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE sessions 
                SET start_time = datetime('now', '-60 days')
                WHERE session_id = ?
            """, (session1,))
        
        # Test cleanup (keeping last 30 days)
        cleaned = self.db.cleanup_old_sessions(days_to_keep=30)
        self.assertGreater(cleaned, 0)
        
        # Verify old session was removed
        recent_sessions = self.db.get_recent_sessions(10)
        session_ids = [s['session_id'] for s in recent_sessions]
        self.assertNotIn(session1, session_ids)
        self.assertIn(session2, session_ids)
    
    def test_export_session_data(self):
        """Test exporting session data"""
        session_id = self.db.start_scraping_session()
        
        # Add test data
        category = CategoryItem("Electronics", "/electronics", CategoryType.LEAF_PRODUCT)
        category_id = self.db.save_category(session_id, category)
        
        product = {"name": "Test Product", "price": 99.99, "brand": "TestBrand"}
        self.db.save_product(session_id, category_id, product)
        
        # Export data
        export_data = self.db.export_session_data(session_id)
        
        self.assertIn("session", export_data)
        self.assertIn("categories", export_data)
        self.assertIn("products", export_data)
        
        self.assertEqual(export_data["session"]["session_id"], session_id)
        self.assertEqual(len(export_data["categories"]), 1)
        self.assertEqual(len(export_data["products"]), 1)
        self.assertEqual(export_data["products"][0]["name"], "Test Product")
    
    def test_database_connection_context_manager(self):
        """Test database connection context manager"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM sessions")
            count = cursor.fetchone()[0]
            self.assertIsInstance(count, int)
    
    def test_database_error_handling(self):
        """Test database error handling"""
        # Test invalid session ID
        result = self.db.get_categories_by_session("invalid_session_id")
        self.assertEqual(len(result), 0)
        
        # Test invalid category ID
        result = self.db.get_products_by_category(99999)
        self.assertEqual(len(result), 0)
    
    def test_concurrent_operations(self):
        """Test concurrent database operations"""
        import threading
        import time
        
        results = []
        errors = []
        
        def create_session(i):
            try:
                session_id = self.db.start_scraping_session(metadata={"thread": i})
                results.append(session_id)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_session, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)
        self.assertEqual(len(set(results)), 5)  # All session IDs should be unique


if __name__ == "__main__":
    print("🧪 Running Costco Database Test Suite")
    print("=" * 50)
    
    # Run tests with verbose output
    unittest.main(verbosity=2, buffer=True)
