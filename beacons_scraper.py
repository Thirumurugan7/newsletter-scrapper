import json
import time
import random
from playwright.sync_api import sync_playwright

class BeaconsScraper:
    def __init__(self):
        self.base_url = "https://beacons.ai"
        self.blog_url = f"{self.base_url}/i/beacons-blog"
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        # Add proxy servers - replace with your proxy details
        self.proxies = [
            {
                'server': 'http://proxy1.example.com:8080',
                'username': 'user1',
                'password': 'pass1'
            },
            {
                'server': 'http://proxy2.example.com:8080',
                'username': 'user2',
                'password': 'pass2'
            }
        ]

    def random_sleep(self, min_seconds=2, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def scrape_blogs(self):
        with sync_playwright() as p:
            # Select random proxy
            proxy = random.choice(self.proxies)
            
            browser = p.chromium.launch(
                headless=False,
                proxy={
                    'server': proxy['server'],
                    'username': proxy['username'],
                    'password': proxy['password']
                },
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                ]
            )
            
            context = browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True,
                bypass_csp=True,
                permissions=['geolocation'],
                locale='en-US',
                timezone_id='America/New_York',
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                color_scheme='light',
            )
            
            # Add more stealth scripts
            context.add_init_script("""
                // Override property getters for stealth
                const overrideProperties = {
                    hardwareConcurrency: 8,
                    deviceMemory: 8,
                    webdriver: false,
                    plugins: [1, 2, 3, 4, 5],
                    languages: ['en-US', 'en'],
                    platform: 'MacIntel',
                    doNotTrack: null,
                };

                for (const [key, value] of Object.entries(overrideProperties)) {
                    Object.defineProperty(navigator, key, {
                        get: () => value
                    });
                }

                // Add Chrome-specific properties
                window.chrome = {
                    app: {
                        isInstalled: false,
                    },
                    runtime: {
                        PlatformOs: {
                            MAC: 'mac',
                            WIN: 'win',
                        },
                    },
                    loadTimes: function() {},
                    csi: function() {},
                };

                // Override toString for stealth
                const originalFunction = Function.prototype.toString;
                Function.prototype.toString = function() {
                    if (this === Function.prototype.toString) return originalFunction.call(this);
                    if (this === navigator.hardwareConcurrency) return '8';
                    return originalFunction.call(this);
                };
            """)
            
            page = context.new_page()
            
            # Add more realistic headers
            page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'DNT': '1',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"'
            })
            
            try:
                print(f"Accessing: {self.blog_url}")
                
                # Add random initial page visit
                start_urls = [
                    'https://beacons.ai',
                    'https://beacons.ai/i',
                    'https://beacons.ai/about'
                ]
                page.goto(random.choice(start_urls), wait_until='networkidle')
                self.random_sleep(3, 5)
                
                # Now go to blog page
                page.goto(self.blog_url, wait_until='networkidle')
                self.random_sleep(4, 7)
                
                all_blogs = []
                
                # Wait for blog grid to load
                page.wait_for_selector("div.grid.w-dyn-items", timeout=30000)
                self.random_sleep()
                
                # Scroll slowly and naturally
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, Math.floor(Math.random() * 400) + 200)")
                    self.random_sleep(1, 3)
                
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
                        
                        # Visit the blog page with random delays
                        page.goto(blog['url'], wait_until='networkidle')
                        self.random_sleep(3, 6)
                        
                        page.wait_for_selector('div.rich-text-block.w-richtext', timeout=30000)
                        self.random_sleep()
                        
                        # Scroll naturally through the content
                        page.evaluate("""
                            () => {
                                const scrollHeight = document.documentElement.scrollHeight;
                                const viewHeight = window.innerHeight;
                                let scrollTop = 0;
                                const scroll = () => {
                                    if (scrollTop < scrollHeight) {
                                        scrollTop += Math.floor(Math.random() * 200) + 100;
                                        window.scrollTo(0, scrollTop);
                                        setTimeout(scroll, Math.random() * 1000 + 500);
                                    }
                                };
                                scroll();
                            }
                        """)
                        self.random_sleep(2, 4)
                        
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
                        self.random_sleep(2, 4)
                        
                    except Exception as e:
                        print(f"Error scraping blog: {str(e)}")
                        self.random_sleep(5, 8)  # Longer delay on error
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