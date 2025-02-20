import json
import time
import random
from playwright.sync_api import sync_playwright

class ChainOfThoughtScraper:
    def __init__(self):
        self.base_url = "https://www.chainofthought.co"

    def random_sleep(self, min_seconds=2, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def scrape_section(self, page, section_data):
        section_id, section_name, item_class = section_data
        articles = []
        page_num = 1
        
        while True:
            print(f"Scraping {section_name} - page {page_num}...")
            
            try:
                # Wait for section content to load
                section_selector = f"div[data-w-id='{section_id}']"
                page.wait_for_selector(f"{section_selector} .w-dyn-items", timeout=30000)
                self.random_sleep(2)
                
                # Extract articles from current page
                new_articles = page.evaluate("""
                    function(params) {
                        const section = document.querySelector(params.selector);
                        if (!section) return [];
                        
                        const articles = [];
                        section.querySelectorAll('.' + params.itemClass).forEach(item => {
                            const link = item.querySelector('a.blog-item');
                            const title = item.querySelector('.blog-title');
                            const description = item.querySelector('.blog-description, .blog-description-copy');
                            const date = item.querySelector('.blog-date');
                            const author = item.querySelector('.blog-author');
                            const image = item.querySelector('img.blog-image');
                            
                            if (title && link) {
                                articles.push({
                                    title: title.innerText.trim(),
                                    url: new URL(link.getAttribute('href'), window.location.origin).href,
                                    description: description ? description.innerText.trim() : '',
                                    date: date ? date.innerText.trim() : '',
                                    author: author ? author.innerText.replace('By ', '').trim() : '',
                                    image: image ? image.src : null,
                                    section: params.sectionName
                                });
                            }
                        });
                        return articles;
                    }
                """, {
                    'selector': section_selector,
                    'itemClass': item_class,
                    'sectionName': section_name
                })
                
                if new_articles:
                    articles.extend(new_articles)
                    print(f"Found {len(new_articles)} articles in {section_name}")
                
                # Look for next button within this section's pagination
                pagination_query = f"{section_selector} .w-pagination-wrapper a[aria-label='Next Page']"
                next_button = page.locator(pagination_query)
                
                if next_button.count() > 0 and next_button.is_visible():
                    next_button.click()
                    page_num += 1
                    self.random_sleep(3)
                    page.wait_for_load_state('networkidle')
                else:
                    break
                    
            except Exception as e:
                print(f"Error in {section_name}: {str(e)}")
                page.screenshot(path=f"error_{section_name.lower().replace(' ', '_')}.png")
                break
                
        return articles

    def scrape_article_content(self, page, url):
        try:
            page.goto(url)
            # Wait for the main article content container
            page.wait_for_selector('.w-richtext', timeout=30000)
            self.random_sleep(2)
            
            return page.evaluate("""
                () => {
                    // Get the main content container
                    const content = document.querySelector('.w-richtext');
                    
                    // Get all images from the article
                    const images = Array.from(document.querySelectorAll('.w-richtext img')).map(img => ({
                        src: img.src,
                        alt: img.alt || ''
                    }));
                    
                    // Get metadata
                    const metadata = {
                        title: document.querySelector('h1')?.innerText.trim() || '',
                        date: document.querySelector('.blog-date')?.innerText.trim() || '',
                        author: document.querySelector('.blog-author')?.innerText.trim() || ''
                    };
                    
                    // Get all text content including headers and paragraphs
                    const textContent = Array.from(content.querySelectorAll('h1, h2, h3, h4, h5, h6, p, ul, ol, li, blockquote')).map(el => ({
                        type: el.tagName.toLowerCase(),
                        text: el.innerText.trim()
                    }));
                    
                    return {
                        metadata: metadata,
                        content: content ? content.innerText.trim() : '',
                        structured_content: textContent,
                        images: images
                    };
                }
            """)
        except Exception as e:
            print(f"Error scraping article content: {str(e)}")
            # Save error screenshot and HTML for debugging
            page.screenshot(path=f"error_article_{url.split('/')[-1]}.png")
            with open(f"error_article_{url.split('/')[-1]}.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            return None

    def scrape_all_content(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            try:
                all_articles = []
                
                # Go to research page
                print("\nAccessing research page...")
                page.goto(f"{self.base_url}/research")
                self.random_sleep(3)
                
                # Define sections with their exact IDs and classes
                sections = [
                    ('44155349-e036-0797-0045-d6d467f2fb0c', 'Protocol Research', 'collection-item-3'),
                    ('e59b43df-8869-4661-e1d1-a33ec6124626', 'Sector Analysis', 'collection-item-4'),
                    ('ee6e2cf9-5d53-5a62-f979-a79c0d1481b2', 'Weekly Newsletter', 'collection-item-5')
                ]
                
                # Scrape each section
                for section_data in sections:
                    print(f"\nScraping {section_data[1]} section...")
                    section_articles = self.scrape_section(page, section_data)
                    all_articles.extend(section_articles)
                
                print(f"\nFound total of {len(all_articles)} articles")
                
                # Save article list
                with open("cot_articles_list.json", "w", encoding="utf-8") as f:
                    json.dump(all_articles, f, indent=2, ensure_ascii=False)
                
                # Scrape full content for each article
                for idx, article in enumerate(all_articles, 1):
                    try:
                        print(f"\nScraping article {idx}/{len(all_articles)}")
                        print(f"URL: {article['url']}")
                        
                        content_data = self.scrape_article_content(page, article['url'])
                        if content_data:
                            article.update({
                                'full_content': content_data['content'],
                                'structured_content': content_data['structured_content'],
                                'content_images': content_data['images'],
                                'metadata': content_data['metadata']
                            })
                            print(f"Successfully scraped: {article['title']}")
                        
                        # Save progress after each article
                        with open("cot_articles_full.json", "w", encoding="utf-8") as f:
                            json.dump(all_articles, f, indent=2, ensure_ascii=False)
                        
                        self.random_sleep(2)
                        
                    except Exception as e:
                        print(f"Error scraping article: {str(e)}")
                        continue
                
                print(f"\nSuccessfully scraped {len(all_articles)} articles!")
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                page.screenshot(path="error.png")
                with open("error.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("Saved error.png and error.html for debugging")
                
            finally:
                browser.close()

def main():
    scraper = ChainOfThoughtScraper()
    scraper.scrape_all_content()

if __name__ == "__main__":
    main()
