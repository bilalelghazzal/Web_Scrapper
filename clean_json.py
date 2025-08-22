"""import json
import csv
import os

def fix_encoding(text):
    if not isinstance(text, str):
        return text
    try:
        # Try to fix common encoding issues
        return text.encode('latin1').decode('utf-8')
    except Exception:
        return text

def flatten_dict(d, parent_key='', sep='.'):  # Flattens nested dicts for CSV
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Join lists as semicolon-separated strings, fixing encoding
            items.append((new_key, '; '.join(fix_encoding(str(i)) for i in v)))
        else:
            items.append((new_key, fix_encoding(v)))
    return dict(items)
"""
import json
import csv
from html import unescape

# Fonction pour corriger les encodages
def fix_encoding(text):
    if not isinstance(text, str):
        return text
    try:
        return text.encode('latin1').decode('utf-8')
    except Exception:
        return text

# Fonction pour aplatir les dictionnaires (utile si tu veux l'étendre)
def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, '; '.join(fix_encoding(str(i)) for i in v)))
        else:
            items.append((new_key, fix_encoding(v)))
    return dict(items)

# Charger le JSON
with open("scraped_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Extraction et nettoyage des données
rows = []

for item in data:
    url = item.get("url", "")
    metadata = item.get("metadata", {})
    content = item.get("content", {})
    headings = content.get("headings", {})
    paragraphs = content.get("paragraphs", [])
    business_info = item.get("business_info", {})

    title = fix_encoding(metadata.get("title", ""))
    description = fix_encoding(metadata.get("description", ""))

    h1 = " | ".join([fix_encoding(h) for h in headings.get("h1", [])])
    h2 = " | ".join([fix_encoding(h) for h in headings.get("h2", [])])
    h3 = " | ".join([fix_encoding(h) for h in headings.get("h3", [])])
    h4 = " | ".join([fix_encoding(h) for h in headings.get("h4", [])])
    h5 = " | ".join([fix_encoding(h) for h in headings.get("h5", [])])
    h6 = " | ".join([fix_encoding(h) for h in headings.get("h6", [])])

    paragraphs = content.get("paragraphs", [])
    navigation = item.get("navigation", {})
    footer_links = navigation.get("footer_links", [])
    media = item.get("media", {})
    image_alt_texts = media.get("image_alt_texts", [])
    document_links = media.get("document_links", {})
    pdf_links = document_links.get("pdf", [])
    doc_links = document_links.get("doc", [])
    docx_links = document_links.get("docx", [])
    business_info = business_info.get("business_info", {})
    business_name = business_info.get("business_name", "")
    business_address = business_info.get("business_address", "")
    business_phone = business_info.get("business_phone", "")
    business_email = business_info.get("business_email", "")

    paragraph_text = " ".join([fix_encoding(p.strip()) for p in paragraphs])

    footer_links = " | ".join([
        fix_encoding(link) for link in item.get("navigation", {}).get("footer_links", []) if link
    ])

    email_form = item.get("forms", {}).get("details", [[]])[0]
    email_placeholder = ""
    for field in email_form:
        if field.get("type") == "email":
            email_placeholder = fix_encoding(field.get("placeholder", ""))

    row = {
        "url": url,
        "title": title,
        "description": description,
        "content":paragraph_text,
        "medoia":media,
        "business_info":business_info,
    }

    rows.append(row)

# En-têtes
fieldnames = list(rows[0].keys())

# Sauvegarde CSV
with open("structured_output.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(" Fichier CSV créé : structured_output.csv")