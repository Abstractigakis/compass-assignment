#!/usr/bin/env python3
"""
Common Category Interface for Costco Web Scraper AI Extraction

This module defines the standard category structure that all AI-generated
extraction functions should use for consistent output across different page types.
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class CategoryType(Enum):
    """Category types based on leaf status and content."""

    LEAF_PRODUCT = "leaf_product"  # Contains actual products
    LEAF_SERVICE = "leaf_service"  # Contains services/offerings
    LEAF_LOCATION = "leaf_location"  # Contains store locations
    NON_LEAF_NAV = "non_leaf_navigation"  # Navigation to subcategories
    NON_LEAF_HUB = "non_leaf_hub"  # Hub page with mixed content
    UNKNOWN = "unknown"  # Cannot be determined


@dataclass
class CategoryItem:
    """
    Standard category structure for Costco pages.

    This interface ensures consistent category extraction across all page types,
    whether they are navigation pages, product listings, or service offerings.
    """

    name: str  # Display name of category
    url: Optional[str] = None  # Relative or absolute URL
    category_type: CategoryType = CategoryType.UNKNOWN
    description: Optional[str] = None  # Brief description if available
    parent_category: Optional[str] = None  # Parent category name
    subcategories: List[str] = None  # List of immediate subcategory names
    metadata: Dict = None  # Additional category-specific data

    def __post_init__(self):
        """Initialize default values."""
        if self.subcategories is None:
            self.subcategories = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "url": self.url,
            "category_type": self.category_type.value,
            "description": self.description,
            "parent_category": self.parent_category,
            "subcategories": self.subcategories,
            "is_leaf": self.is_leaf_category(),
            "metadata": self.metadata,
        }

    def is_leaf_category(self) -> bool:
        """Determine if this is a leaf category (contains end content)."""
        return self.category_type in [
            CategoryType.LEAF_PRODUCT,
            CategoryType.LEAF_SERVICE,
            CategoryType.LEAF_LOCATION,
        ]


def create_category_extraction_prompt(page_type_hint: str = "unknown") -> str:
    """
    Generate a standardized Gemini prompt for category extraction.

    Args:
        page_type_hint: Hint about the page type (product, service, navigation, etc.)

    Returns:
        Formatted prompt string for consistent category extraction
    """

    prompt = f"""
You are analyzing a Costco.ca page to extract category information using a STANDARDIZED interface.

CRITICAL: You must use this EXACT category structure for ALL categories found:

```json
{{
    "name": "Category Display Name",
    "url": "/relative-url-path",
    "category_type": "one of: leaf_product|leaf_service|leaf_location|non_leaf_navigation|non_leaf_hub|unknown",
    "description": "Brief description if available (optional)",
    "parent_category": "Parent category name if applicable (optional)",
    "subcategories": ["list", "of", "immediate", "subcategory", "names"],
    "is_leaf": true/false,
    "metadata": {{"any": "additional", "relevant": "data"}}
}}
```

CATEGORY TYPE DEFINITIONS:
- **leaf_product**: Page contains actual products for purchase
- **leaf_service**: Page contains services or offerings (insurance, photo services, etc.)
- **leaf_location**: Page contains store locations or warehouse information
- **non_leaf_navigation**: Navigation page leading to subcategories
- **non_leaf_hub**: Hub page with mixed content and multiple navigation paths
- **unknown**: Cannot determine the category type

EXTRACTION RULES:
1. Extract ALL categories/navigation elements found on the page
2. Use relative URLs (start with /) when possible
3. Determine category_type based on the content the category leads to
4. Set is_leaf to true for leaf_* types, false for non_leaf_* types
5. Include parent-child relationships when visible
6. Extract meaningful descriptions from link text, headings, or nearby content
7. For Costco specifically, look for:
   - Department categories (Grocery, Electronics, etc.)
   - Service categories (Photo, Travel, Insurance, etc.)
   - Location/warehouse categories
   - Subcategory navigation (within departments)

PAGE TYPE HINT: {page_type_hint}

Return ONLY a JSON array of category objects using the exact structure above.
No explanations, no markdown formatting, just the JSON array.
"""

    return prompt


def validate_category_output(categories: List[Dict]) -> List[CategoryItem]:
    """
    Validate and convert AI output to standard category items.

    Args:
        categories: Raw category dictionaries from AI

    Returns:
        List of validated CategoryItem objects
    """
    validated_categories = []

    for cat_dict in categories:
        try:
            # Handle different input formats gracefully
            if isinstance(cat_dict, str):
                # Simple string category
                category = CategoryItem(
                    name=cat_dict, category_type=CategoryType.UNKNOWN
                )
            elif isinstance(cat_dict, dict):
                # Structured category
                category_type = CategoryType.UNKNOWN
                if "category_type" in cat_dict:
                    try:
                        category_type = CategoryType(cat_dict["category_type"])
                    except ValueError:
                        category_type = CategoryType.UNKNOWN

                category = CategoryItem(
                    name=cat_dict.get("name", "Unknown Category"),
                    url=cat_dict.get("url"),
                    category_type=category_type,
                    description=cat_dict.get("description"),
                    parent_category=cat_dict.get("parent_category"),
                    subcategories=cat_dict.get("subcategories", []),
                    metadata=cat_dict.get("metadata", {}),
                )
            else:
                continue  # Skip invalid entries

            validated_categories.append(category)

        except Exception as e:
            print(f"Warning: Failed to validate category {cat_dict}: {e}")
            continue

    return validated_categories


# Example usage for AI-generated extraction functions
CATEGORY_EXTRACTION_TEMPLATE = '''
def extract_categories(soup, output_folder=None):
    """Extract categories using standardized interface."""
    categories = []
    
    # Extract category elements from HTML
    category_elements = soup.find_all("a", href=True)  # Customize based on page structure
    
    for element in category_elements:
        try:
            name = element.get_text(strip=True)
            url = element.get("href")
            
            # Determine category type based on content/context
            category_type = "unknown"
            if "product" in url.lower() or "catalog" in url.lower():
                category_type = "leaf_product"
            elif any(service in url.lower() for service in ["service", "insurance", "photo", "travel"]):
                category_type = "leaf_service"
            elif "location" in url.lower() or "warehouse" in url.lower():
                category_type = "leaf_location"
            elif any(nav in url.lower() for nav in ["category", "department", "browse"]):
                category_type = "non_leaf_navigation"
            
            category = {
                "name": name,
                "url": url,
                "category_type": category_type,
                "is_leaf": category_type.startswith("leaf_"),
                "subcategories": [],
                "metadata": {}
            }
            
            categories.append(category)
            
        except Exception as e:
            continue
    
    return categories
'''


if __name__ == "__main__":
    # Test the interface
    sample_categories = [
        CategoryItem(
            name="Electronics",
            url="/electronics.html",
            category_type=CategoryType.NON_LEAF_NAV,
            description="Electronic devices and accessories",
            subcategories=["Computers", "TVs", "Audio"],
        ),
        CategoryItem(
            name="iPhone 15",
            url="/iphone-15.html",
            category_type=CategoryType.LEAF_PRODUCT,
            description="Latest iPhone model",
        ),
    ]

    print("Sample category interface:")
    for cat in sample_categories:
        print(
            f"- {cat.name}: {cat.category_type.value} (leaf: {cat.is_leaf_category()})"
        )
