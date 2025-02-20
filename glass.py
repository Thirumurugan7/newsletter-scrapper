import json
import time
from playwright.sync_api import sync_playwright

class GlassnodeScraper:
    def __init__(self):
        self.base_url = "https://insights.glassnode.com"
        self.archive_url = f"{self.base_url}/tag/newsletter"

    def scrape_newsletters(self):
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=False)
            page = browser.new_page()
            
            try:
                print(f"Accessing: {self.archive_url}")
                page.goto(self.archive_url)
                time.sleep(5)
                
                print("Loading newsletter content...")
                
                # Wait for content to load
                page.wait_for_selector(".post-card", timeout=30000)
                
                # Scroll to load all content
                print("Loading all articles...")
                for _ in range(10):  # More scrolls since there are many articles
                    page.keyboard.press('End')
                    time.sleep(3)
                    print("Scrolling...")

                # Extract articles
                articles = page.evaluate("""
                    () => {
                        const articles = [];
                        document.querySelectorAll('article.post-card').forEach(post => {
                            const titleElem = post.querySelector('.post-card-title');
                            const linkElem = post.querySelector('.post-card-image-link, .post-card-content-link');
                            const excerptElem = post.querySelector('.post-card-excerpt');
                            const dateElem = post.querySelector('.post-card-meta-date');
                            const readTimeElem = post.querySelector('.post-card-meta-length');
                            const imageElem = post.querySelector('.post-card-image');
                            
                            if (titleElem && linkElem) {
                                articles.push({
                                    title: titleElem.innerText.trim(),
                                    url: new URL(linkElem.href, 'https://insights.glassnode.com').href,
                                    excerpt: excerptElem ? excerptElem.innerText.trim() : '',
                                    date: dateElem ? dateElem.getAttribute('datetime') : '',
                                    read_time: readTimeElem ? readTimeElem.innerText.trim() : '',
                                    image: imageElem ? imageElem.src : null
                                });
                            }
                        });
                        return articles;
                    }
                """)
                
                print(f"\nFound {len(articles)} newsletters")
                
                newsletters = []
                for idx, article in enumerate(articles, 1):
                    try:
                        print(f"\nScraping newsletter {idx}/{len(articles)}")
                        print(f"URL: {article['url']}")
                        
                        # Visit the article page
                        page.goto(article['url'])
                        page.wait_for_selector('article.article', timeout=30000)
                        time.sleep(3)
                        
                        # Extract article content
                        content_data = page.evaluate("""
                            () => {
                                const getText = selector => {
                                    const el = document.querySelector(selector);
                                    return el ? el.innerText.trim() : '';
                                };
                                
                                // Get all images in the article
                                const images = Array.from(document.querySelectorAll('article.article img')).map(img => ({
                                    src: img.src,
                                    alt: img.alt || '',
                                    width: img.width || '',
                                    height: img.height || ''
                                }));
                                
                                // Get content
                                const content = getText('article.article');
                                
                                // Get tags
                                const tags = Array.from(document.querySelectorAll('.article-tag'))
                                    .map(tag => tag.innerText.trim());
                                
                                return { 
                                    content,
                                    images,
                                    tags
                                };
                            }
                        """)
                        
                        newsletter_data = {
                            "newsletter_id": idx,
                            "source": "Glassnode Insights",
                            "title": article['title'],
                            "publication_date": article['date'],
                            "read_time": article['read_time'],
                            "excerpt": article['excerpt'],
                            "content": content_data['content'],
                            "url": article['url'],
                            "featured_image": article['image'],
                            "content_images": content_data['images'],
                            "categories": content_data['tags'] if content_data['tags'] else ["crypto", "bitcoin", "market-analysis"]
                        }
                        
                        newsletters.append(newsletter_data)
                        print(f"Successfully scraped: {article['title']}")
                        print(f"Read time: {article['read_time']}")
                        print(f"Found {len(content_data['images'])} content images")
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"Error scraping article: {str(e)}")
                        continue
                
                # Save results
                with open("glassnode_newsletters.json", "w", encoding="utf-8") as f:
                    json.dump(newsletters, f, indent=2, ensure_ascii=False)
                
                print(f"\nSuccessfully scraped {len(newsletters)} newsletters!")
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                page.screenshot(path="error.png")
                with open("error.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("Saved error.png and error.html for debugging")
                
            finally:
                browser.close()

def main():
    scraper = GlassnodeScraper()
    scraper.scrape_newsletters()

if __name__ == "__main__":
    main()
