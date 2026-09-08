import json
import csv

# Fonction pour corriger les encodages
def fix_encoding(text):
    if not isinstance(text, str):
        return text
    try:
        return text.encode('latin1').decode('utf-8')
    except Exception:
        return text

# Corrige l'encodage récursivement dans les dicts/listes
def fix_encoding_deep(value):
    if isinstance(value, str):
        return fix_encoding(value)
    if isinstance(value, list):
        return [fix_encoding_deep(v) for v in value]
    if isinstance(value, dict):
        return {k: fix_encoding_deep(v) for k, v in value.items()}
    return value

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
    navigation = item.get("navigation", {})
    media = item.get("media", {})
    business_info = item.get("business_info", {})

    title = fix_encoding(metadata.get("title", ""))
    description = fix_encoding(metadata.get("description", ""))

    h1 = " | ".join([fix_encoding(h) for h in headings.get("h1", [])])
    h2 = " | ".join([fix_encoding(h) for h in headings.get("h2", [])])
    h3 = " | ".join([fix_encoding(h) for h in headings.get("h3", [])])

    paragraph_text = " ".join([fix_encoding(p.strip()) for p in paragraphs])

    footer_links = " | ".join([
        fix_encoding(link) for link in navigation.get("footer_links", []) if link
    ])

    # Recherche d'un champ email dans les formulaires
    email_placeholder = ""
    for form_fields in item.get("forms", {}).get("details", []):
        for field in form_fields:
            if field.get("type") == "email":
                email_placeholder = fix_encoding(field.get("placeholder", ""))

    row = {
        "url": url,
        "title": title,
        "description": description,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "content": paragraph_text,
        "footer_links": footer_links,
        "email_placeholder": email_placeholder,
        "media": json.dumps(fix_encoding_deep(media), ensure_ascii=False),
        "business_info": json.dumps(fix_encoding_deep(business_info), ensure_ascii=False),
    }

    rows.append(row)

def normalize_url(url):
    """Normalise une URL pour comparer les doublons (minuscules + suppression des espaces)."""
    return (url or "").strip().lower()


def load_existing_rows(filename="structured_output.csv"):
    """
    Charge les lignes déjà présentes dans le CSV s'il existe.
    Retourne une liste de dictionnaires.
    """
    try:
        with open(filename, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return [dict(row) for row in reader]
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Erreur lors de la lecture de {filename} : {e}")
        return []


def merge_with_existing(new_rows, filename="structured_output.csv"):
    """
    Fusionne les nouvelles lignes avec celles déjà présentes dans le CSV.
    Les doublons (même URL) sont ignorés, mais les données existantes sont conservées.
    """
    existing_rows = load_existing_rows(filename)

    # Index des URLs déjà présentes pour éviter les doublons
    seen_urls = {normalize_url(row.get("url")) for row in existing_rows if row.get("url")}

    combined = list(existing_rows)

    added_count = 0
    for row in new_rows:
        url_key = normalize_url(row.get("url"))
        if url_key and url_key in seen_urls:
            continue  # URL déjà présente -> on la saute
        combined.append(row)
        seen_urls.add(url_key)
        added_count += 1

    return combined, len(existing_rows), added_count


if not rows:
    print("Aucune donnée à exporter. Vérifiez le fichier scraped_data.json.")
else:
    # Fusionner avec les données déjà conservées (anciennes saisons)
    combined_rows, previous_count, added_count = merge_with_existing(rows)

    # En-têtes (basés sur les nouvelles lignes, mais on garde l'ordre de la première ligne)
    fieldnames = list(rows[0].keys())

    # Sauvegarde CSV (fusion complète : anciennes + nouvelles données)
    with open("structured_output.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(combined_rows)

    print(
        f"Fichier CSV créé : structured_output.csv "
        f"({previous_count} lignes conservées, {added_count} nouvelles ajoutées, "
        f"{len(combined_rows)} lignes au total)"
    )
