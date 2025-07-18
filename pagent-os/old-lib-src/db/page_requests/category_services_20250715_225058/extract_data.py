import json
import os
from bs4 import BeautifulSoup

def extract_data(html_content, output_folder=None):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        return {'entities_found': [], 'files_created': [], 'error': f'Error parsing HTML: {e}'}

    entities = {}
    files_created = []

    # Example:  Adapt to the actual HTML structure.  This is a placeholder.
    for product in soup.find_all('div', class_='product'): # Replace with actual class/tag
        product_data = {
            'name': product.find('h2').text.strip() if product.find('h2') else None,
            'price': product.find('span', class_='price').text.strip() if product.find('span', class_='price') else None,
            # Add other product attributes as needed
        }
        if 'products' not in entities:
            entities['products'] = []
        entities['products'].append(product_data)


    for category in soup.find_all('div', class_='category'): # Replace with actual class/tag
        category_data = {
            'name': category.find('h3').text.strip() if category.find('h3') else None,
            # Add other category attributes as needed
        }
        if 'categories' not in entities:
            entities['categories'] = []
        entities['categories'].append(category_data)


    # Add more entity types (sales, promotions, etc.) as needed, similar to the above examples


    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
        for entity_type, data in entities.items():
            filepath = os.path.join(output_folder, f'{entity_type}.json')
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                files_created.append(filepath)
            except Exception as e:
                return {'entities_found': list(entities.keys()), 'files_created': files_created, 'error': f'Error writing JSON file: {e}'}

    return {'entities_found': list(entities.keys()), 'files_created': files_created}