import json
from bs4 import BeautifulSoup
import os

def extract_data(html_content, output_folder=None):
    soup = BeautifulSoup(html_content, 'html.parser')
    categories = []
    products = []
    services = []
    entities_found = []
    files_created = []

    for a_tag in soup.find_all('a', class_='e-1qcnqs9'):
        href = a_tag.get('href')
        img_alt = a_tag.find('img').get('alt')
        category = {
            "name": img_alt,
            "url": href,
            "category_type": "unknown",
            "description": img_alt,
            "parent_category": None,
            "subcategories": [],
            "is_leaf": False,
            "metadata": {}
        }

        if "/collections/" in href:
            category["category_type"] = "non_leaf_navigation"
        elif "/pages/" in href:
            category["category_type"] = "leaf_service"
            category["is_leaf"] = True
        elif "/store/" in href and "alcohol" in href:
            category["category_type"] = "leaf_service"
            category["is_leaf"] = True

        categories.append(category)

    if categories:
        entities_found.append("categories")
        if output_folder:
            filepath = os.path.join(output_folder, "categories.json")
            with open(filepath, 'w') as f:
                json.dump(categories, f, indent=4)
            files_created.append(filepath)

    return {
        "entities_found": entities_found,
        "files_created": files_created
    }