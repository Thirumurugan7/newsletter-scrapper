from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import datetime
from typing import Dict, List
import re
from textblob import TextBlob
import spacy
import json
import time
from webdriver_manager.chrome import ChromeDriverManager

class NewsletterScraper:
    def __init__(self):
        self.url = "https://www.decentralised.co/archive"
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize the Chrome WebDriver with automatic ChromeDriver management
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Load spaCy model for entity extraction
        self.nlp = spacy.load("en_core_web_sm")

    def extract_entities(self, text: str) -> List[str]:
        """Extract key entities from text using spaCy"""
        doc = self.nlp(text)
        entities = []
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT"]:
                entities.append(ent.text)
        return list(set(entities))

    def get_sentiment(self, text: str) -> float:
        """Calculate sentiment score using TextBlob"""
        analysis = TextBlob(text)
        return analysis.sentiment.polarity

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def wait_and_find_element(self, by, value, timeout=10):
        """Wait for element to be present and return it"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def scroll_to_bottom(self):
        """Scroll to the bottom of the page to load all articles"""
        SCROLL_PAUSE_TIME = 2
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            
            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                break
            last_height = new_height
            print("Scrolling to load more articles...")

    def scrape_newsletters(self) -> List[Dict]:
        """Scrape newsletter data and return in structured format"""
        newsletters = []
        
        try:
            print("Fetching data from:", self.url)
            self.driver.get(self.url)
            time.sleep(5)  # Initial wait for page load
            
            # Wait for the first article to load
            self.wait_and_find_element(By.CSS_SELECTOR, "article.post-preview")
            
            # Scroll to load all articles
            print("Loading all articles...")
            self.scroll_to_bottom()
            
            # Get page source after all content is loaded
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            articles = soup.find_all('article', class_='post-preview')
            
            print(f"Found {len(articles)} articles")
            
            for idx, article in enumerate(articles, 1):
                try:
                    # Extract title and URL
                    title_elem = article.find('h3', class_='post-preview-title')
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    url_elem = article.find('a', href=True)
                    url = url_elem['href'] if url_elem else None
                    
                    if not url:
                        continue
                        
                    if not url.startswith('http'):
                        url = f"https://www.decentralised.co{url}"
                    
                    print(f"\nScraping article {idx}/{len(articles)}: {title}")
                    print(f"URL: {url}")  # Debug print
                    
                    # Visit the article page
                    self.driver.get(url)
                    time.sleep(3)  # Wait for content to load
                    
                    # Get the article content
                    article_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    # Extract date
                    date_elem = article_soup.find('time')
                    date_str = date_elem.get('datetime') if date_elem else ""
                    print(f"Date: {date_str}")  # Debug print
                    
                    # Extract content
                    content_elem = article_soup.find('div', class_='post-content')
                    content = content_elem.text.strip() if content_elem else ""
                    print(f"Content length: {len(content)}")  # Debug print
                    
                    # Extract author
                    author_elem = article_soup.find('a', class_='user-name')
                    author = author_elem.text.strip() if author_elem else "Decentralised Team"
                    print(f"Author: {author}")  # Debug print
                    
                    # Clean content
                    cleaned_content = self.clean_text(content)
                    
                    # Create newsletter data
                    newsletter_data = {
                        "newsletter_id": idx,
                        "source": "Decentralised.co",
                        "title": title,
                        "publication_date": date_str,
                        "content": cleaned_content,
                        "author": author,
                        "url": url,
                        "categories": ["blockchain", "crypto", "web3"],
                        "sentiment": self.get_sentiment(cleaned_content),
                        "entities": self.extract_entities(cleaned_content)
                    }
                    
                    newsletters.append(newsletter_data)
                    print(f"Successfully scraped: {title}")
                    
                except Exception as e:
                    print(f"Error processing article {idx}: {str(e)}")
                    continue
                
        except Exception as e:
            print(f"Error scraping newsletters: {str(e)}")
            
        finally:
            self.driver.quit()
            
        return newsletters

    def save_to_json(self, data: List[Dict], filename: str = "newsletters.json"):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

def main():
    scraper = NewsletterScraper()
    newsletters = scraper.scrape_newsletters()
    scraper.save_to_json(newsletters)
    print(f"Scraped {len(newsletters)} newsletters successfully!")

if __name__ == "__main__":
    main()