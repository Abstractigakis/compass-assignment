import json
import os
from bs4 import BeautifulSoup

def extract_data(html_content, output_folder=None):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        entities = {'promotions': [], 'categories': []}
        files_created = []

        promotions = soup.find_all('img', {'class': 'e-798uwr'})
        for promo in promotions:
            alt_text = promo.get('alt', '')
            src = promo.get('src', '')
            entities['promotions'].append({'alt_text': alt_text, 'image_src': src})


        links = soup.find_all('a', {'class': 'e-1qcnqs9'})
        for link in links:
            href = link.get('href', '')
            if '/collections/' in href:
                entities['categories'].append({'url': href})


        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
            for entity_type, data in entities.items():
                filepath = os.path.join(output_folder, f"{entity_type}.json")
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=4)
                files_created.append(filepath)

        return {'entities_found': list(entities.keys()), 'files_created': files_created}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {'entities_found': [], 'files_created': []}