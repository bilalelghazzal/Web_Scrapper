# Web Scrapper

This project is a web scraping toolkit designed to crawl websites, extract structured data, and clean the results for further analysis. It includes scripts for crawling, scraping, data cleaning, and exporting to CSV.

## Features
- Crawl and collect URLs from target websites
- Scrape metadata, content, navigation, and media information
- Clean and transform scraped data
- Export cleaned data to CSV for analysis

## Main Files
- `crawler.py`: Crawls websites and collects URLs ,(Make Sure to wrtie YOUR_USER_AGENT "Line 57" )
- `scrapper.py` / `scrapper_2.py`: Scrapes data from collected URLs
- `clean_json.py` / `clean_data_2.py`: Cleans and processes scraped data
- `scraped_data.json`: Raw scraped data in JSON format
- `structured_output.csv`, `jumia_cleaned_data.csv`: Cleaned data in CSV format

## Requirements
Install dependencies with:
```sh
pip install -r requirements.txt
```

## Usage
1. **Crawl URLs:**
   ```sh
   python crawler.py
   ```
2. **Scrape Data:**
   ```sh
   python scrapper.py
   # or
   python scrapper_2.py
   ```
3. **Clean Data:**
   ```sh
   python clean_data_2.py
   # or
   python clean_json.py
   ```

## Output
- Cleaned data will be saved as CSV files (e.g., `jumia_cleaned_data.csv`).
