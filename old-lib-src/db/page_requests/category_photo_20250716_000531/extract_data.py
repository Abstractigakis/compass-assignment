import json
import os
from bs4 import BeautifulSoup

def extract_data(html_content, output_folder=None):
    soup = BeautifulSoup(html_content, 'html.parser')
    categories = []
    products = []
    services = []
    entities_found = []
    files_created = []

    # Extract categories from breadcrumbs
    breadcrumbs = soup.find('ol', {'class': 'crumbs'})
    if breadcrumbs:
        for i, li in enumerate(breadcrumbs.find_all('li')):
            name = li.find('span', itemprop='name').text.strip()
            url = li.find('a')['href'] if li.find('a') else None
            category_type = "non_leaf_navigation" if i < len(breadcrumbs.find_all('li')) -1 else "leaf_service"
            is_leaf = True if i == len(breadcrumbs.find_all('li')) -1 else False
            parent_category = breadcrumbs.find_all('li')[i-1].find('span', itemprop='name').text.strip() if i > 0 else None
            categories.append({
                "name": name,
                "url": url,
                "category_type": category_type,
                "description": "",
                "parent_category": parent_category,
                "subcategories": [],
                "is_leaf": is_leaf,
                "metadata": {}
            })


    # Extract services
    service_section = soup.find('div', id='rs-costco-services-wrapper')
    if service_section:
      services.append({"name": "Shutterfly Photo Services", "description": "Photo printing and gifting services", "url": "https://www.shutterflycanada.ca"})
      entities_found.append("services")


    if categories:
        if output_folder:
            categories_file_path = os.path.join(output_folder, 'categories.json')
            with open(categories_file_path, 'w', encoding='utf-8') as f:
                json.dump(categories, f, indent=4)
            files_created.append(categories_file_path)
        entities_found.append("categories")

    if services:
        if output_folder:
            services_file_path = os.path.join(output_folder, 'services.json')
            with open(services_file_path, 'w', encoding='utf-8') as f:
                json.dump(services, f, indent=4)
            files_created.append(services_file_path)

    return {
        "entities_found": entities_found,
        "files_created": files_created
    }