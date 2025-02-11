import json
import time
from playwright.sync_api import sync_playwright

class NewsletterScraper:
    def __init__(self):
        self.base_url = "https://www.decentralised.co"
        self.archive_url = f"{self.base_url}/archive"

    def scrape_newsletters(self):
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=False)
            page = browser.new_page()
            
            try:
                print(f"Accessing: {self.archive_url}")
                page.goto(self.archive_url)
                time.sleep(5)  # Initial wait
                
                print("Analyzing page structure...")
                
                # Take a screenshot for debugging
                page.screenshot(path="archive_page.png")
                
                # Wait for content to load
                page.wait_for_selector("h3", timeout=30000)
                
                # Scroll to load all content
                print("Loading all articles...")
                for _ in range(5):
                    page.keyboard.press('End')
                    time.sleep(3)  # Increased wait time
                    print("Scrolling...")
                
                # Debug: Print page title and URL
                print(f"\nPage Title: {page.title()}")
                print(f"Current URL: {page.url}")
                
                # First try to get all h3 elements (article titles)
                titles = page.evaluate("""
                    () => {
                        const titles = [];
                        document.querySelectorAll('h3').forEach(h3 => {
                            const link = h3.querySelector('a');
                            if (link && link.href.includes('/p/')) {
                                titles.push({
                                    title: h3.innerText.trim(),
                                    url: link.href
                                });
                            }
                        });
                        return titles;
                    }
                """)
                
                print(f"\nFound {len(titles)} articles through h3 elements")
                
                # If no titles found, try alternative selectors
                if not titles:
                    print("Trying alternative selectors...")
                    titles = page.evaluate("""
                        () => {
                            const articles = [];
                            // Try multiple possible selectors
                            const selectors = [
                                'a[href*="/p/"]',
                                '.post-preview a',
                                '[data-component="post-preview"] a',
                                '.post-preview-title'
                            ];
                            
                            selectors.forEach(selector => {
                                document.querySelectorAll(selector).forEach(element => {
                                    if (element.href && element.href.includes('/p/')) {
                                        articles.push({
                                            title: element.innerText.trim() || 'Untitled',
                                            url: element.href
                                        });
                                    }
                                });
                            });
                            
                            // Remove duplicates
                            return Array.from(new Set(articles.map(a => a.url)))
                                .map(url => articles.find(a => a.url === url));
                        }
                    """)
                
                print(f"Found {len(titles)} unique articles")
                
                # Debug: Print first few articles
                for i, article in enumerate(titles[:3], 1):
                    print(f"Article {i}: {article['title']} - {article['url']}")
                
                # Save the HTML for debugging
                with open("page_content.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                
                newsletters = []
                for idx, article in enumerate(titles, 1):
                    try:
                        print(f"\nScraping article {idx}/{len(titles)}")
                        print(f"URL: {article['url']}")
                        
                        # Visit the article page
                        page.goto(article['url'])
                        page.wait_for_selector('article', timeout=30000)
                        time.sleep(3)
                        
                        # Extract article data
                        article_data = page.evaluate("""
                            () => {
                                const getText = selector => {
                                    const el = document.querySelector(selector);
                                    return el ? el.innerText.trim() : '';
                                };
                                
                                const content = getText('article') || getText('.post-content');
                                const date = document.querySelector('time')?.getAttribute('datetime') || '';
                                const author = getText('.author-name') || 
                                             getText('.writer-name') || 
                                             getText('[data-component="post-author-name"]') ||
                                             'Decentralised Team';
                                
                                return { content, date, author };
                            }
                        """)
                        
                        newsletter_data = {
                            "newsletter_id": idx,
                            "source": "Decentralised.co",
                            "title": article['title'],
                            "publication_date": article_data['date'],
                            "content": article_data['content'],
                            "author": article_data['author'],
                            "url": article['url'],
                            "categories": ["blockchain", "crypto", "web3"],
                            "sentiment": 0.0,
                            "entities": []
                        }
                        
                        newsletters.append(newsletter_data)
                        print(f"Successfully scraped: {article['title']}")
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"Error scraping article: {str(e)}")
                        continue
                
                # Save results
                with open("newsletters.json", "w", encoding="utf-8") as f:
                    json.dump(newsletters, f, indent=2, ensure_ascii=False)
                
                print(f"\nSuccessfully scraped {len(newsletters)} newsletters!")
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                print("\nPage HTML saved to page_content.html")
                
            finally:
                browser.close()

def main():
    scraper = NewsletterScraper()
    scraper.scrape_newsletters()

if __name__ == "__main__":
    main()
