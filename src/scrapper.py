import requests
from bs4 import BeautifulSoup
import yaml
import logging
import os
import pandas as pd
from utils import setup_logging, create_directory


def load_config(config_file):
    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Configuration file {config_file} not found.")
        raise
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file {config_file}: {e}")
        raise

def read_excel(excel_file):
    try:
        df = pd.read_excel(excel_file)
        return df
    except Exception as e:
        logging.error(f"An error occurred while reading the Excel file {excel_file}: {e}")
        raise

def scrape_article(url, url_id, output_directory):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extracting the article title
        title_element = soup.find('h1', class_='entry-title')
        title = title_element.text.strip() if title_element else "No Title Found"
        article_body = soup.find('div', class_='td-post-content')
        footer = soup.find('footer')
        if footer:
            footer.decompose() 
        article_text = ""
        if article_body:
            for element in article_body.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol']):
                if element.name == 'h1' and element.text.strip():
                    article_text += f"\n\n{element.text.strip()}\n"  
                elif element.name in ['h2', 'h3', 'h4', 'h5', 'h6'] and element.text.strip():
                    article_text += f"\n\n{element.text.strip()}\n"  
                elif element.name == 'p' and element.text.strip():
                    article_text += element.text.strip() + '\n'  
                elif element.name in ['ul', 'ol']:
                    for li in element.find_all('li'):
                        if li.text.strip():
                            article_text += f"  - {li.text.strip()}\n" 
        else:
            logging.warning(f"No article content found for URL_ID: {url_id}")

        create_directory(output_directory)

        filename = os.path.join(output_directory, f'{url_id}.txt')
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(f"Title: {title}\n\n")
            file.write(article_text)

        logging.info(f"Article saved as {filename}")

    except requests.RequestException as e:
        logging.error(f"An error occurred while fetching the URL {url}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        
        
def main():
    try:
        config = load_config('config/config.yaml')
        url_details_file = config.get('scraping', {}).get('url_details')
        output_directory = config.get('scraping', {}).get('output_directory')
        log_directory = config.get('scraping', {}).get('log_directory')
        log_file = config.get('scraping', {}).get('log_file')
        
        create_directory(output_directory)
        create_directory(log_directory)
    
        setup_logging(log_file)
        
        data = read_excel(url_details_file)
        
        for index, row in data.iterrows():
            url_id = row.get('URL_ID')
            url = row.get('URL')
            
            if pd.notna(url_id) and pd.notna(url):
                scrape_article(url, url_id, output_directory)
            else:
                logging.warning(f"URL_ID or URL missing for row {index}: {row.to_dict()}")
    
    except Exception as e:
        logging.error(f"An error occurred in the main function: {e}")

if __name__ == "__main__":
    main()
    
    
    
   
