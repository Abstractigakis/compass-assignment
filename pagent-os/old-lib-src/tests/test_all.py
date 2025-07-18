"""
Master test runner for all Costco scraping system components
Runs comprehensive tests for API, PAgent, Web Scraper, and Database
"""

import unittest
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all test modules
from test_costco_api import TestCostcoAPI
from test_pagent import TestPagent, TestPagentIntegration
from test_costco_web_scraper import TestCostcoWebScraper, TestCostcoWebScraperIntegration, TestCategoryInterface
from test_costco_database import TestCostcoDatabase


def create_test_suite():
    """Create comprehensive test suite for all components"""
    suite = unittest.TestSuite()
    
    # Database tests (foundational)
    print("📦 Adding Database Tests...")
    suite.addTest(unittest.makeSuite(TestCostcoDatabase))
    
    # PAgent tests (browser automation)
    print("🌐 Adding PAgent Tests...")
    suite.addTest(unittest.makeSuite(TestPagent))
    suite.addTest(unittest.makeSuite(TestPagentIntegration))
    
    # Web Scraper tests (core scraping logic)
    print("🏪 Adding Web Scraper Tests...")
    suite.addTest(unittest.makeSuite(TestCostcoWebScraper))
    suite.addTest(unittest.makeSuite(TestCostcoWebScraperIntegration))
    suite.addTest(unittest.makeSuite(TestCategoryInterface))
    
    # API tests (REST interface)
    print("🌐 Adding API Tests...")
    suite.addTest(unittest.makeSuite(TestCostcoAPI))
    
    return suite


def run_component_tests(component_name, test_classes):
    """Run tests for a specific component"""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING {component_name.upper()}")
    print(f"{'='*60}")
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        suite.addTest(unittest.makeSuite(test_class))
    
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    print(f"\n📊 {component_name} Test Results:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"   Duration: {end_time - start_time:.2f} seconds")
    
    if result.failures:
        print(f"   ❌ Failures:")
        for test, traceback in result.failures:
            print(f"      - {test}")
    
    if result.errors:
        print(f"   💥 Errors:")
        for test, traceback in result.errors:
            print(f"      - {test}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"   ✅ Success Rate: {success_rate:.1f}%")
    
    return result


def main():
    """Main test runner"""
    print("🏪 COSTCO SCRAPING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print("🧪 Testing API, PAgent, Web Scraper, and Database components")
    print("=" * 60)
    
    total_start_time = time.time()
    all_results = []
    
    # Test components individually
    test_components = [
        ("Database", [TestCostcoDatabase]),
        ("PAgent", [TestPagent, TestPagentIntegration]),
        ("Web Scraper", [TestCostcoWebScraper, TestCostcoWebScraperIntegration, TestCategoryInterface]),
        ("API", [TestCostcoAPI])
    ]
    
    for component_name, test_classes in test_components:
        try:
            result = run_component_tests(component_name, test_classes)
            all_results.append((component_name, result))
        except Exception as e:
            print(f"❌ Failed to run {component_name} tests: {e}")
            continue
    
    # Summary
    total_end_time = time.time()
    print(f"\n{'='*60}")
    print("📊 OVERALL TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    
    for component_name, result in all_results:
        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)
        total_skipped += len(result.skipped) if hasattr(result, 'skipped') else 0
        
        status = "✅ PASS" if (len(result.failures) + len(result.errors)) == 0 else "❌ FAIL"
        print(f"{status} {component_name}: {result.testsRun} tests")
    
    print(f"\n📈 Total Statistics:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {total_tests - total_failures - total_errors}")
    print(f"   Failed: {total_failures}")
    print(f"   Errors: {total_errors}")
    print(f"   Skipped: {total_skipped}")
    print(f"   Duration: {total_end_time - total_start_time:.2f} seconds")
    
    overall_success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
    print(f"   Overall Success Rate: {overall_success_rate:.1f}%")
    
    if overall_success_rate >= 90:
        print(f"\n🎉 EXCELLENT! System is in great shape!")
    elif overall_success_rate >= 75:
        print(f"\n👍 GOOD! Most components are working well.")
    elif overall_success_rate >= 50:
        print(f"\n⚠️  WARNING! Some significant issues detected.")
    else:
        print(f"\n🚨 CRITICAL! Major issues need attention.")
    
    print("\n" + "="*60)
    print("🏁 Test run completed!")
    
    # Exit with appropriate code
    exit_code = 0 if (total_failures + total_errors) == 0 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
