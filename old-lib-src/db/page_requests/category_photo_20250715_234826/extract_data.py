import json
import os
from bs4 import BeautifulSoup

def extract_data(html_content, output_folder=None):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        entities = {}
        entities_found = []
        files_created = []

        # Extract promotions
        promotions = []
        promotion_elements = soup.find_all(class_=['rs-costco-services-hero-row', 'rs-costco-services-promise-row'])
        for element in promotion_elements:
            title = element.find('h1' or 'h2').text.strip() if element.find('h1' or 'h2') else None
            description = element.find('p').text.strip() if element.find('p') else None
            promotion = {'title': title, 'description': description}
            promotions.append(promotion)
        if promotions:
            entities['promotions'] = promotions
            entities_found.append('promotions')

        # Extract categories
        categories = []
        category_elements = soup.find_all('li', itemprop='itemListElement')
        for element in category_elements:
            category_name = element.find('span', itemprop='name').text.strip()
            categories.append(category_name)
        if categories:
            entities['categories'] = categories
            entities_found.append('categories')

        #Extract links
        links = []
        link_elements = soup.find_all('a', class_='external')
        for element in link_elements:
            link = element['href']
            links.append(link)
        if links:
            entities['links'] = links
            entities_found.append('links')

        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
            for entity_type, data in entities.items():
                filepath = os.path.join(output_folder, f"{entity_type}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                files_created.append(filepath)

        return {'entities_found': entities_found, 'files_created': files_created}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {'entities_found': [], 'files_created': []}