#!/usr/bin/env python3
"""
Costco Database CLI Tool

Command-line interface for managing the Costco database and running scraping operations.
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Optional

from costco_service import CostcoService
from costco_database import CostcoDatabase


def main():
    parser = argparse.ArgumentParser(description="Costco Database CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    scrape_parser = subparsers.add_parser(
        "scrape", help="Run scraping with database storage"
    )
    scrape_parser.add_argument("--limit", type=int, help="Limit number of categories")
    scrape_parser.add_argument(
        "--categories", nargs="+", help="Specific categories to scrape"
    )
    scrape_parser.add_argument(
        "--no-ai", action="store_true", help="Disable AI extraction"
    )

    # Database commands
    subparsers.add_parser("init", help="Initialize database")
    subparsers.add_parser("stats", help="Show database statistics")

    # Session commands
    sessions_parser = subparsers.add_parser("sessions", help="List recent sessions")
    sessions_parser.add_argument(
        "--limit", type=int, default=10, help="Number of sessions to show"
    )

    export_parser = subparsers.add_parser("export", help="Export session data")
    export_parser.add_argument(
        "session_id", nargs="?", help="Session ID to export (latest if not specified)"
    )
    export_parser.add_argument(
        "--format", default="json", choices=["json"], help="Export format"
    )

    # Search commands
    search_parser = subparsers.add_parser("search", help="Search products")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--session", help="Session ID to search in")

    # Cleanup commands
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old data")
    cleanup_parser.add_argument(
        "--days", type=int, default=30, help="Keep data from last N days"
    )

    # Category commands
    categories_parser = subparsers.add_parser("categories", help="Show categories")
    categories_parser.add_argument("session_id", nargs="?", help="Session ID")
    categories_parser.add_argument(
        "--hierarchy", action="store_true", help="Show full hierarchy"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        service = CostcoService()

        if args.command == "scrape":
            print("🚀 Starting Costco scraping with database storage...")

            # Setup progress callbacks
            def on_category(session_id, category):
                print(
                    f"  📁 Found category: {category.name} ({category.category_type.value})"
                )

            def on_product(session_id, product):
                price = product.get("price", "N/A")
                print(f"    🛍️  Found product: {product.get('name')} - ${price}")

            service.on_category_found = on_category
            service.on_product_found = on_product

            session_id = service.scrape_categories(
                categories_limit=args.limit, specific_categories=args.categories
            )

            # Show results
            data = service.get_session_data()
            print(f"\n📊 Scraping completed!")
            print(f"   Session: {session_id}")
            print(f"   Categories: {data['stats'].get('categories_found', 0)}")
            print(f"   Products: {data['stats'].get('products_found', 0)}")

            service.end_scraping_session()

        elif args.command == "init":
            print("🗄️  Initializing database...")
            db = CostcoDatabase()
            print("✅ Database initialized successfully")

        elif args.command == "stats":
            stats = service.get_database_stats()
            print("📊 Database Statistics:")
            print(json.dumps(stats, indent=2, default=str))

        elif args.command == "sessions":
            sessions = service.db.get_recent_sessions(args.limit)
            print(f"📅 Recent {len(sessions)} sessions:")
            for session in sessions:
                status_emoji = (
                    "✅"
                    if session["status"] == "completed"
                    else "❌"
                    if session["status"] == "failed"
                    else "🔄"
                )
                print(f"  {status_emoji} {session['session_id']}")
                print(f"     Started: {session['start_time']}")
                print(
                    f"     Categories: {session.get('categories_found', 0)}, Products: {session.get('products_found', 0)}"
                )
                print()

        elif args.command == "export":
            if args.session_id:
                export_file = service.export_session_data(args.session_id, args.format)
            else:
                # Export latest session
                sessions = service.db.get_recent_sessions(1)
                if not sessions:
                    print("❌ No sessions found to export")
                    return
                export_file = service.export_session_data(
                    sessions[0]["session_id"], args.format
                )

            print(f"📁 Data exported to: {export_file}")

        elif args.command == "search":
            results = service.search_products(args.query, args.session)
            print(f"🔍 Found {len(results)} products matching '{args.query}':")
            for product in results[:10]:  # Limit to 10 results
                price = f"${product['price']:.2f}" if product.get("price") else "N/A"
                print(f"  🛍️  {product['name']} - {price}")
                if product.get("brand"):
                    print(f"      Brand: {product['brand']}")
                print()

        elif args.command == "cleanup":
            print(f"🧹 Cleaning up data older than {args.days} days...")
            service.cleanup_old_data(args.days)
            print("✅ Cleanup completed")

        elif args.command == "categories":
            session_id = args.session_id
            if not session_id:
                # Use latest session
                sessions = service.db.get_recent_sessions(1)
                if not sessions:
                    print("❌ No sessions found")
                    return
                session_id = sessions[0]["session_id"]

            if args.hierarchy:
                categories = service.db.get_category_hierarchy(session_id)
                print(f"🌳 Category hierarchy for session {session_id}:")
                current_level = -1
                for cat in categories:
                    if cat["level"] > current_level:
                        current_level = cat["level"]
                    indent = "  " * cat["level"]
                    leaf_indicator = "🍃" if cat["is_leaf"] else "📁"
                    print(
                        f"{indent}{leaf_indicator} {cat['name']} ({cat['category_type']})"
                    )
            else:
                categories = service.db.get_categories(session_id)
                print(f"📁 Root categories for session {session_id}:")
                for cat in categories:
                    leaf_indicator = "🍃" if cat["is_leaf"] else "📁"
                    print(f"  {leaf_indicator} {cat['name']} ({cat['category_type']})")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
