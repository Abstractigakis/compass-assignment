import json
import os
from bs4 import BeautifulSoup

def extract_data(html_content, output_folder=None):
    soup = BeautifulSoup(html_content, 'html.parser')
    categories = []
    products = []
    entities_found = []
    files_created = []

    category_element = soup.find('h1', class_='t1-style')
    if category_element:
        category_name = category_element.text.strip()
        categories.append({
            "name": category_name,
            "url": "/",
            "category_type": "non_leaf_navigation",
            "description": "Grocery and Household",
            "parent_category": None,
            "subcategories": [],
            "is_leaf": False,
            "metadata": {}
        })

    product_tiles = soup.find_all('div', class_='product-tile-set')
    for tile in product_tiles:
        pdp_url = tile.get('data-pdp-url')
        if pdp_url:
            products.append({"name": tile.find('span', class_='description').text.strip(), "url": pdp_url})


    if categories:
        entities_found.append("categories")
        if output_folder:
            filepath = os.path.join(output_folder, "categories.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(categories, f, indent=4)
            files_created.append(filepath)

    if products:
        entities_found.append("products")
        if output_folder:
            filepath = os.path.join(output_folder, "products.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=4)
            files_created.append(filepath)

    return {
        "entities_found": entities_found,
        "files_created": files_created
    }