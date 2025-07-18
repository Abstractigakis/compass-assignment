import json
from bs4 import BeautifulSoup
import os

def extract_data(html_content, output_folder=None):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        entities = {'promotions': [], 'categories': [], 'sales': []}
        files_created = []

        for li in soup.find_all('li'):
            a_tag = li.find('a')
            if a_tag:
                href = a_tag.get('href')
                img_tag = a_tag.find('img')
                alt_text = img_tag.get('alt') if img_tag else None

                if "monthly credit" in alt_text or "annual value" in alt_text:
                    entities['promotions'].append({'href': href, 'alt_text': alt_text})
                elif "Warehouse Savings" in alt_text:
                    entities['sales'].append({'href': href, 'alt_text': alt_text})
                elif "Alcohol Wine" in alt_text or "beer" in alt_text:
                    entities['categories'].append({'href': href, 'alt_text': alt_text})


        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
            for entity_type, data in entities.items():
                filepath = os.path.join(output_folder, f"{entity_type}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                files_created.append(filepath)

        return {'entities_found': list(entities.keys()), 'files_created': files_created}

    except Exception as e:
        return {'entities_found': [], 'files_created': [], 'error': str(e)}