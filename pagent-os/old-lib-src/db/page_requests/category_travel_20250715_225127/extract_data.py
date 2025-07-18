import json
import os
from bs4 import BeautifulSoup

def extract_data(html_content, output_folder=None):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        entities = {}
        entities_found = []
        files_created = []

        #Extract promotions
        promotions = []
        for item in soup.find_all(class_='card image-card'):
            promotion = {
                'item_name': item.get('data-item_name'),
                'link_to': item.get('data-link-to'),
                'packageid': item.get('data-packageid'),
                'href': item.get('href'),
                'title': item.find(data_test="offerCardTitle").text.strip(),
                'summary': item.find(data_test="offerCardSummary").text.strip().replace('\n',', ')
            }
            promotions.append(promotion)
        if promotions:
            entities['promotions'] = promotions
            entities_found.append('promotions')


        # Extract carousel items
        carousel_items = []
        for item in soup.select('ul.carousel-items > li'):
            carousel_item = {
                'item_name': item.find(data_test="carouselOfferItemName").text.strip() if item.find(data_test="carouselOfferItemName") else None,
                'item_heading': item.find(data_test="carouselOfferHeading").text.strip() if item.find(data_test="carouselOfferHeading") else None,
                'item_description': item.find(data_test="carouselOfferItemDescription").text.strip() if item.find(data_test="carouselOfferItemDescription") else None,
                'bullets': [li.text.strip() for li in item.select('ul.check > li')],
                'details_link': item.select_one('a.details-link').get('href') if item.select_one('a.details-link') else None
            }
            carousel_items.append(carousel_item)
        if carousel_items:
            entities['carousel_items'] = carousel_items
            entities_found.append('carousel_items')

        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
            for entity_type, entity_data in entities.items():
                file_path = os.path.join(output_folder, f"{entity_type}.json")
                with open(file_path, 'w') as f:
                    json.dump(entity_data, f, indent=4)
                files_created.append(file_path)

        return {'entities_found': entities_found, 'files_created': files_created}
    except Exception as e:
        return {'entities_found': [], 'files_created': [], 'error': str(e)}