import requests
import json
import time
import random
import os
from bs4 import BeautifulSoup
import sys
import re

class SimpleBanklessScraper:
    def __init__(self):
        self.base_url = "https://www.bankless.com"
        self.blog_url = f"{self.base_url}/read"
        self.cookies_file = "browser_cookies.json"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'Sec-Ch-Ua': '"Google Chrome";v="120", "Chromium";v="120", "Not-A.Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        self.session = requests.Session()

    def random_sleep(self, min_seconds=1, max_seconds=3):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def manual_browser_flow(self):
        """Guide the user through a manual browser flow"""
        print("\n==== MANUAL BROWSER ACCESS REQUIRED ====")
        print("This script will use your browser's cookies after you've manually accessed the site.")
        print("\nPlease follow these steps in order:")
        print("1. Open Chrome and ensure you're logged out of all accounts")
        print("2. Clear your browser cookies and cache")
        print("3. Visit https://www.bankless.com in Chrome")
        print("4. Complete any Cloudflare challenges until you can see the actual site content")
        print("5. Once you're on the main page, take these steps to export cookies:")
        print("   a. Press F12 to open Developer Tools")
        print("   b. Go to the 'Network' tab")
        print("   c. Refresh the page (F5)")
        print("   d. Click on the first request to bankless.com")
        print("   e. In the Headers tab, find the 'Cookie' header")
        print("   f. Copy the entire cookie string value")
        
        cookie_string = input("\nPaste the Cookie header value here: ")
        
        if not cookie_string.strip():
            print("Error: No cookie string provided")
            return False
            
        # Parse cookie string into a dict format
        cookies = {}
        for cookie_part in cookie_string.split(';'):
            if '=' in cookie_part:
                name, value = cookie_part.strip().split('=', 1)
                cookies[name] = value
        
        # Save cookies to file
        with open(self.cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2)
            
        print(f"Saved {len(cookies)} cookies to {self.cookies_file}")
        return True
        
    def load_cookies(self):
        """Load cookies into the session"""
        if not os.path.exists(self.cookies_file):
            print(f"Cookie file {self.cookies_file} not found")
            return False
            
        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                
            if not cookies:
                print("Cookie file is empty")
                return False
                
            # Set cookies in the session
            self.session.cookies.update(cookies)
            print(f"Loaded {len(cookies)} cookies into session")
            return True
            
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return False
            
    def scrape(self):
        """Simple request-based scraping approach"""
        # First ensure we have cookies
        if not os.path.exists(self.cookies_file):
            print("No cookies file found.")
            if not self.manual_browser_flow():
                print("Cannot continue without valid cookies.")
                return
                
        # Load cookies
        if not self.load_cookies():
            print("Failed to load cookies.")
            if not self.manual_browser_flow():
                print("Cannot continue without valid cookies.")
                return
            
            # Try loading again
            if not self.load_cookies():
                print("Still failed to load cookies. Exiting.")
                return
        
        # First, try to access the main page
        print("\nTesting access to main page...")
        try:
            response = self.session.get(self.base_url, headers=self.headers, timeout=30)
            
            # Save response for inspection
            with open("main_page_response.html", "w", encoding="utf-8") as f:
                f.write(response.text)
                
            print(f"Main page response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error: Got status code {response.status_code}")
                if "cloudflare" in response.text.lower() or "challenge" in response.text.lower():
                    print("Cloudflare protection detected in response")
                    if not self.manual_browser_flow():
                        return
                    
                    # Try again with new cookies
                    if not self.load_cookies():
                        print("Still failed to load cookies. Exiting.")
                        return
                        
                    # Try the request again
                    response = self.session.get(self.base_url, headers=self.headers, timeout=30)
                    if response.status_code != 200:
                        print(f"Still getting error status: {response.status_code}")
                        print("Please try running the script again after accessing the site manually")
                        return
                else:
                    print("Unknown error accessing the site")
                    return
            
            print("Successfully accessed main page!")
            
            # Now access the blog page
            print("\nAccessing blog page...")
            self.random_sleep(2, 4)
            
            blog_response = self.session.get(self.blog_url, headers=self.headers, timeout=30)
            
            with open("blog_page_response.html", "w", encoding="utf-8") as f:
                f.write(blog_response.text)
                
            print(f"Blog page response status: {blog_response.status_code}")
            
            if blog_response.status_code != 200:
                print(f"Error accessing blog page: {blog_response.status_code}")
                return
                
            # Parse and extract articles
            print("\nExtracting articles from blog page...")
            articles = self.extract_articles(blog_response.text)
            
            if not articles:
                print("No articles found. Check blog_page_response.html for debugging.")
                return
                
            print(f"Found {len(articles)} articles")
            
            # Save articles
            with open("bankless_articles.json", "w", encoding="utf-8") as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
                
            print(f"Saved {len(articles)} articles to bankless_articles.json")
            
            # Optionally scrape individual articles
            if articles and input("\nWould you like to scrape full article content? (y/n): ").lower() == 'y':
                self.scrape_article_content(articles)
            
        except requests.RequestException as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    
    def extract_articles(self, html_content):
        """Extract article information from blog page HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            articles = []
            
            # Try different article container patterns
            article_containers = []
            
            # Pattern 1: Standard article elements
            article_elements = soup.find_all('article')
            if article_elements:
                article_containers.extend(article_elements)
                print(f"Found {len(article_elements)} standard article elements")
            
            # Pattern 2: Post cards
            post_cards = soup.select('.post-card, .blog-post, .article-card, .post-item')
            if post_cards:
                article_containers.extend(post_cards)
                print(f"Found {len(post_cards)} post card elements")
                
            # Pattern 3: Grid items or list items containing articles
            grid_items = soup.select('.grid-item, .post-grid-item, li.post, .post-list-item')
            if grid_items:
                article_containers.extend(grid_items)
                print(f"Found {len(grid_items)} grid/list items")
                
            # If still no containers found, look for content blocks with titles and links
            if not article_containers:
                # Find all heading elements with links
                heading_links = []
                for heading in soup.find_all(['h1', 'h2', 'h3']):
                    link = heading.find('a')
                    if link and link.get('href'):
                        # Get the parent container
                        parent = heading.parent
                        if parent and parent.name != 'body':
                            heading_links.append(parent)
                
                if heading_links:
                    article_containers.extend(heading_links)
                    print(f"Found {len(heading_links)} content blocks with headings and links")
            
            # Process each container
            for container in article_containers:
                article = {}
                
                # Try to find title
                title_elem = container.find(['h1', 'h2', 'h3', 'h4']) or container.select_one('.title, .post-title, .entry-title')
                if title_elem:
                    article['title'] = title_elem.get_text().strip()
                else:
                    continue  # Skip if no title
                
                # Try to find link
                link = None
                if title_elem:
                    link = title_elem.find('a')
                if not link:
                    link = container.find('a')
                
                if link and link.get('href'):
                    url = link['href']
                    # Make relative URLs absolute
                    if url.startswith('/'):
                        url = self.base_url + url
                    article['url'] = url
                else:
                    continue  # Skip if no link
                
                # Try to find date
                date_elem = container.find('time') or container.select_one('.date, .post-date, .published')
                if date_elem:
                    article['date'] = date_elem.get_text().strip()
                
                # Try to find excerpt
                excerpt_elem = container.find('p') or container.select_one('.excerpt, .summary, .description')
                if excerpt_elem and excerpt_elem != title_elem:
                    article['excerpt'] = excerpt_elem.get_text().strip()
                
                # Add if we have at least title and URL
                if article.get('title') and article.get('url'):
                    articles.append(article)
            
            # De-duplicate based on URL
            unique_articles = []
            seen_urls = set()
            
            for article in articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            print(f"Found {len(unique_articles)} unique articles after deduplication")
            return unique_articles
            
        except Exception as e:
            print(f"Error extracting articles: {e}")
            return []
    
    def scrape_article_content(self, articles):
        """Scrape full content for each article"""
        print(f"\nScraping content for {len(articles)} articles...")
        
        for i, article in enumerate(articles):
            try:
                print(f"Scraping article {i+1}/{len(articles)}: {article['title']}")
                url = article['url']
                
                # Random delay between requests
                self.random_sleep(3, 7)
                
                response = self.session.get(url, headers=self.headers, timeout=30)
                
                if response.status_code != 200:
                    print(f"  Error: Got status {response.status_code}")
                    continue
                
                # Parse content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to find the main content container
                content_selectors = [
                    'article', 
                    '.post-content',
                    '.entry-content',
                    '.article-content',
                    '.content',
                    'main'
                ]
                
                content_elem = None
                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        break
                
                if not content_elem:
                    print("  Could not find content container")
                    continue
                
                # Clean up the content (remove unnecessary elements)
                for elem in content_elem.select('.related-posts, .share-buttons, .author-bio, .comments, nav, aside, .sidebar'):
                    elem.decompose()
                
                # Get text content
                article['full_content'] = content_elem.get_text(separator='\n').strip()
                
                # Try to get author
                author_elem = soup.select_one('.author, .post-author, .entry-author, [rel="author"]')
                if author_elem:
                    article['author'] = author_elem.get_text().strip()
                
                # Try to get published date if not already present
                if 'date' not in article:
                    date_elem = soup.find('time') or soup.select_one('.date, .published, .post-date')
                    if date_elem:
                        article['date'] = date_elem.get_text().strip()
                
                print(f"  Success: Extracted {len(article['full_content'])} characters")
                
                # Save progress after each article
                with open("bankless_articles_with_content.json", "w", encoding="utf-8") as f:
                    json.dump(articles, f, indent=2, ensure_ascii=False)
                
            except Exception as e:
                print(f"  Error scraping article: {e}")
        
        print(f"\nCompleted scraping content for {len(articles)} articles")
        print("Saved results to bankless_articles_with_content.json")


def main():
    scraper = SimpleBanklessScraper()
    scraper.scrape()

if __name__ == "__main__":
    main()