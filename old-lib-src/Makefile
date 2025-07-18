# Costco Web Scraper Makefile
# Provides convenient commands for running the # Analysis & Results
analyze:
	@echo "📊 Analyzing extraction results..."
	python analyze_results.py

validate-categories:
	@echo "🔍 Validating category interface compliance..."
	python validate_categories.py

show-stats:r and tests

.PHONY: help setup install clean test test-all run run-full run-limited analyze deps check-env

# Default target
help:
	@echo "🏪 Costco Web Scraper - Available Commands"
	@echo "=============================================="
	@echo ""
	@echo "🚀 Setup & Installation:"
	@echo "  make setup         - Setup environment and install dependencies"
	@echo "  make install       - Install Python dependencies"
	@echo "  make check-env     - Check environment configuration"
	@echo "  make deps          - Check dependency status"
	@echo ""
	@echo "🤖 Running the Scraper:"
	@echo "  make run           - Run scraper with 10 categories (default)"
	@echo "  make run-limited   - Run scraper with 5 categories (quick test)"
	@echo "  make run-full      - Run scraper with ALL categories (⚠️  takes hours)"
	@echo "  make run-traditional - Run without AI (traditional extraction)"
	@echo ""
	@echo "📊 Analysis & Results:"
	@echo "  make analyze       - Analyze extraction results"
	@echo "  make validate-categories - Validate category interface compliance"
	@echo "  make show-stats    - Show scraping statistics"
	@echo "  make show-products - Show sample extracted products"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test          - Run comprehensive test suite for all components"
	@echo "  make test-all      - Run all component tests (same as test)"
	@echo "  make test-api      - Test REST API functionality"
	@echo "  make test-pagent   - Test PAgent (browser automation)"
	@echo "  make test-scraper  - Test web scraper functionality"
	@echo "  make test-database - Test database functionality"
	@echo "  make test-ai       - Test AI functionality (requires API key)"
	@echo ""
	@echo "🗄️  Database & Service:"
	@echo "  make run-service   - Run scraping with database storage"
	@echo "  make init-db       - Initialize database with schema"
	@echo "  make db-stats      - Show database statistics"
	@echo "  make export-data   - Export latest session data"
	@echo "  make cleanup-db    - Clean up old database sessions"
	@echo ""
	@echo "🌐 REST API:"
	@echo "  make run-api       - Start Flask API server"
	@echo "  make api-docs      - Open API documentation in browser"
	@echo "  make test-api      - Test API endpoints"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean         - Clean temporary files and cache"
	@echo "  make clean-db      - Clean database files (extracted data)"
	@echo "  make clean-all     - Clean everything including venv"
	@echo ""

# Setup and installation
setup:
	@echo "🛠️  Setting up Costco Web Scraper..."
	python setup.py

install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

check-env:
	@echo "🔍 Checking environment configuration..."
	@python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ GEMINI_API_KEY configured' if os.getenv('GEMINI_API_KEY') and os.getenv('GEMINI_API_KEY') != 'your_gemini_api_key_here' else '❌ GEMINI_API_KEY not configured - check .env file')"

deps:
	@echo "📋 Checking dependencies..."
	@python -c "import sys; packages=['requests', 'bs4', 'playwright', 'dotenv', 'google.generativeai']; [print(f'✅ {p}') if __import__(p) else print(f'❌ {p}') for p in packages]" 2>/dev/null || echo "❌ Some dependencies missing - run 'make install'"

# Running the scraper
run:
	@echo "🚀 Running Costco Web Scraper (10 categories)..."
	python costco_web_scraper.py

run-limited:
	@echo "🧪 Running Costco Web Scraper (5 categories - quick test)..."
	@python -c "from costco_web_scraper import create_costco_scraper; scraper = create_costco_scraper(); result = scraper.scrape_all_categories_with_ai_extraction(max_categories=5); print(f'✅ Completed: {result[\"successful_extractions\"]}/{result[\"categories_processed\"]} categories')"

