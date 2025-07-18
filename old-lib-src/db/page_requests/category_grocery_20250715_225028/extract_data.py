import json
import os
from bs4 import BeautifulSoup

def extract_data(html_content, output_folder=None):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        entities_found = []
        files_created = []

        products = []
        product_elements = soup.find_all('div', class_='product-tile-set')
        for product in product_elements:
            product_data = {
                'name': product.find('span', class_='description').text.strip(),
                'price': product.find('div', class_='price').text.strip(),
                'url': product.get('data-pdp-url'),
                'image': product.find('img').get('data-src'),
                'features': [li.text.strip() for li in product.find('ul', class_='product-features').find_all('li')] if product.find('ul', class_='product-features') else [],
                'rating': product.find('div', class_='ratings-number').text.strip().replace('(', '').replace(')', '') if product.find('div', class_='ratings-number') else None
            }
            products.append(product_data)

        if products:
            entities_found.append('products')
            if output_folder:
                filepath = os.path.join(output_folder, 'products.json')
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(products, f, indent=4)
                files_created.append(filepath)


        categories = []
        category_element = soup.find('h1', class_='t1-style')
        if category_element:
            categories.append({'name': category_element.text.strip()})
            entities_found.append('categories')
            if output_folder:
                filepath = os.path.join(output_folder, 'categories.json')
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(categories, f, indent=4)
                files_created.append(filepath)

        return {'entities_found': entities_found, 'files_created': files_created}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'entities_found': [], 'files_created': []}