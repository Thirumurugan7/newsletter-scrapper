import json
import time
import random
from playwright.sync_api import sync_playwright

class ColosseumScraper:
    def __init__(self):
        self.base_url = "https://blog.colosseum.org"

    def random_sleep(self, min_seconds=2, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def scrape_blogs(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            try:
                print(f"Accessing: {self.base_url}")
                page.goto(self.base_url)
                self.random_sleep(3)
                
                # Wait for content to load
                page.wait_for_selector(".gh-feed", timeout=30000)
                
                # Click "See all" button if it exists
                try:
                    see_all_button = page.get_by_text("See all")
                    if see_all_button:
                        print("Clicking 'See all' button...")
                        see_all_button.click()
                        self.random_sleep(3)
                except Exception as e:
                    print(f"No 'See all' button found: {e}")
                
                # Scroll to load all content
                print("Loading all articles...")
                last_height = 0
                scroll_attempts = 0
                max_attempts = 10
                
                while scroll_attempts < max_attempts:
                    # Scroll down
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    self.random_sleep(2)
                    
                    # Calculate new scroll height
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                    scroll_attempts += 1
                    print(f"Scrolling... (attempt {scroll_attempts}/{max_attempts})")

                # Extract articles with updated selectors
                articles = page.evaluate("""
                    () => {
                        const articles = [];
                        document.querySelectorAll('.gh-feed article').forEach(article => {
                            const link = article.querySelector('a.gh-card-link');
                            const title = article.querySelector('.gh-card-title');
                            const excerpt = article.querySelector('.gh-card-excerpt');
                            const author = article.querySelector('.gh-card-author');
                            const date = article.querySelector('.gh-card-date');
                            const image = article.querySelector('img');
                            
                            if (title && link) {
                                articles.push({
                                    title: title.innerText.trim(),
                                    url: link.href,
                                    excerpt: excerpt ? excerpt.innerText.trim() : '',
                                    author: author ? author.innerText.replace('By ', '').trim() : '',
                                    date: date ? date.getAttribute('datetime') : '',
                                    image: image ? image.src : null
                                });
                            }
                        });
                        return articles;
                    }
                """)
                
                print(f"\nFound {len(articles)} articles")
                
                # Now scrape individual articles with correct selectors
                for idx, article in enumerate(articles, 1):
                    try:
                        print(f"\nScraping article {idx}/{len(articles)}")
                        print(f"URL: {article['url']}")
                        
                        page.goto(article['url'])
                        # Wait for the main article content with updated selector
                        page.wait_for_selector('.article-content, .gh-content', timeout=30000)
                        self.random_sleep(2)
                        
                        # Extract article content with updated selectors
                        content_data = page.evaluate("""
                            () => {
                                const content = document.querySelector('.article-content, .gh-content');
                                const images = Array.from(document.querySelectorAll('.article-content img, .gh-content img')).map(img => ({
                                    src: img.src,
                                    alt: img.alt || ''
                                }));
                                
                                return {
                                    content: content ? content.innerText.trim() : '',
                                    images: images
                                };
                            }
                        """)
                        
                        article['content'] = content_data['content']
                        article['content_images'] = content_data['images']
                        
                        print(f"Successfully scraped: {article['title']}")
                        
                        # Save progress after each article
                        with open("colosseum_articles.json", "w", encoding="utf-8") as f:
                            json.dump(articles, f, indent=2, ensure_ascii=False)
                        
                        self.random_sleep(2)
                        
                    except Exception as e:
                        print(f"Error scraping article: {str(e)}")
                        page.screenshot(path=f"error_{idx}.png")
                        continue
                
                print(f"\nSuccessfully scraped {len(articles)} articles!")
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                page.screenshot(path="error.png")
                with open("error.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("Saved error.png and error.html for debugging")
                
            finally:
                browser.close()

def main():
    scraper = ColosseumScraper()
    scraper.scrape_blogs()

if __name__ == "__main__":
    main()