run-full:
	@echo "⚠️  Running Costco Web Scraper with ALL categories (this may take hours)..."
	@echo "Press Ctrl+C to cancel within 5 seconds..."
	@sleep 5
	@python -c "from costco_web_scraper import create_costco_scraper; scraper = create_costco_scraper(); result = scraper.scrape_all_categories_with_ai_extraction(); print(f'🎉 Full scrape completed: {result[\"successful_extractions\"]}/{result[\"categories_processed\"]} categories')"

run-traditional:
	@echo "🔧 Running traditional scraper (without AI)..."
	@python -c "from costco_web_scraper import create_costco_scraper; scraper = create_costco_scraper(gemini_api_key=None); result = scraper.get_all_products_for_all_categories(max_categories=10); print(f'✅ Traditional extraction: {result[\"total_products\"]} products found')"

# Analysis and results
analyze:
	@echo "📊 Analyzing extraction results..."
	python analyze_results.py

show-stats:
	@echo "📈 Scraper Statistics:"
	@python -c "from costco_web_scraper import create_costco_scraper; scraper = create_costco_scraper(); stats = scraper.get_stats(); print(f'📂 Total requests: {stats.get(\"total_requests\", 0)}'); print(f'💾 DB size: {stats.get(\"db_size_mb\", 0):.1f} MB'); print(f'🗂️  Request types: {stats.get(\"request_types\", {})}')"

show-products:
	@echo "🛒 Sample Products Found:"
	@python -c "import json; from pathlib import Path; [print(f'📋 {f.parent.name}: {len(json.load(open(f)))} products') for f in Path('db/page_requests').glob('*/products.json') if f.exists()][:5]" 2>/dev/null || echo "No products found yet - run scraper first"

# Testing
test:
	@echo "🧪 Running comprehensive test suite..."
	python tests/test_all.py

test-all:
	@echo "🧪 Running all component tests..."
	python tests/test_all.py

test-api:
	@echo "🌐 Testing API functionality..."
	python tests/test_costco_api.py

test-pagent:
	@echo "🌐 Testing PAgent functionality..."
	python tests/test_pagent.py

test-scraper:
	@echo "🏪 Testing web scraper functionality..."
	python tests/test_costco_web_scraper.py

test-database:
	@echo "🗄️  Testing database functionality..."
	python tests/test_costco_database.py

test-ai:
	@echo "🤖 Testing AI functionality..."
	@echo "⚠️  AI tests require GEMINI_API_KEY to be configured"
	python -c "from costco_web_scraper import create_costco_scraper; scraper = create_costco_scraper(); print('✅ AI initialization successful' if scraper.gemini_api_key else '❌ No API key configured')"

test-is-leaf:
	@echo "🍃 Testing leaf detection..."
	python tests/test_costco_web_scraper.py TestCostcoWebScraper.test_is_leaf_category_detection

# Maintenance and cleanup
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned temporary files"

clean-db:
	@echo "🗑️  Cleaning database files..."
	@echo "⚠️  This will delete all extracted data. Continue? (y/N)"
	@read -r confirm && [ "$$confirm" = "y" ] && rm -rf db/ && echo "✅ Database cleaned" || echo "❌ Cancelled"

clean-all: clean clean-db
	@echo "🗑️  Cleaning everything including virtual environment..."
	@echo "⚠️  This will delete venv and all data. Continue? (y/N)"
	@read -r confirm && [ "$$confirm" = "y" ] && rm -rf venv/ && echo "✅ Full cleanup completed" || echo "❌ Cancelled"

# Development shortcuts
dev-setup: install check-env
	@echo "🛠️  Development environment ready!"

quick-test: test-scraper analyze
	@echo "✅ Quick test completed"

demo: run-limited analyze
	@echo "🎬 Demo completed - check results above!"

