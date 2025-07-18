"""
Test suite for the Costco Web Scraper functionality
Tests scraping logic, category detection, and product extraction
"""

import unittest
import sys
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from costco_web_scraper import CostcoWebScraper, create_costco_scraper
from category_interface import CategoryItem, CategoryType


class TestCostcoWebScraper(unittest.TestCase):
    """Test suite for CostcoWebScraper functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.scraper = CostcoWebScraper(
            base_url="https://www.costco.ca",
            output_dir=self.temp_dir,
            gemini_api_key=None  # Disable AI for basic tests
        )
    
    def tearDown(self):
        """Clean up after tests"""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        if hasattr(self.scraper, 'pagent') and self.scraper.pagent:
            try:
                self.scraper.pagent.close()
            except:
                pass
    
    def test_scraper_initialization(self):
        """Test scraper initialization"""
        self.assertEqual(self.scraper.base_url, "https://www.costco.ca")
        self.assertEqual(self.scraper.output_dir, self.temp_dir)
        self.assertIsNone(self.scraper.gemini_api_key)
        self.assertIsNone(self.scraper.pagent)
    
    def test_create_costco_scraper_function(self):
        """Test the factory function for creating scrapers"""
        scraper = create_costco_scraper(gemini_api_key=None)
        self.assertIsInstance(scraper, CostcoWebScraper)
        self.assertEqual(scraper.base_url, "https://www.costco.ca")
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        test_cases = [
            ("Electronics & Computers", "electronics_computers"),
            ("Home & Garden", "home_garden"),
            ("Special/Chars!@#", "special_chars"),
            ("  Spaces  ", "spaces"),
            ("MixedCASE", "mixedcase")
        ]
        
        for input_name, expected in test_cases:
            result = self.scraper._sanitize_filename(input_name)
            self.assertEqual(result, expected)
    
    def test_extract_category_info_basic(self):
        """Test basic category information extraction"""
        # Mock HTML with category links
        mock_html = """
        <html>
            <body>
                <div class="category-list">
                    <a href="/electronics">Electronics</a>
                    <a href="/home-garden">Home & Garden</a>
                    <a href="/clothing">Clothing</a>
                </div>
            </body>
        </html>
        """
        
        with patch.object(self.scraper, '_get_page_html', return_value=mock_html):
            categories = self.scraper._extract_category_info("https://www.costco.ca")
            
            self.assertIsInstance(categories, list)
            self.assertGreater(len(categories), 0)
    
    def test_is_leaf_category_detection(self):
        """Test leaf category detection logic"""
        # Mock product page HTML
        product_html = """
        <html>
            <body>
                <div class="product-list">
                    <div class="product-item">Product 1</div>
                    <div class="product-item">Product 2</div>
                </div>
                <div class="price">$99.99</div>
            </body>
        </html>
        """
        
        # Mock navigation page HTML
        navigation_html = """
        <html>
            <body>
                <div class="category-nav">
                    <a href="/subcategory1">Sub Category 1</a>
                    <a href="/subcategory2">Sub Category 2</a>
                </div>
            </body>
        </html>
        """
        
        with patch.object(self.scraper, '_get_page_html') as mock_get_html:
            # Test product page (should be leaf)
            mock_get_html.return_value = product_html
            is_leaf = self.scraper._is_leaf_category("https://www.costco.ca/electronics")
            self.assertTrue(is_leaf)
            
            # Test navigation page (should not be leaf)
            mock_get_html.return_value = navigation_html
            is_leaf = self.scraper._is_leaf_category("https://www.costco.ca/categories")
            self.assertFalse(is_leaf)
    
    def test_extract_products_from_page(self):
        """Test product extraction from HTML"""
        mock_html = """
        <html>
            <body>
                <div class="product-tile">
                    <h3>Test Product 1</h3>
                    <span class="price">$199.99</span>
                    <div class="item-number">Item #12345</div>
                </div>
                <div class="product-tile">
                    <h3>Test Product 2</h3>
                    <span class="price">$299.99</span>
                    <div class="item-number">Item #67890</div>
                </div>
            </body>
        </html>
        """
        
        with patch.object(self.scraper, '_get_page_html', return_value=mock_html):
            products = self.scraper._extract_products_from_page("https://www.costco.ca/electronics")
            
            self.assertIsInstance(products, list)
            # Note: Actual extraction depends on the implementation
            # This test ensures the method runs without error
    
    def test_save_page_request(self):
        """Test saving page request data"""
        test_data = {
            "url": "https://www.costco.ca/test",
            "html": "<html><body>Test</body></html>",
            "products": [{"name": "Test Product", "price": "$99.99"}]
        }
        
        request_id = self.scraper._save_page_request(
            url=test_data["url"],
            html=test_data["html"],
            products=test_data["products"],
            request_type="category_test"
        )
        
        self.assertIsNotNone(request_id)
        
        # Verify files were created
        request_dir = Path(self.temp_dir) / "page_requests" / request_id
        self.assertTrue(request_dir.exists())
        self.assertTrue((request_dir / "meta.json").exists())
        self.assertTrue((request_dir / "page.html").exists())
        self.assertTrue((request_dir / "products.json").exists())
        
        # Verify content
        with open(request_dir / "meta.json") as f:
            meta = json.load(f)
            self.assertEqual(meta["url"], test_data["url"])
        
        with open(request_dir / "products.json") as f:
            products = json.load(f)
            self.assertEqual(len(products), 1)
            self.assertEqual(products[0]["name"], "Test Product")
    
    def test_get_stats(self):
        """Test statistics collection"""
        # Create some test request data
        test_requests = [
            ("sitemap", "https://www.costco.ca", "<html>1</html>", []),
            ("category", "https://www.costco.ca/electronics", "<html>2</html>", [{"name": "Product"}])
        ]
        
        for req_type, url, html, products in test_requests:
            self.scraper._save_page_request(url, html, products, req_type)
        
        stats = self.scraper.get_stats()
        
        self.assertIn("total_requests", stats)
        self.assertIn("request_types", stats)
        self.assertIn("db_size_mb", stats)
        self.assertEqual(stats["total_requests"], 2)
        self.assertIn("sitemap", stats["request_types"])
        self.assertIn("category", stats["request_types"])
    
    @patch('costco_web_scraper.PAgent')
    def test_scraper_with_mocked_pagent(self, mock_pagent_class):
        """Test scraper with mocked PAgent"""
        # Setup mock
        mock_pagent = Mock()
        mock_pagent_class.return_value = mock_pagent
        mock_pagent.navigate.return_value = True
        mock_pagent.get_html.return_value = "<html><body>Mock page</body></html>"
        
        # Test scraper initialization with PAgent
        scraper = CostcoWebScraper(
            base_url="https://www.costco.ca",
            output_dir=self.temp_dir
        )
        
        # Test getting page HTML
        html = scraper._get_page_html("https://www.costco.ca")
        self.assertEqual(html, "<html><body>Mock page</body></html>")
        
        # Verify PAgent was used
        mock_pagent.navigate.assert_called_with("https://www.costco.ca")
        mock_pagent.get_html.assert_called_once()


class TestCostcoWebScraperIntegration(unittest.TestCase):
    """Integration tests for the scraper with real components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up after tests"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_scraper_category_processing(self):
        """Test end-to-end category processing"""
        scraper = CostcoWebScraper(
            base_url="https://www.costco.ca",
            output_dir=self.temp_dir,
            gemini_api_key=None
        )
        
        # Mock the category extraction to return test data
        test_categories = [
            CategoryItem(
                name="Test Electronics",
                url="/test-electronics",
                category_type=CategoryType.LEAF_PRODUCT,
                description="Test electronics category"
            )
        ]
        
        with patch.object(scraper, '_extract_category_info', return_value=test_categories):
            with patch.object(scraper, '_get_page_html', return_value="<html>Test</html>"):
                with patch.object(scraper, '_is_leaf_category', return_value=True):
                    with patch.object(scraper, '_extract_products_from_page', return_value=[]):
                        
                        # Test processing categories
                        result = scraper.get_all_products_for_all_categories(max_categories=1)
                        
                        self.assertIn("categories_processed", result)
                        self.assertIn("total_products", result)
                        self.assertEqual(result["categories_processed"], 1)
    
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'})
    def test_scraper_with_ai_key(self):
        """Test scraper initialization with AI key"""
        scraper = create_costco_scraper()
        self.assertEqual(scraper.gemini_api_key, 'test_key')
    
    def test_scraper_error_handling(self):
        """Test scraper error handling"""
        scraper = CostcoWebScraper(
            base_url="https://invalid-url-that-does-not-exist.com",
            output_dir=self.temp_dir
        )
        
        # Test handling of invalid URLs
        with patch.object(scraper, '_get_page_html', side_effect=Exception("Network error")):
            # Should handle errors gracefully
            try:
                result = scraper.get_all_products_for_all_categories(max_categories=1)
                # Should return some result even with errors
                self.assertIsInstance(result, dict)
            except Exception as e:
                # If it raises an exception, it should be handled gracefully
                self.fail(f"Scraper should handle errors gracefully: {e}")


