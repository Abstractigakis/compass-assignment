import json
import os
from bs4 import BeautifulSoup

def extract_data(html_content, output_folder=None):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        entities_found = []
        files_created = []

        # Extract categories
        categories = []
        category_elements = soup.find_all(class_="categoryname")
        for element in category_elements:
            category = element.find('h1').text.strip()
            categories.append({'name': category})
        if categories:
            entities_found.append('categories')
            if output_folder:
                filepath = os.path.join(output_folder, 'categories.json')
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(categories, f, indent=4)
                files_created.append(filepath)


        # Extract products
        products = []
        product_elements = soup.find_all(class_="product-tile-set")
        for element in product_elements:
            product = {}
            product['name'] = element.find('span', class_='description').text.strip()
            product['price'] = element.find(class_='price').text.strip()
            product['image'] = element.find('img')['src']
            product['url'] = element.get('data-pdp-url')
            products.append(product)

        if products:
            entities_found.append('products')
            if output_folder:
                filepath = os.path.join(output_folder, 'products.json')
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(products, f, indent=4)
                files_created.append(filepath)

        return {'entities_found': entities_found, 'files_created': files_created}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {'entities_found': [], 'files_created': []}