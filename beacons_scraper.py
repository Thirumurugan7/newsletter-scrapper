import json
import time
from playwright.sync_api import sync_playwright

class BeaconsScraper:
    def __init__(self):
        self.base_url = "https://beacons.ai/i/beacons-blog"

    def scrape_blogs(self):
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=False)
            page = browser.new_page()
            
            try:
                print(f"Accessing: {self.base_url}")
                page.goto(self.base_url)
                time.sleep(5)  # Initial wait
                
                print("Loading blog content...")
                
                # Wait for blog posts to load (updated selector)
                page.wait_for_selector(".grid-item", timeout=30000)
                
                # Scroll to load all content
                print("Loading all articles...")
                for _ in range(5):
                    page.keyboard.press('End')
                    time.sleep(3)
                    print("Scrolling...")

                # Extract blog posts with updated selectors
                blog_data = page.evaluate("""
                    () => {
                        const articles = [];
                        document.querySelectorAll('.grid-item').forEach(card => {
                            const titleElem = card.querySelector('.text-lg');
                            const linkElem = card.querySelector('a');
                            const imgElem = card.querySelector('img');
                            const dateElem = card.querySelector('.text-sm');
                            
                            if (linkElem && titleElem) {
                                articles.push({
                                    title: titleElem.innerText.trim(),
                                    url: linkElem.href,
                                    thumbnail: imgElem ? imgElem.src : null,
                                    date: dateElem ? dateElem.innerText.trim() : null
                                });
                            }
                        });
                        return articles;
                    }
                """)
                
                print(f"\nFound {len(blog_data)} blog posts")
                
                blogs = []
                for idx, blog in enumerate(blog_data, 1):
                    try:
                        print(f"\nScraping blog {idx}/{len(blog_data)}")
                        print(f"URL: {blog['url']}")
                        
                        # Visit the blog page
                        page.goto(blog['url'])
                        page.wait_for_selector('.prose', timeout=30000)
                        time.sleep(3)
                        
                        # Extract blog content with updated selectors
                        content_data = page.evaluate("""
                            () => {
                                const getText = selector => {
                                    const el = document.querySelector(selector);
                                    return el ? el.innerText.trim() : '';
                                };
                                
                                // Get all images in the blog post
                                const images = Array.from(document.querySelectorAll('.prose img')).map(img => ({
                                    src: img.src,
                                    alt: img.alt || '',
                                    width: img.width || '',
                                    height: img.height || ''
                                }));
                                
                                // Get main content
                                const content = getText('.prose');
                                
                                // Get author
                                const author = getText('.author') || 'Beacons Team';
                                
                                return {
                                    content,
                                    author,
                                    images
                                };
                            }
                        """)
                        
                        blog_entry = {
                            "blog_id": idx,
                            "source": "Beacons Blog",
                            "title": blog['title'],
                            "publication_date": blog['date'],
                            "content": content_data['content'],
                            "author": content_data['author'],
                            "url": blog['url'],
                            "thumbnail": blog['thumbnail'],
                            "images": content_data['images'],
                            "categories": ["beacons", "creator-economy"]
                        }
                        
                        blogs.append(blog_entry)
                        print(f"Successfully scraped: {blog['title']}")
                        print(f"Found {len(content_data['images'])} images")
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"Error scraping blog: {str(e)}")
                        continue
                
                # Save results
                with open("beacons_blogs.json", "w", encoding="utf-8") as f:
                    json.dump(blogs, f, indent=2, ensure_ascii=False)
                
                print(f"\nSuccessfully scraped {len(blogs)} blog posts!")
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                # Take screenshot and save HTML for debugging
                page.screenshot(path="error.png")
                with open("error.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("Saved error.png and error.html for debugging")
                
            finally:
                browser.close()

def main():
    scraper = BeaconsScraper()
    scraper.scrape_blogs()

if __name__ == "__main__":
    main() 