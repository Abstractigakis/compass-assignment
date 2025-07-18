import json
import os
from bs4 import BeautifulSoup

def extract_data(html_content, output_folder=None):
    soup = BeautifulSoup(html_content, 'html.parser')
    categories = []
    services = []
    entities_found = []
    files_created = []

    # Extract categories from breadcrumbs
    breadcrumb = soup.find('ol', {'class': 'crumbs'})
    if breadcrumb:
        for li in breadcrumb.find_all('li'):
            a_tag = li.find('a')
            name = li.find('span', itemprop='name').text.strip()
            url = a_tag['href'] if a_tag else None
            categories.append({
                "name": name,
                "url": url,
                "category_type": "non_leaf_navigation" if a_tag else "unknown",
                "description": "",
                "parent_category": "",
                "subcategories": [],
                "is_leaf": False,
                "metadata": {}
            })

    #Extract services
    service_tiles = soup.find_all('div', {'class': 'CSLPtile'})
    for tile in service_tiles:
        a_tag = tile.find('a', class_='external')
        name = tile.find('h2').text.strip()
        url = a_tag['href']
        description = tile.find('p').text.strip()
        services.append({
            "name": name,
            "url": url,
            "description": description
        })


    if categories:
        entities_found.append("categories")
        if output_folder:
            filepath = os.path.join(output_folder, 'categories.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(categories, f, indent=4)
            files_created.append(filepath)

    if services:
        entities_found.append("services")
        if output_folder:
            filepath = os.path.join(output_folder, 'services.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(services, f, indent=4)
            files_created.append(filepath)

    return {
        "entities_found": entities_found,
        "files_created": files_created
    }