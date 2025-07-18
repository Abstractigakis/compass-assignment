import json
import os
from bs4 import BeautifulSoup

def extract_data(html_content, output_folder=None):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        entities = {}
        entities_found = []
        files_created = []

        # Extract services
        services = []
        for tile in soup.find_all('div', class_='CSLPtile'):
            service = {}
            service['title'] = tile.find('h2').text.strip()
            service['description'] = tile.find('p').text.strip()
            service['url'] = tile.find('a')['href']
            service['image'] = tile.find('img', class_='CSLPtileimage')['src']
            services.append(service)
        if services:
            entities['services'] = services
            entities_found.append('services')

        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
            for entity_type, entity_data in entities.items():
                filepath = os.path.join(output_folder, f"{entity_type}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(entity_data, f, indent=4)
                files_created.append(filepath)

        return {'entities_found': entities_found, 'files_created': files_created}

    except Exception as e:
        return {'entities_found': [], 'files_created': [], 'error': str(e)}