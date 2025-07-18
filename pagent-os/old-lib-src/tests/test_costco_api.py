"""
Test suite for the Costco API functionality
Tests all endpoints, error handling, and data validation
"""

import unittest
import requests
import json
import time
import threading
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestCostcoAPI(unittest.TestCase):
    """Test suite for the Costco REST API"""
    
    BASE_URL = "http://localhost:5001"
    api_process = None
    
    @classmethod
    def setUpClass(cls):
        """Start API server before running tests"""
        print("🚀 Starting API server for testing...")
        # Check if API is already running
        try:
            response = requests.get(f"{cls.BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✅ API server already running")
                return
        except requests.exceptions.RequestException:
            pass
        
        # Start API server in background
        cls.api_process = subprocess.Popen([
            sys.executable, "costco_api.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for API to start
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get(f"{cls.BASE_URL}/health", timeout=1)
                if response.status_code == 200:
                    print("✅ API server started successfully")
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)
        else:
            raise Exception("Failed to start API server")
    
    @classmethod
    def tearDownClass(cls):
        """Stop API server after tests"""
        if cls.api_process:
            cls.api_process.terminate()
            cls.api_process.wait()
            print("🔄 API server stopped")
    
    def test_health_endpoint(self):
        """Test API health check"""
        response = requests.get(f"{self.BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("database", data)
        self.assertEqual(data["status"], "healthy")
    
    def test_sessions_list(self):
        """Test sessions listing endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/v1/sessions")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        if data:  # If sessions exist
            session = data[0]
            required_fields = ["session_id", "start_time", "status"]
            for field in required_fields:
                self.assertIn(field, session)
    
    def test_sessions_with_limit(self):
        """Test sessions with limit parameter"""
        response = requests.get(f"{self.BASE_URL}/api/v1/sessions?limit=3")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertLessEqual(len(data), 3)
    
    def test_categories_list(self):
        """Test categories listing endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/v1/categories")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        if data:  # If categories exist
            category = data[0]
            required_fields = ["id", "name", "category_type"]
            for field in required_fields:
                self.assertIn(field, category)
    
    def test_categories_hierarchy(self):
        """Test categories hierarchy endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/v1/categories/hierarchy")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
    
    def test_products_list(self):
        """Test products listing endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/v1/products")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        if data:  # If products exist
            product = data[0]
            required_fields = ["id", "name", "price"]
            for field in required_fields:
                self.assertIn(field, product)
    
    def test_products_search(self):
        """Test product search functionality"""
        response = requests.get(f"{self.BASE_URL}/api/v1/products/search?q=test")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("total_results", data)
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)
    
    def test_products_search_empty_query(self):
        """Test product search with empty query"""
        response = requests.get(f"{self.BASE_URL}/api/v1/products/search")
        self.assertEqual(response.status_code, 400)
    
    def test_database_stats(self):
        """Test database statistics endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/v1/stats/database")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        required_fields = ["total_sessions", "total_categories", "total_products"]
        for field in required_fields:
            self.assertIn(field, data)
            self.assertIsInstance(data[field], int)
    
    def test_category_stats(self):
        """Test category statistics endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/v1/stats/categories")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("type_distribution", data)
        self.assertIn("leaf_distribution", data)
    
    def test_product_stats(self):
        """Test product statistics endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/v1/stats/products")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("price_statistics", data)
    
    def test_system_health(self):
        """Test system health endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/v1/system/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "healthy")
    
    def test_invalid_endpoint(self):
        """Test invalid endpoint returns 404"""
        response = requests.get(f"{self.BASE_URL}/api/v1/invalid")
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_session_id(self):
        """Test invalid session ID returns 404"""
        response = requests.get(f"{self.BASE_URL}/api/v1/sessions/invalid_session")
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_category_id(self):
        """Test invalid category ID returns 404"""
        response = requests.get(f"{self.BASE_URL}/api/v1/categories/99999")
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_product_id(self):
        """Test invalid product ID returns 404"""
        response = requests.get(f"{self.BASE_URL}/api/v1/products/99999")
        self.assertEqual(response.status_code, 404)
    
    def test_products_with_filters(self):
        """Test products with price filters"""
        response = requests.get(f"{self.BASE_URL}/api/v1/products?min_price=100&max_price=5000")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
    
    def test_swagger_docs_accessible(self):
        """Test that Swagger documentation is accessible"""
        response = requests.get(f"{self.BASE_URL}/docs/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))


if __name__ == "__main__":
    print("🧪 Running Costco API Test Suite")
    print("=" * 50)
    
    # Run tests with verbose output
    unittest.main(verbosity=2, buffer=True)
