import json
import time
from playwright.sync_api import sync_playwright

class MultiSiteScraper:
    def __init__(self):
        # Define all sites to scrape
        self.sites = [
            {
                "name": "Decentralised",
                "base_url": "https://www.decentralised.co",
                "archive_url": "https://www.decentralised.co/archive",
                "selectors": {
                    "article": "h3",
                    "link": "a[href*='/p/']",
                    "content": "article, .post-content",
                    "date": "time",
                    "author": ".author-name, .writer-name",
                    "categories": ["blockchain", "crypto", "web3"]
                }
            },
        
            {
                "name": "Milkroad",
                "base_url": "https://milkroad.com",
                "archive_url": "https://milkroad.com/daily",
                "selectors": {
                    "article": "h3",
                    "link": "a[href*='/p/']",
                    "content": "article, .post-content",
                    "date": "time",
                    "author": ".author-name, .writer-name",
                    "categories": ["crypto", "web3", "newsletter"]
                }
            },
            {
                "name": "Beacons",
                "base_url": "https://beacons.ai",
                "archive_url": "https://beacons.ai/i/beacons-blog",
                "selectors": {
                    "article": ".blog-post-card",
                    "link": "a",
                    "content": ".blog-post-content",
                    "date": ".blog-post-date",
                    "author": ".blog-post-author",
                    "categories": ["beacons", "creator-economy"]
                }
            }
        ]

    def scrape_site(self, site, page):
        try:
            print(f"\nScraping {site['name']}...")
            print(f"Accessing: {site['archive_url']}")
            page.goto(site['archive_url'])
            time.sleep(5)

            # Handle popup if it's Milkroad
            if site['name'] == "Milkroad":
                try:
                    close_button_selectors = [
                        'button[aria-label="Close"]',
                        '.modal-close',
                        '.close-button',
                        'button.close'
                    ]
                    for selector in close_button_selectors:
                        if page.locator(selector).is_visible(timeout=5000):
                            page.click(selector)
                            time.sleep(2)
                            break
                except Exception as e:
                    print(f"No popup found or error handling popup: {str(e)}")

            # Wait for content to load
            page.wait_for_selector(site['selectors']['article'], timeout=30000)
            
            # Scroll to load all content
            print("Loading all articles...")
            for _ in range(5):
                page.keyboard.press('End')
                time.sleep(3)
                print("Scrolling...")

            # Extract articles
            articles = page.evaluate("""
                () => {
                    const articles = [];
                    const articleElements = document.querySelectorAll('h3');
                    
                    articleElements.forEach(article => {
                        const link = article.querySelector('a');
                        if (link && link.href && link.href.includes('/p/')) {
                            articles.push({
                                title: link.innerText.trim() || article.innerText.trim(),
                                url: link.href
                            });
                        }
                    });
                    
                    // If no articles found with h3, try alternative selectors
                    if (articles.length === 0) {
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
                    }
                    
                    // Remove duplicates
                    return Array.from(new Set(articles.map(a => a.url)))
                        .map(url => articles.find(a => a.url === url));
                }
            """)

            print(f"\nFound {len(articles)} articles on {site['name']}")

            newsletters = []
            for idx, article in enumerate(articles, 1):
                try:
                    print(f"\nScraping article {idx}/{len(articles)}")
                    print(f"URL: {article['url']}")
                    
                    page.goto(article['url'])
                    page.wait_for_selector(site['selectors']['content'], timeout=30000)
                    time.sleep(3)
                    
                    # Extract article data
                    article_data = page.evaluate(f"""
                        () => {{
                            const getText = selector => {{
                                const el = document.querySelector(selector);
                                return el ? el.innerText.trim() : '';
                            }};
                            
                            const images = Array.from(document.querySelectorAll('article img, .post-content img')).map(img => ({{
                                src: img.src,
                                alt: img.alt || '',
                                width: img.width || '',
                                height: img.height || ''
                            }}));
                            
                            const featuredImage = document.querySelector('.post-feature-image img, article header img');
                            const headerImage = featuredImage ? {{
                                src: featuredImage.src,
                                alt: featuredImage.alt || '',
                                width: featuredImage.width || '',
                                height: featuredImage.height || ''
                            }} : null;
                            
                            return {{ 
                                content: getText('{site["selectors"]["content"]}'),
                                date: document.querySelector('{site["selectors"]["date"]}')?.getAttribute('datetime') || '',
                                author: getText('{site["selectors"]["author"]}') || '{site["name"]} Team',
                                images,
                                headerImage
                            }};
                        }}
                    """)
                    
                    newsletter_data = {
                        "newsletter_id": idx,
                        "source": site['name'],
                        "title": article['title'],
                        "publication_date": article_data['date'],
                        "content": article_data['content'],
                        "author": article_data['author'],
                        "url": article['url'],
                        "categories": site['selectors']['categories'],
                        "sentiment": 0.0,
                        "entities": [],
                        "featured_image": article_data['headerImage'],
                        "content_images": article_data['images']
                    }
                    
                    newsletters.append(newsletter_data)
                    print(f"Successfully scraped: {article['title']}")
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Error scraping article: {str(e)}")
                    continue

            # Save results for this site
            filename = f"{site['name'].lower()}_newsletters.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(newsletters, f, indent=2, ensure_ascii=False)
            
            print(f"\nSuccessfully scraped {len(newsletters)} newsletters from {site['name']}!")
            return newsletters

        except Exception as e:
            print(f"Error scraping {site['name']}: {str(e)}")
            return []

    def scrape_all_sites(self):
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=False)
            page = browser.new_page()
            
            all_results = {}
            
            try:
                for site in self.sites:
                    results = self.scrape_site(site, page)
                    all_results[site['name']] = results
                    print(f"Completed scraping {site['name']}")
                    time.sleep(5)  # Wait between sites
                
                # Save combined results
                with open("all_newsletters.json", "w", encoding="utf-8") as f:
                    json.dump(all_results, f, indent=2, ensure_ascii=False)
                
                print("\nCompleted scraping all sites!")
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                
            finally:
                browser.close()

def main():
    scraper = MultiSiteScraper()
    scraper.scrape_all_sites()

if __name__ == "__main__":
    main()