# Health check
health:
	@echo "🏥 System Health Check:"
	@echo "Environment: $$(python --version)"
	@echo "Dependencies:"
	@make deps
	@echo "API Key:"
	@make check-env
	@echo "Database:"
	@ls -la db/ 2>/dev/null && echo "✅ Database exists" || echo "❌ No database found"

# Database and Service operations
run-service:
	@echo "🚀 Running Costco scraper with database storage..."
	python costco_service.py

run-service-limited:
	@echo "🚀 Running limited Costco scraper with database storage..."
	python -c "from costco_service import CostcoService; s = CostcoService(); s.scrape_categories(categories_limit=5); s.end_scraping_session()"

init-db:
	@echo "🗄️  Initializing Costco database..."
	python -c "from costco_database import CostcoDatabase; CostcoDatabase()"
	@echo "✅ Database initialized"

db-stats:
	@echo "📊 Database Statistics:"
	python -c "from costco_service import CostcoService; import json; s = CostcoService(); stats = s.get_database_stats(); print(json.dumps(stats, indent=2, default=str))"

export-data:
	@echo "📁 Exporting latest session data..."
	python -c "from costco_service import CostcoService; s = CostcoService(); sessions = s.db.get_recent_sessions(1); print('Latest session:', sessions[0]['session_id'] if sessions else 'No sessions found'); s.export_session_data(sessions[0]['session_id']) if sessions else None"

export-session:
	@echo "📁 Export specific session (usage: make export-session SESSION_ID=your_session_id)"
	@if [ -z "$(SESSION_ID)" ]; then echo "❌ Please provide SESSION_ID parameter"; else python -c "from costco_service import CostcoService; s = CostcoService(); s.export_session_data('$(SESSION_ID)')"; fi

cleanup-db:
	@echo "🧹 Cleaning up old database sessions (keeping last 30 days)..."
	python -c "from costco_service import CostcoService; s = CostcoService(); s.cleanup_old_data()"

test-database:
	@echo "🧪 Testing database functionality..."
	python -c "from costco_database import CostcoDatabase; from category_interface import CategoryItem, CategoryType; db = CostcoDatabase(); print('✅ Database connection working'); session = db.start_scraping_session(metadata={'test': True}); cat = CategoryItem('Test Category', category_type=CategoryType.LEAF_PRODUCT); cat_id = db.save_category(session, cat); print(f'✅ Category saved with ID: {cat_id}'); db.end_scraping_session(session); print('✅ Database test completed')"

test-service:
	@echo "🧪 Testing Costco service..."
	python -c "from costco_service import CostcoService; s = CostcoService(); print('✅ Service initialized'); stats = s.get_database_stats(); print(f'Database contains {stats[\"total_sessions\"]} sessions'); print('✅ Service test completed')"

test-integration:
	@echo "🧪 Running complete integration test..."
	python test_integration.py

test-system: test-database test-service test-integration
	@echo "✅ All system tests completed successfully!"

# REST API operations
run-api:
	@echo "🌐 Starting Costco Database API server..."
	@echo "📚 Swagger docs will be available at: http://localhost:5000/docs/"
	@echo "🏥 Health check at: http://localhost:5000/health"
	python costco_api.py

run-api-background:
	@echo "🌐 Starting API server in background..."
	python costco_api.py &
	@echo "API server started in background"

api-docs:
	@echo "📚 Opening API documentation..."
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:5001/docs/; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:5001/docs/; \
	else \
		echo "Please open http://localhost:5001/docs/ in your browser"; \
	fi

test-api:
	@echo "🧪 Testing API endpoints..."
	python test_api.py

api-health:
	@echo "🏥 Checking API health..."
	@curl -s http://localhost:5001/health | python -m json.tool || echo "❌ API server not responding"

install-api:
	@echo "📦 Installing API dependencies..."
	pip install flask flask-restx werkzeug
	@echo "✅ API dependencies installed"
