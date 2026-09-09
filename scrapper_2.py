import time
import requests
from bs4 import BeautifulSoup
import json

def extract_page_content(url):
    """
    Extrait les données pertinentes d'une page web :
    uniquement le titre, l'email, le téléphone et l'adresse.
    """
    try:
        # Récupérer le contenu de la page
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Erreur lors de la récupération de {url}: {response.status_code}")
            return None

        # Forcer UTF-8 : requests utilise ISO-8859-1 lorsque le header Content-Type
        # ne précise pas de charset, ce qui provoque des erreurs d'encodage (mojibake).
        response.encoding = 'utf-8'

        # Parser le contenu HTML avec BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Dictionnaire avec uniquement les 4 champs attendus
        data = {
            "url": url,
            "title": "",
            "email": "",
            "phone": "",
            "address": ""
        }

        # --- Titre de la page ---
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            data["title"] = title_tag.string.strip()

        # --- Email ---
        # Chercher un lien "mailto:" dans toute la page (plus robuste qu'un seul div)
        email = ""
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("mailto:"):
                email = href.replace("mailto:", "").strip()
                break
        if email:
            data["email"] = email

        # --- Téléphone ---
        # Préférer un lien "tel:", sinon chercher un élément avec classe "phone"
        phone = ""
        tel_link = soup.find("a", href=lambda h: h and h.startswith("tel:"))
        if tel_link:
            phone = tel_link["href"].replace("tel:", "").strip()
        else:
            phone_tag = soup.find("span", class_="phone") or soup.find("a", class_="phone")
            if phone_tag:
                phone = phone_tag.get_text(strip=True)
        if phone:
            data["phone"] = phone

        # --- Adresse ---
        address = ""
        addr_tag = (soup.find("span", class_="address")
                    or soup.find("div", class_="address")
                    or soup.find("p", class_="address"))
        if addr_tag:
            address = addr_tag.get_text(strip=True)

        # Repli (fallback) : si aucune classe "address" n'a été trouvée,
        # essayer la balise sémantique <address> (HTML5).
        if not address:
            addr_tag = soup.find("address")
            if addr_tag:
                address = addr_tag.get_text(" ", strip=True)

        if address:
            data["address"] = address

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
        with open(filename, "r", encoding="utf-8") as f:
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