import json
import time
from playwright.sync_api import sync_playwright

class BeaconsScraper:
    def __init__(self):
        self.base_url = "https://beacons.ai"
        self.blog_url = f"{self.base_url}/i/blog"

    def scrape_blogs(self):
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=False)
            page = browser.new_page()
            
            try:
                print(f"Accessing: {self.blog_url}")
                page.goto(self.blog_url)
                time.sleep(5)
                
                all_blogs = []
                
                # Wait for blog grid to load
                page.wait_for_selector("div.grid.w-dyn-items", timeout=30000)
                
                # Extract blogs
                blogs = page.evaluate("""
                    () => {
                        const blogs = [];
                        document.querySelectorAll('div.grid_item.w-dyn-item').forEach(blog => {
                            const linkElem = blog.querySelector('a.blog_linkblock');
                            const titleElem = blog.querySelector('.blog_title');
                            const categoryElem = blog.querySelector('.blog_category');
                            const dateElem = blog.querySelector('.blog_date:last-child');
                            const imageStyle = blog.querySelector('.blog_cover_img').style.backgroundImage;
                            const imageUrl = imageStyle.replace('url("', '').replace('")', '');
                            
                            if (linkElem && titleElem) {
                                blogs.push({
                                    title: titleElem.innerText.trim(),
                                    url: linkElem.href,
                                    category: categoryElem ? categoryElem.innerText.trim() : '',
                                    date: dateElem ? dateElem.innerText.trim() : '',
                                    image: imageUrl
                                });
                            }
                        });
                        return blogs;
                    }
                """)
                
                print(f"\nFound {len(blogs)} blogs")
                
                # Now scrape individual blog posts
                for idx, blog in enumerate(blogs, 1):
                    try:
                        print(f"\nScraping blog {idx}/{len(blogs)}")
                        print(f"URL: {blog['url']}")
                        
                        # Visit the blog page
                        page.goto(blog['url'])
                        page.wait_for_selector('div.rich-text-block.w-richtext', timeout=30000)
                        time.sleep(3)
                        
                        # Extract blog content
                        content_data = page.evaluate("""
                            () => {
                                const content = document.querySelector('div.rich-text-block.w-richtext');
                                return content ? content.innerText.trim() : '';
                            }
                        """)
                        
                        blog_data = {
                            "blog_id": idx,
                            "source": "Beacons",
                            "title": blog['title'],
                            "category": blog['category'],
                            "publication_date": blog['date'],
                            "content": content_data,
                            "url": blog['url'],
                            "image": blog['image']
                        }
                        
                        all_blogs.append(blog_data)
                        print(f"Successfully scraped: {blog['title']}")
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"Error scraping blog: {str(e)}")
                        continue
                
                # Save results
                with open("beacons_blogs.json", "w", encoding="utf-8") as f:
                    json.dump(all_blogs, f, indent=2, ensure_ascii=False)
                
                print(f"\nSuccessfully scraped {len(all_blogs)} blogs!")
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
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