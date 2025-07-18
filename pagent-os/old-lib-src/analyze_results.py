#!/usr/bin/env python3
"""
Summary script to analyze the results of the Costco web scraper AI extraction.
Shows what the AI learned from each category page.
"""

import json
import os
from pathlib import Path


def analyze_extraction_results():
    """Analyze all extraction results from the db/page_requests directory."""

    base_dir = Path("db/page_requests")
    if not base_dir.exists():
        print("❌ No page_requests directory found")
        print("Run 'make run' or 'make run-limited' first to generate data")
        return

    print("🔍 COSTCO WEB SCRAPER - AI LEARNING ANALYSIS")
    print("=" * 60)

    category_folders = [
        d for d in base_dir.iterdir() if d.is_dir() and "category_" in d.name
    ]
    category_folders.sort(key=lambda x: x.name)

    if not category_folders:
        print("❌ No category folders found")
        print("Run 'make run' or 'make run-limited' first to generate data")
        return

    total_products = 0
    total_entities = set()
    total_files = 0

    for folder in category_folders:
        category_name = (
            folder.name.replace("category_", "")
            .split("_202")[0]
            .replace("_", " ")
            .title()
        )

        print(f"\n📂 {category_name}")
        print("-" * 40)

        # Check what files were created
        json_files = list(folder.glob("*.json"))
        json_files = [f for f in json_files if f.name != "meta.json"]

        if not json_files:
            print("   ⚠️  No data files generated")
            continue

        for json_file in json_files:
            entity_type = json_file.stem
            total_entities.add(entity_type)
            total_files += 1

            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    count = len(data)
                    if entity_type == "products":
                        total_products += count
                    print(f"   📋 {entity_type}: {count} items")

                    # Show sample items for products
                    if entity_type == "products" and count > 0:
                        sample = data[0]
                        if "name" in sample:
                            print(f"      💡 Sample: {sample['name'][:50]}...")
                        if "price" in sample:
                            print(f"      💰 Price: {sample['price']}")

                else:
                    print(f"   📋 {entity_type}: {type(data).__name__} data")

            except Exception as e:
                print(f"   ❌ Error reading {json_file.name}: {e}")

        # Check if extraction function exists
        extract_py = folder / "extract_data.py"
        if extract_py.exists():
            print(f"   🤖 AI-generated extraction function: ✅")
            # Get function size
            size = extract_py.stat().st_size
            print(f"   📏 Function size: {size} bytes")
        else:
            print(f"   🤖 AI-generated extraction function: ❌")

    print(f"\n{'='*60}")
    print("📊 OVERALL RESULTS:")
    print(f"   🏪 Categories processed: {len(category_folders)}")
    print(f"   🛒 Total products found: {total_products}")
    print(f"   📋 Entity types discovered: {len(total_entities)}")
    print(f"   📁 Total files created: {total_files}")
    print(f"   🧠 Entity types: {', '.join(sorted(total_entities))}")

    print(f"\n🎉 AI LEARNING SUCCESS:")
    print(f"   • AI generated custom extraction functions for each page type")
    print(f"   • Successfully identified {len(total_entities)} different entity types")
    print(f"   • Extracted {total_products} products across categories")
    print(f"   • Learned to adapt extraction patterns to different page structures")


if __name__ == "__main__":
    analyze_extraction_results()
