import json
import os
from bs4 import BeautifulSoup

def extract_data(html_content, output_folder=None):
    soup = BeautifulSoup(html_content, 'html.parser')
    categories = []
    other_entities = []
    entities_found = []
    files_created = []

    try:
        slides = soup.find('ul', class_='e-rgasvd').find_all('li')
        for slide in slides:
            a_tag = slide.find('a')
            href = a_tag['href']
            img_alt = a_tag.find('img')['alt']
            
            category = {
                "name": img_alt,
                "url": href,
                "category_type": "unknown",
                "description": img_alt,
                "parent_category": None,
                "subcategories": [],
                "is_leaf": False,
                "metadata": {}
            }

            if "/collections/" in href:
                category["category_type"] = "non_leaf_navigation"
            elif "/pages/" in href:
                category["category_type"] = "leaf_service"
                category["is_leaf"] = True
            elif "sameday.costco.ca" in href:
                category["category_type"] = "leaf_service"
                category["is_leaf"] = True
            
            categories.append(category)
            entities_found.append(category)

        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
            with open(os.path.join(output_folder, 'categories.json'), 'w', encoding='utf-8') as f:
                json.dump(categories, f, indent=4)
            files_created.append('categories.json')

    except Exception as e:
        print(f"Error processing categories: {e}")

    return {"entities_found": entities_found, "files_created": files_created}