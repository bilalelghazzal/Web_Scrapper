import time
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse

def extract_page_content(url):
    """
    Extrait les données pertinentes d'une page web.
    """
    try:
        # Récupérer le contenu de la page
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Erreur lors de la récupération de {url}: {response.status_code}")
            return None

        # Parser le contenu HTML avec BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Initialiser un dictionnaire pour stocker les données
        data = {
            "url": url,
            "metadata": {},
            "content": {},
            "navigation": {},
            "forms": {},
            "media": {},
            "structured_data": {},
            "business_info": {}
        }

        # --- 1. Métadonnées de Page ---
        # Titre de la page
        title_tag = soup.find('title')
        if title_tag:
            data["metadata"]["title"] = title_tag.string.strip()

        # Méta description
        meta_description = soup.find("meta", attrs={"name": "description"})
        if meta_description and meta_description.get("content"):
            data["metadata"]["description"] = meta_description["content"].strip()

        # Mots-clés
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords and meta_keywords.get("content"):
            data["metadata"]["keywords"] = [keyword.strip() for keyword in meta_keywords["content"].split(",")]

        # Date de dernière modification
        last_modified = soup.find("meta", attrs={"name": "last-modified"})
        if last_modified and last_modified.get("content"):
            data["metadata"]["last_modified"] = last_modified["content"]

        # Fil d'Ariane (Breadcrumb)
        breadcrumb = soup.find("ol", class_="breadcrumb")
        if breadcrumb:
            data["metadata"]["breadcrumb"] = [item.get_text(strip=True) for item in breadcrumb.find_all("li")]

        # --- 2. Éléments de Contenu ---
        # Titres (H1-H6)
        headings = {}
        for i in range(1, 7):
            h_tags = soup.find_all(f"h{i}")
            if h_tags:
                headings[f"h{i}"] = [tag.get_text(strip=True) for tag in h_tags]
        data["content"]["headings"] = headings

        # Paragraphes
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
        data["content"]["paragraphs"] = paragraphs

        # --- 3. Navigation ---
        # Menu principal
        main_menu = soup.find("nav", class_="menu")
        if main_menu:
            data["navigation"]["main_menu"] = [a.get_text(strip=True) for a in main_menu.find_all("a")]

        # Liens de pied de page
        footer_links = soup.find("footer").find_all("a") if soup.find("footer") else []
        data["navigation"]["footer_links"] = [link.get_text(strip=True) for link in footer_links]

        # Fil d'Ariane
        if breadcrumb:
            data["navigation"]["breadcrumb"] = [item.get_text(strip=True) for item in breadcrumb.find_all("li")]

        # --- 4. Formulaires ---
        forms = soup.find_all("form")
        if forms:
            form_details = []
            for form in forms:
                fields = []
                for input_tag in form.find_all(["input", "textarea", "select"]):
                    field = {
                        "type": input_tag.get("type"),
                        "name": input_tag.get("name"),
                        "placeholder": input_tag.get("placeholder"),
                        "value": input_tag.get("value")
                    }
                    fields.append(field)
                form_details.append(fields)
            data["forms"]["details"] = form_details

        # --- 5. Média ---
        # Texte alternatif d'images
        images = soup.find_all("img")
        image_alt_texts = [img.get("alt") for img in images if img.get("alt")]
        data["media"]["image_alt_texts"] = image_alt_texts

        # Descriptions de vidéos
        videos = soup.find_all("video")
        video_descriptions = [video.get("title") or video.get("description") for video in videos]
        data["media"]["video_descriptions"] = video_descriptions

        # --- 5.1. Liens vers Documents ---
        # Trouver tous les liens
        all_links = soup.find_all("a", href=True)
        document_links = {
            "pdf": [],
            "doc": [],
            "docx": []
        }
        
        for link in all_links:
            href = link.get("href", "").lower()
            link_text = link.get_text(strip=True)
            
            # Construire l'URL complète si c'est un lien relatif
            if href.startswith("/"):
                parsed_url = urlparse(url)
                full_href = f"{parsed_url.scheme}://{parsed_url.netloc}{href}"
            elif href.startswith("http"):
                full_href = href
            else:
                # Lien relatif
                parsed_url = urlparse(url)
                full_href = f"{parsed_url.scheme}://{parsed_url.netloc}/{href.lstrip('/')}"
            
            # Détecter les types de documents (seulement PDF, DOC, DOCX)
            if href.endswith(".pdf"):
                document_links["pdf"].append({
                    "url": full_href,
                    "title": link.get("title", "") or link_text
                })
            elif href.endswith(".doc"):
                document_links["doc"].append({
                    "url": full_href,
                    "title": link.get("title", "") or link_text
                })
            elif href.endswith(".docx"):
                document_links["docx"].append({
                    "url": full_href,
                    "title": link.get("title", "") or link_text
                })
        
        data["media"]["document_links"] = document_links

        # --- 6. Données Structurées ---
        # JSON-LD
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        if json_ld_scripts:
            data["structured_data"]["json_ld"] = []
            for script in json_ld_scripts:
                try:
                    json_ld = json.loads(script.string)
                    data["structured_data"]["json_ld"].append(json_ld)
                except Exception as e:
                    print(f"Erreur lors de l'analyse du JSON-LD : {e}")

        # Microdata
        microdata_items = soup.find_all(itemprop=True)
        if microdata_items:
            data["structured_data"]["microdata"] = [
                {
                    "itemprop": item.get("itemprop"),
                    "content": item.get_text(strip=True)
                } for item in microdata_items
            ]

        # Schema.org
        schema_org_scripts = soup.find_all("script", type="application/ld+json")
        if schema_org_scripts:
            data["structured_data"]["schema_org"] = []
            for script in schema_org_scripts:
                try:
                    schema_data = json.loads(script.string)
                    if "@type" in schema_data:
                        data["structured_data"]["schema_org"].append(schema_data)
                except Exception as e:
                    print(f"Erreur lors de l'analyse du Schema.org : {e}")

        # --- 7. Informations Business ---
        # Coordonnées (téléphone, email, adresse)
        contact_info = soup.find("div", class_="contact-info")
        if contact_info:
            phone = contact_info.find("span", class_="phone")
            email = contact_info.find("a", href=lambda href: href and "mailto:" in href)
            address = contact_info.find("span", class_="address")

            if phone:
                data["business_info"]["phone"] = phone.get_text(strip=True)
            if email:
                data["business_info"]["email"] = email["href"].replace("mailto:", "")
            if address:
                data["business_info"]["address"] = address.get_text(strip=True)

        # Horaires d'ouverture
        opening_hours = soup.find("time", datetime=True)
        if opening_hours:
            data["business_info"]["opening_hours"] = opening_hours["datetime"]

        # Services/produits offerts
        services = soup.find_all("li", class_="service-item")
        if services:
            data["business_info"]["services_offered"] = [service.get_text(strip=True) for service in services]

        # Contenu "À propos"
        about_us = soup.find("section", id="about-us")
        if about_us:
            data["business_info"]["about_us"] = about_us.get_text(strip=True)

        # Informations équipe
        team_members = soup.find_all("div", class_="team-member")
        if team_members:
            data["business_info"]["team"] = [
                {
                    "name": member.find("h3").get_text(strip=True),
                    "role": member.find("p").get_text(strip=True)
                } for member in team_members
            ]

        # Témoignages/avis
        testimonials = soup.find_all("blockquote", class_="testimonial")
        if testimonials:
            data["business_info"]["testimonials"] = [
                {
                    "text": testimonial.get_text(strip=True),
                    "author": testimonial.find("cite").get_text(strip=True)
                } for testimonial in testimonials
            ]

        return data

    except Exception as e:
        print(f"Erreur lors de l'extraction de {url}: {e}")
        return None

def scrape_all_urls_from_file(filename="crawled_urls.txt"):
    """
    Scrape toutes les URLs depuis le fichier généré par le crawler
    """
    try:
        # Lire les URLs depuis le fichier
        with open(filename, "r") as f:
            urls = [line.strip() for line in f.readlines()]
        
        print(f"Scraping de {len(urls)} URLs...")
        scraped_data = []
        
        for i, url in enumerate(urls, 1):
            print(f"Scraping {i}/{len(urls)}: {url}")
            content = extract_page_content(url)
            if content:
                scraped_data.append(content)
            
            # Pause pour ne pas surcharger le serveur
            time.sleep(1)
        
        return scraped_data
        
    except FileNotFoundError:
        print(f"Fichier {filename} non trouvé. Exécutez d'abord le crawler.")
        return []

# Exemple d'utilisation
if __name__ == "__main__":
    # Scrapper toutes les URLs crawlées
    scraped_data = scrape_all_urls_from_file("crawled_urls.txt")
    
    # Sauvegarder les données scrapées
    with open("scraped_data.json", "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=4)
    
    print(f"Scraping terminé. {len(scraped_data)} pages scrapées.")
    print("Données sauvegardées dans 'scraped_data.json'")