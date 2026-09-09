import json
import csv
import io
import os

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
    url = fix_encoding(item.get("url", ""))
    title = fix_encoding(item.get("title", ""))
    email = fix_encoding(item.get("email", ""))
    phone = fix_encoding(item.get("phone", ""))
    address = fix_encoding(item.get("address", ""))

    # On conserve uniquement les 5 champs extraits par le scrapper :
    # titre, email, téléphone et adresse
    row = {
        "url": url,
        "title": title,
        "email": email,
        "phone": phone,
        "address": address,
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
    - Les URLs absentes sont ajoutées.
    - Les URLs déjà présentes sont mises à jour : les champs vides de la ligne
      existante sont remplis avec les nouvelles données (si non vides).
    """
    existing_rows = load_existing_rows(filename)

    # Index des URLs déjà présentes -> position de la ligne dans `combined`
    seen_urls = {normalize_url(row.get("url")): idx
                 for idx, row in enumerate(existing_rows) if row.get("url")}

    combined = list(existing_rows)

    added_count = 0
    updated_count = 0
    skipped_count = 0
    for row in new_rows:
        url_key = normalize_url(row.get("url"))
        if not url_key:
            skipped_count += 1
            continue

        if url_key in seen_urls:
            # URL déjà présente : remplir les champs vides avec les nouvelles données
            idx = seen_urls[url_key]
            changed = False
            for field, value in row.items():
                if value and not combined[idx].get(field):
                    combined[idx][field] = value
                    changed = True
            if changed:
                updated_count += 1
        else:
            combined.append(row)
            seen_urls[url_key] = len(combined) - 1
            added_count += 1

    return combined, len(existing_rows), added_count, updated_count, skipped_count


def write_csv_atomic(rows, fieldnames, filename="structured_output.csv"):
    """
    Écrit le CSV en toute sécurité :
    - construit tout le contenu en mémoire d'abord,
    - puis remplace le fichier sur le disque uniquement si tout a réussi.
    Ainsi, une erreur ne laisse JAMAIS un fichier CSV vide ou corrompu.
    """
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)

    tmp_filename = filename + ".tmp"
    with open(tmp_filename, "w", encoding="utf-8", newline="") as f:
        f.write(buffer.getvalue())

    # Remplacement atomique (Windows-safe) : on supprime l'ancien puis on
    # renomme le fichier temporaire, seulement après écriture réussie.
    if os.path.exists(filename):
        os.remove(filename)
    os.rename(tmp_filename, filename)


if not rows:
    print("Aucune donnée à exporter. Vérifiez le fichier scraped_data.json.")
else:
    # Fusionner avec les données déjà conservées (anciennes lignes)
    combined_rows, previous_count, added_count, updated_count, skipped_count = merge_with_existing(rows)

    # En-têtes (basés sur les nouvelles lignes, mais on garde l'ordre de la première ligne)
    fieldnames = list(rows[0].keys())

    # Sauvegarde CSV (fusion complète : anciennes + nouvelles données)
    # Écriture en toute sécurité : le fichier n'est remplacé qu'en cas de succès,
    # donc jamais de CSV vide en cas d'erreur.
    write_csv_atomic(combined_rows, fieldnames)

    if skipped_count:
        print(f"Attention : {skipped_count} lignes ignorées (champ 'url' manquant ou vide).")

    print(
        f"Fichier CSV créé : structured_output.csv "
        f"({previous_count} lignes conservées, {added_count} nouvelles ajoutées, "
        f"{updated_count} mises à jour, {len(combined_rows)} lignes au total)"
    )
