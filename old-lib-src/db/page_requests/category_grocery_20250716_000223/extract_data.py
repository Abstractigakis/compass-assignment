import json
import os
from bs4 import BeautifulSoup

def extract_data(html_content, output_folder=None):
    soup = BeautifulSoup(html_content, 'html.parser')
    categories = []
    products = []
    other_entities = []
    entities_found = []
    files_created = []

    # Extract Category
    category_name_element = soup.find('h1', class_='t1-style')
    if category_name_element:
        category_name = category_name_element.text.strip()
        category = {
            "name": category_name,
            "url": "",
            "category_type": "non_leaf_navigation",
            "description": "",
            "parent_category": None,
            "subcategories": [],
            "is_leaf": False,
            "metadata": {}
        }
        categories.append(category)
        entities_found.append(category)


    # Extract Products
    product_tiles = soup.find_all('div', class_='product-tile-set')
    for tile in product_tiles:
        product = {}
        product['name'] = tile.find('span', class_='description').text.strip()
        product['url'] = tile.get('data-pdp-url')
        product['price'] = tile.find('div', class_='price').text.strip()
        products.append(product)
        entities_found.append(product)


    #Save to JSON
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
        with open(os.path.join(output_folder, 'categories.json'), 'w') as f:
            json.dump(categories, f, indent=4)
        with open(os.path.join(output_folder, 'products.json'), 'w') as f:
            json.dump(products, f, indent=4)
        files_created.extend([os.path.join(output_folder, 'categories.json'), os.path.join(output_folder, 'products.json')])


    return {'entities_found': entities_found, 'files_created': files_created}