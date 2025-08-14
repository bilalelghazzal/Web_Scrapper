import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import time
import queue
import xml.etree.ElementTree as ET

def get_sitemap_urls(sitemap_url):
    try:
        print(f"Tentative de récupération du sitemap : {sitemap_url}")
        response = requests.get(sitemap_url, timeout=10)
        if response.status_code == 200:
            tree = ET.fromstring(response.content)
            urls = [url.text for url in tree.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
            print(f"Sitemap trouvé avec {len(urls)} URLs")
            return urls
        else:
            print(f"Sitemap non trouvé (code {response.status_code})")
            return []
    except Exception as e:
        print(f"Erreur lors de la lecture du sitemap : {e}")
        return []

def respect_robots_txt(base_url):
    rp = RobotFileParser()
    robots_url = urljoin(base_url, "robots.txt")
    print(f"Vérification du robots.txt : {robots_url}")
    
    try:
        rp.set_url(robots_url)
        rp.read()
        print("robots.txt trouvé et lu")
    except Exception as e:
        print(f"Erreur lors de la lecture du robots.txt : {e}")
        # Si on ne peut pas lire robots.txt, on assume que tout est autorisé
        def can_fetch(user_agent, url):
            return True
        return can_fetch
    
    def can_fetch(user_agent, url):
        return rp.can_fetch(user_agent, url)
    
    return can_fetch

class WebCrawler:
    def __init__(self, base_url, max_depth=3):
        self.base_url = base_url
        self.visited_urls = set()
        self.queue = queue.Queue()
        self.max_depth = max_depth
        self.depth_map = {}
        self.can_fetch = respect_robots_txt(base_url)
        self.session = requests.Session()
        # Ajouter des headers pour éviter d'être bloqué
        self.session.headers.update({
            'User-Agent': 'YOUR_USER_AGENT'
        })

    def is_valid_url(self, url):
        # Vérifier que l'URL est bien formée et appartient au même domaine
        parsed = urlparse(url)
        base_parsed = urlparse(self.base_url)
        
        # Vérifier que l'URL a un schéma et un domaine
        if not parsed.scheme or not parsed.netloc:
            return False
            
        # Vérifier que l'URL appartient au même domaine (optionnel, décommentez si nécessaire)
        # if parsed.netloc != base_parsed.netloc:
        #     return False
            
        # Vérifier robots.txt
        return self.can_fetch("*", url)

    def enqueue_url(self, url, depth):
        # Ajouter l'URL à la queue si elle n'a jamais été visitée
        if url not in self.visited_urls and depth <= self.max_depth:
            self.queue.put((url, depth))
            self.depth_map[url] = depth

    def crawl(self, max_pages=10):
        # Essayer de récupérer les URLs du sitemap
        sitemap_urls = get_sitemap_urls(urljoin(self.base_url, "sitemap.xml"))
        
        if sitemap_urls:
            print(f"Ajout de {len(sitemap_urls)} URLs du sitemap à la queue")
            for url in sitemap_urls:
                self.enqueue_url(url, 0)
        else:
            # Si pas de sitemap, commencer par l'URL de base
            print("Aucun sitemap trouvé, démarrage depuis l'URL de base")
            self.enqueue_url(self.base_url, 0)

        pages_crawled = 0
        while not self.queue.empty() and pages_crawled < max_pages:
            current_url, depth = self.queue.get()
            if current_url in self.visited_urls:
                continue
            
            print(f"Crawling : {current_url} (Profondeur : {depth})")
            self.visited_urls.add(current_url)
            pages_crawled += 1
            
            try:
                response = self.session.get(current_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extraire tous les liens de la page
                    links_found = 0
                    for link in soup.find_all('a', href=True):
                        absolute_link = urljoin(current_url, link['href'])
                        if self.is_valid_url(absolute_link):
                            new_depth = depth + 1
                            self.enqueue_url(absolute_link, new_depth)
                            links_found += 1
                    
                    print(f"  -> {links_found} liens valides trouvés")
                else:
                    print(f"  -> Erreur HTTP {response.status_code}")
                
                # Pause pour éviter de surcharger le serveur
                time.sleep(1)
            
            except Exception as e:
                print(f"  -> Erreur lors du crawling de {current_url}: {e}")

# Exemple d'utilisation
if __name__ == "__main__":
    base_url = input("Entrez l'URL de base à crawler : ")
    crawler = WebCrawler(base_url, max_depth=2)
    crawler.crawl(max_pages=10)
    crawled_urls = list(crawler.visited_urls)
    
    with open("crawled_urls.txt", "w", encoding='utf-8') as f:
        for url in crawled_urls:
            f.write(url + "\n")
    
    print(f"Crawling terminé. {len(crawled_urls)} URLs sauvegardées dans 'crawled_urls.txt'")