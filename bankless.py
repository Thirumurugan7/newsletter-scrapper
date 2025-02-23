import time
import logging
import os
from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions
from bs4 import BeautifulSoup
import json
import random

class BanklessScraper:
    def __init__(self):
        self.base_url = "https://www.bankless.com"
        self.blog_url = f"{self.base_url}/read"
        self.driver = None
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('bankless_scraper.log', mode='w')
            ]
        )

    def random_sleep(self, min_seconds=2, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def init_driver(self):
        """Initialize ChromiumPage with proper options"""
        try:
            logging.info("Initializing driver...")
            
            # Configure Chrome options
            options = ChromiumOptions().auto_port()
            arguments = [
                "-no-first-run",
                "-force-color-profile=srgb",
                "-metrics-recording-only",
                "-password-store=basic",
                "-use-mock-keychain",
                "-export-tagged-pdf",
                "-no-default-browser-check",
                "-disable-background-mode",
                "-enable-features=NetworkService,NetworkServiceInProcess",
                "-disable-features=FlashDeprecationWarning",
                "-disable-gpu",
                "-accept-lang=en-US",
            ]
            
            for argument in arguments:
                options.set_argument(argument)
            
            # Initialize driver
            self.driver = ChromiumPage(addr_or_opts=options)
            
            # Access site and bypass Cloudflare
            logging.info("Accessing site and bypassing Cloudflare...")
            self.driver.get(self.base_url)
            
            cf_bypasser = CloudflareBypasser(self.driver)
            cf_bypasser.bypass()
            
            logging.info("Successfully bypassed Cloudflare!")
            self.random_sleep(3, 5)
            
            return True
            
        except Exception as e:
            logging.error(f"Error initializing driver: {e}")
            return False

    def scrape_articles(self):
        """Scrape all articles from the blog page"""
        try:
            logging.info("\nAccessing blog page...")
            self.driver.get(self.blog_url)
            self.random_sleep(3, 5)
            
            articles = []
            
            # Get page content
            soup = BeautifulSoup(self.driver.html, 'html.parser')
            
            # Find the content list container
            content_list = soup.find('div', {'class': 'contentList', 'id': 'filterAjax'})
            if not content_list:
                logging.error("Could not find content list container")
                return []
            
            # Find all article blocks
            article_blocks = content_list.find_all('a', {'class': 'item articleBlockSmall'})
            
            for block in article_blocks:
                article = {}
                
                # Extract article URL
                article['url'] = block['href']
                if not article['url'].startswith('http'):
                    article['url'] = self.base_url + article['url']
                    
                # Extract metadata
                content_span = block.find('span', {'class': 'content'})
                if content_span:
                    # Get title
                    title_span = content_span.find('span', {'class': 'title'})
                    article['title'] = title_span.get_text().strip() if title_span else ''
                    
                    # Get subtitle/description
                    subtitle_span = content_span.find('span', {'class': 'subTitle'})
                    article['description'] = subtitle_span.get_text().strip() if subtitle_span else ''
                    
                    # Get metadata (author, date, read time)
                    meta_span = content_span.find('span', {'class': 'topMeta'})
                    if meta_span:
                        # Get author
                        author_span = meta_span.find('span', {'class': 'author'})
                        if author_span and author_span.find('strong'):
                            article['author'] = author_span.find('strong').get_text().strip()
                        
                        # Get publish date and read time from meta text
                        meta_text = meta_span.get_text().strip()
                        meta_parts = [p.strip() for p in meta_text.split('•')]
                        if len(meta_parts) >= 2:
                            article['published'] = meta_parts[1].strip()
                        if len(meta_parts) >= 3:
                            article['read_time'] = meta_parts[2].strip()
                    
                    # Get categories
                    categories = content_span.find_all('span', {'class': 'category'})
                    article['categories'] = [cat.get_text().strip() for cat in categories]
                
                # Get thumbnail image
                image_span = block.find('span', {'class': 'image'})
                if image_span and image_span.find('img'):
                    article['thumbnail'] = image_span.find('img')['src']
                
                logging.info(f"Scraped: {article['title']}")
                articles.append(article)
                
                if len(articles) % 10 == 0:
                    logging.info(f"Saved {len(articles)} articles to bankless_articles.json")
                    self.save_articles(articles)
                    
            logging.info(f"Found {len(articles)} articles")
            self.save_articles(articles)
            return articles
            
        except Exception as e:
            logging.error(f"Error scraping articles: {e}")
            return []

    def scrape_article_content(self, articles):
        """Scrape full content for each article"""
        logging.info(f"\nScraping content for {len(articles)} articles...")
        
        for i, article in enumerate(articles):
            try:
                logging.info(f"\nScraping article {i+1}/{len(articles)}: {article['title']}")
                
                # Access article page
                self.driver.get(article['url'])
                self.random_sleep(3, 5)
                
                # Parse content
                soup = BeautifulSoup(self.driver.html, 'html.parser')
                
                # Find content container - updated selector
                content_elem = soup.select_one('#article .contents')
                if not content_elem:
                    logging.info("Could not find content container")
                    continue
                
                # Extract content and metadata
                article['full_content'] = content_elem.get_text(separator='\n').strip()
                
                # Get all images in the article
                article['content_images'] = [
                    img['src'] for img in content_elem.select('img')
                ]
                
                logging.info(f"Successfully scraped {len(article['full_content'])} chars")
                
                # Save progress
                self.save_articles(articles, filename="bankless_articles_full.json")
                self.random_sleep(2, 4)
                
            except Exception as e:
                logging.error(f"Error scraping article content: {e}")
                continue

    def save_articles(self, articles, filename="bankless_articles.json"):
        """Save articles to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved {len(articles)} articles to {filename}")

    def scrape(self):
        """Main scraping method"""
        try:
            if not self.init_driver():
                logging.error("Failed to initialize driver")
                return
            
            # Scrape article list
            articles = self.scrape_articles()
            if not articles:
                logging.error("No articles found")
                return
            
            # Scrape full content
            self.scrape_article_content(articles)
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    scraper = BanklessScraper()
    scraper.scrape()

if __name__ == "__main__":
    main()