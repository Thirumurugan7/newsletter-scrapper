import json
import time
import random
import logging
from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions
from bs4 import BeautifulSoup

class BeaconsScraper:
    def __init__(self):
        self.base_url = "https://beacons.ai"
        self.blog_url = f"{self.base_url}/i/beacons-blog"
        self.driver = None

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('beacons_scraper.log', mode='w')
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

    def scrape_article_content(self, url):
        """Scrape individual blog content"""
        try:
            self.driver.get(url)
            self.random_sleep(3, 5)
            
            soup = BeautifulSoup(self.driver.html, 'html.parser')
            
            # Get article container
            article_container = soup.find('div', {'class': 'article_container'})
            if not article_container:
                logging.info("Could not find article container")
                return {}
            
            # Get header info
            header = article_container.find('div', {'class': 'article_head'})
            article_data = {}
            
            if header:
                # Get metadata (date and category)
                details = header.find('div', {'class': 'article_detailsblock'})
                if details:
                    tags = details.find_all('div', {'class': 'article_tag'})
                    article_data['date'] = tags[0].text.strip() if tags else ""
                    article_data['category'] = tags[2].text.strip() if len(tags) > 2 else ""
                
                # Get title
                title = header.find('h1', {'class': 'article_heading'})
                article_data['title'] = title.text.strip() if title else ""
                
                # Get author info
                author_container = header.find('div', {'class': 'author_container'})
                if author_container:
                    author_name = author_container.find('div', {'class': 'cu_author_name'})
                    author_title = author_container.find('div', {'class': 'cu_author_title'})
                    author_image = author_container.find('img', {'class': 'cu_author_image'})
                    
                    article_data['author'] = {
                        'name': author_name.text.strip() if author_name else "",
                        'title': author_title.text.strip() if author_title else "",
                        'image': author_image['src'] if author_image else ""
                    }
                
                # Get header image
                masthead = header.find('div', {'class': 'article_masthead'})
                if masthead and 'style' in masthead.attrs:
                    image_url = masthead['style'].split('url("')[1].split('")')[0] if 'url(' in masthead['style'] else ""
                    article_data['header_image'] = image_url
            
            # Get main content
            content_container = article_container.find('div', {'class': 'cu_article w-richtext'})
            if content_container:
                # Extract structured content
                content_elements = []
                
                for element in content_container.children:
                    if element.name:  # Skip NavigableString objects
                        element_data = {
                            'type': element.name,
                            'content': element.get_text(separator='\n').strip()
                        }
                        
                        # Handle special elements
                        if element.name == 'blockquote':
                            element_data['type'] = 'quote'
                        elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                            element_data['type'] = 'heading'
                            element_data['level'] = element.name[1]
                        elif element.name == 'img':
                            element_data['type'] = 'image'
                            element_data['src'] = element.get('src', '')
                            element_data['alt'] = element.get('alt', '')
                        elif element.name in ['ul', 'ol']:
                            element_data['type'] = 'list'
                            element_data['items'] = [li.text.strip() for li in element.find_all('li')]
                        
                        content_elements.append(element_data)
                
                article_data['content'] = content_elements
                article_data['full_text'] = content_container.get_text(separator='\n').strip()
                
                # Get embedded media
                embeds = content_container.find_all(['iframe', 'blockquote'])
                if embeds:
                    article_data['embedded_media'] = [
                        {
                            'type': 'video' if embed.name == 'iframe' else 'social',
                            'src': embed.get('src', '') if embed.name == 'iframe' else embed.get('cite', '')
                        } for embed in embeds
                    ]
            
            return article_data
            
        except Exception as e:
            logging.error(f"Error scraping article content: {e}")
            return {}

    def scrape_blogs(self):
        """Scrape all blogs from the blog page including pagination"""
        try:
            logging.info("\nAccessing blog page...")
            self.driver.get(self.blog_url)
            self.random_sleep(3, 5)
            
            all_blogs = []
            page = 1
            last_item_count = 0
            max_retries = 3
            retry_count = 0
            
            while True:
                logging.info(f"\nScraping page {page}...")
                
                # Get page content
                soup = BeautifulSoup(self.driver.html, 'html.parser')
                
                # Find blog grid container
                blog_grid = soup.find('div', {'class': 'grid w-dyn-items'})
                if not blog_grid:
                    logging.error("Could not find blog grid container")
                    break
                
                # Find all blog items
                blog_items = blog_grid.find_all('div', {'class': 'grid_item w-dyn-item'})
                current_item_count = len(blog_items)
                
                if not blog_items:
                    logging.info("No blog items found")
                    break
                    
                if current_item_count == last_item_count:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logging.info("No new items loaded after multiple attempts - reached last page")
                        break
                    logging.info(f"No new items loaded, retrying... ({retry_count}/{max_retries})")
                    continue
                
                logging.info(f"Found {len(blog_items)} blogs on page {page}")
                
                # Process only new items
                new_items = blog_items[last_item_count:]
                for idx, item in enumerate(new_items, last_item_count + 1):
                    try:
                        # Extract blog metadata
                        link_elem = item.find('a', {'class': 'blog_linkblock'})
                        title_elem = item.find('div', {'class': 'blog_title'})
                        
                        # Extract category and date from info wrapper
                        info_wrapper = item.find('div', {'class': 'blog-featured-card-infowrapper'})
                        category_elem = info_wrapper.find('div', {'class': 'blog_category'}) if info_wrapper else None
                        date_elems = info_wrapper.find_all('div', {'class': 'blog_date'}) if info_wrapper else []
                        
                        # Get image URL from background-image style
                        image_elem = item.find('div', {'class': 'blog_cover_img'})
                        image_url = ""
                        if image_elem and 'style' in image_elem.attrs:
                            style = image_elem['style']
                            if 'url(' in style:
                                image_url = style.split('url("')[1].split('")')[0]
                        
                        blog_data = {
                            "blog_id": len(all_blogs) + 1,
                            "source": "Beacons",
                            "title": title_elem.text.strip() if title_elem else "",
                            "url": link_elem['href'] if link_elem else "",
                            "category": category_elem.text.strip() if category_elem else "",
                            "publication_date": date_elems[-1].text.strip() if date_elems else "",
                            "image": image_url
                        }
                        
                        # Make URL absolute if needed
                        if blog_data['url'] and not blog_data['url'].startswith('http'):
                            blog_data['url'] = self.base_url + blog_data['url']
                        
                        # Get blog content
                        if blog_data['url']:
                            logging.info(f"\nScraping blog {len(all_blogs)+1}: {blog_data['title']}")
                            content_data = self.scrape_article_content(blog_data['url'])
                            blog_data.update(content_data)
                            
                        all_blogs.append(blog_data)
                        
                        # Save progress periodically
                        if len(all_blogs) % 5 == 0:
                            self.save_blogs(all_blogs)
                            
                    except Exception as e:
                        logging.error(f"Error scraping blog: {str(e)}")
                        continue
                
                # Update last item count
                last_item_count = current_item_count
                
                # Scroll to load more items
                self.driver.execute_script("""
                    window.scrollTo({
                        top: document.body.scrollHeight,
                        behavior: 'smooth'
                    });
                """)
                
                # Wait for new content with timeout
                self.random_sleep(5, 8)  # Longer wait for content load
                
                page += 1
                retry_count = 0  # Reset retry count after successful load
            
            # Final save
            self.save_blogs(all_blogs)
            logging.info(f"\nSuccessfully scraped {len(all_blogs)} blogs across {page} pages!")
            
            return all_blogs
            
        except Exception as e:
            logging.error(f"Error during scraping: {str(e)}")
            return []

    def save_blogs(self, blogs, filename="beacons_blogs.json"):
        """Save blogs to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(blogs, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved {len(blogs)} blogs to {filename}")

    def scrape(self):
        """Main scraping method"""
        try:
            if not self.init_driver():
                logging.error("Failed to initialize driver")
                return
            
            self.scrape_blogs()
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    scraper = BeaconsScraper()
    scraper.scrape()

if __name__ == "__main__":
    main() 