class TestCategoryInterface(unittest.TestCase):
    """Test the category interface compliance"""
    
    def test_category_item_creation(self):
        """Test CategoryItem creation and validation"""
        category = CategoryItem(
            name="Test Category",
            url="/test-category",
            category_type=CategoryType.LEAF_PRODUCT,
            description="A test category"
        )
        
        self.assertEqual(category.name, "Test Category")
        self.assertEqual(category.url, "/test-category")
        self.assertEqual(category.category_type, CategoryType.LEAF_PRODUCT)
        self.assertEqual(category.description, "A test category")
    
    def test_category_type_enum(self):
        """Test CategoryType enum values"""
        self.assertEqual(CategoryType.LEAF_PRODUCT.value, "leaf_product")
        self.assertEqual(CategoryType.NON_LEAF_NAVIGATION.value, "non_leaf_navigation")
        self.assertEqual(CategoryType.AMBIGUOUS.value, "ambiguous")
        self.assertEqual(CategoryType.ERROR.value, "error")
    
    def test_category_item_dict_conversion(self):
        """Test CategoryItem to dict conversion"""
        category = CategoryItem(
            name="Test Category",
            url="/test-category",
            category_type=CategoryType.LEAF_PRODUCT,
            description="A test category",
            metadata={"test": "value"}
        )
        
        category_dict = category.to_dict()
        
        self.assertIn("name", category_dict)
        self.assertIn("url", category_dict)
        self.assertIn("category_type", category_dict)
        self.assertIn("description", category_dict)
        self.assertIn("metadata", category_dict)
        
        self.assertEqual(category_dict["name"], "Test Category")
        self.assertEqual(category_dict["category_type"], "leaf_product")


if __name__ == "__main__":
    print("🧪 Running Costco Web Scraper Test Suite")
    print("=" * 50)
    
    # Run tests with verbose output
    unittest.main(verbosity=2, buffer=True)
