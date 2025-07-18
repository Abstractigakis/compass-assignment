import json
import os
from bs4 import BeautifulSoup

def extract_data(html_content, output_folder=None):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        entities = {}
        entities_found = []
        files_created = []

        #Example - Adapt to your actual HTML structure
        products = []
        for product in soup.find_all('div', class_='product'): #Replace with your actual class or tag
            product_data = {
                'name': product.find('h3').text.strip(),
                'price': product.find('span', class_='price').text.strip(),
                #Add other product attributes as needed
            }
            products.append(product_data)
        if products:
            entities['products'] = products
            entities_found.append('products')


        categories = []
        for category in soup.find_all('div', class_='category'): #Replace with your actual class or tag
            category_data = {
                'name': category.find('h2').text.strip(),
                #Add other category attributes as needed
            }
            categories.append(category_data)
        if categories:
            entities['categories'] = categories
            entities_found.append('categories')


        #Add similar blocks for other entity types (sales, promotions etc.)

        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
            for entity_type, data in entities.items():
                filepath = os.path.join(output_folder, f'{entity_type}.json')
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                files_created.append(filepath)

        return {'entities_found': entities_found, 'files_created': files_created}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {'entities_found': [], 'files_created': []}