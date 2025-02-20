import json
import time
from playwright.sync_api import sync_playwright

class UnchainedScraper:
    def __init__(self):
        self.base_url = "https://unchainedcrypto.substack.com"
        self.archive_url = f"{self.base_url}/archive"

    def random_sleep(self, min_seconds=2, max_seconds=5):
        time.sleep(min_seconds)

    def scrape_blogs(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            try:
                print(f"Accessing: {self.archive_url}")
                page.goto(self.archive_url)
                self.random_sleep(3)
                
                all_posts = []
                
                # Wait for posts to load
                page.wait_for_selector("div.post-preview", timeout=30000)
                
                # Scroll to load all content
                print("Loading all posts...")
                last_height = 0
                while True:
                    # Scroll down
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    self.random_sleep(2)
                    
                    # Calculate new scroll height
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                    print("Scrolling...")

                # Extract posts
                posts = page.evaluate("""
                    () => {
                        const posts = [];
                        document.querySelectorAll('div.post-preview').forEach(post => {
                            const titleElem = post.querySelector('h3.post-preview-title');
                            const linkElem = post.querySelector('a.post-preview-title');
                            const dateElem = post.querySelector('div.post-preview-date');
                            const authorElem = post.querySelector('span.post-preview-byline');
                            const descriptionElem = post.querySelector('div.post-preview-description');
                            
                            // Only add if it's a main article URL (not a comments URL)
                            if (titleElem && linkElem && !linkElem.href.endsWith('/comments')) {
                                posts.push({
                                    title: titleElem.innerText.trim(),
                                    url: linkElem.href,
                                    date: dateElem ? dateElem.innerText.trim() : '',
                                    author: authorElem ? authorElem.innerText.trim() : '',
                                    description: descriptionElem ? descriptionElem.innerText.trim() : ''
                                });
                            }
                        });
                        return posts;
                    }
                """)
                
                print(f"\nFound {len(posts)} posts")
                
                # Now scrape individual posts
                for idx, post in enumerate(posts, 1):
                    try:
                        print(f"\nScraping post {idx}/{len(posts)}")
                        print(f"URL: {post['url']}")
                        
                        # Visit the post page
                        page.goto(post['url'])
                        page.wait_for_selector('div.available-content', timeout=30000)
                        self.random_sleep(2)
                        
                        # Extract post content
                        content_data = page.evaluate("""
                            () => {
                                const content = document.querySelector('div.available-content');
                                return content ? content.innerText.trim() : '';
                            }
                        """)
                        
                        post_data = {
                            "post_id": idx,
                            "source": "Unchained",
                            "title": post['title'],
                            "author": post['author'],
                            "publication_date": post['date'],
                            "description": post['description'],
                            "content": content_data,
                            "url": post['url']
                        }
                        
                        all_posts.append(post_data)
                        print(f"Successfully scraped: {post['title']}")
                        self.random_sleep(2)
                        
                    except Exception as e:
                        print(f"Error scraping post: {str(e)}")
                        continue
                
                # Save results
                with open("unchained_posts.json", "w", encoding="utf-8") as f:
                    json.dump(all_posts, f, indent=2, ensure_ascii=False)
                
                print(f"\nSuccessfully scraped {len(all_posts)} posts!")
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                page.screenshot(path="error.png")
                with open("error.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("Saved error.png and error.html for debugging")
                
            finally:
                browser.close()

def main():
    scraper = UnchainedScraper()
    scraper.scrape_blogs()

if __name__ == "__main__":
    main()
