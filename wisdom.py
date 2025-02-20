import json
import time
from playwright.sync_api import sync_playwright

class WizdomScraper:
    def __init__(self):
        self.base_url = "https://www.weeklywizdom.com"
        self.archive_url = f"{self.base_url}/archive?tags=Newsletter"

    def scrape_newsletters(self):
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=False)
            page = browser.new_page()
            
            try:
                print(f"Accessing: {self.archive_url}")
                page.goto(self.archive_url)
                time.sleep(5)
                
                all_articles = []
                page_num = 1
                
                while True:
                    print(f"\nScraping page {page_num}...")
                    print("Loading newsletter content...")
                    
                    try:
                        # Wait for content to load
                        page.wait_for_selector("div.grid.grid-cols-1.gap-6", timeout=30000)
                        
                        # Scroll to load all content on current page
                        print("Loading all articles...")
                        for _ in range(3):  # Reduced scrolls per page
                            page.keyboard.press('End')
                            time.sleep(2)
                            print("Scrolling...")

                        # Extract articles from current page
                        articles = page.evaluate("""
                            () => {
                                const articles = [];
                                document.querySelectorAll('div.transparent.h-full.cursor-pointer.overflow-hidden.rounded-lg.flex.flex-col.border').forEach(post => {
                                    const titleElem = post.querySelector('h2');
                                    const linkElem = post.querySelector('a[href*="/p/"]');
                                    const excerptElem = post.querySelector('p.line-clamp-2');
                                    const dateElem = post.querySelector('time');
                                    const imageElem = post.querySelector('img');
                                    
                                    if (titleElem && linkElem) {
                                        articles.push({
                                            title: titleElem.innerText.trim(),
                                            url: linkElem.href,
                                            excerpt: excerptElem ? excerptElem.innerText.trim() : '',
                                            date: dateElem ? dateElem.getAttribute('datetime') : '',
                                            image: imageElem ? imageElem.src : null
                                        });
                                    }
                                });
                                return articles;
                            }
                        """)
                        
                        if not articles:  # If no articles found, we've reached the end
                            print("No articles found on this page - reached the end")
                            break
                            
                        all_articles.extend(articles)
                        print(f"Found {len(articles)} newsletters on page {page_num}")
                        
                        # Check for next page button
                        next_page_exists = page.evaluate("""
                            () => {
                                const nextButton = Array.from(document.querySelectorAll('a')).find(a => 
                                    a.textContent.includes('Next') || 
                                    a.textContent.includes('→') ||
                                    a.getAttribute('aria-label')?.includes('next')
                                );
                                return nextButton && !nextButton.disabled;
                            }
                        """)
                        
                        if not next_page_exists:
                            print("No more pages to scrape")
                            break
                            
                        # Click next page
                        page.evaluate("""
                            () => {
                                const nextButton = Array.from(document.querySelectorAll('a')).find(a => 
                                    a.textContent.includes('Next') || 
                                    a.textContent.includes('→') ||
                                    a.getAttribute('aria-label')?.includes('next')
                                );
                                nextButton.click();
                            }
                        """)
                        
                        time.sleep(5)  # Wait for next page to load
                        page_num += 1
                        
                    except Exception as e:
                        print(f"Error on page {page_num}, assuming end of pagination")
                        break

                print(f"\nTotal newsletters found across all pages: {len(all_articles)}")
                
                # Now scrape individual articles
                newsletters = []
                for idx, article in enumerate(all_articles, 1):
                    try:
                        print(f"\nScraping newsletter {idx}/{len(all_articles)}")
                        print(f"URL: {article['url']}")
                        
                        # Visit the article page
                        page.goto(article['url'])
                        page.wait_for_selector('div.flex.min-h-screen.flex-col', timeout=30000)
                        time.sleep(3)
                        
                        # Extract article content
                        content_data = page.evaluate("""
                            () => {
                                const contentDivs = document.querySelectorAll('div.flex.min-h-screen.flex-col div');
                                let content = '';
                                
                                contentDivs.forEach(div => {
                                    const text = div.innerText.trim();
                                    if (text && !div.querySelector('nav')) {
                                        content += text + '\\n\\n';
                                    }
                                });
                                
                                return content.trim();
                            }
                        """)
                        
                        newsletter_data = {
                            "newsletter_id": idx,
                            "source": "Weekly Wizdom",
                            "title": article['title'],
                            "publication_date": article['date'],
                            "excerpt": article['excerpt'],
                            "content": content_data,
                            "url": article['url'],
                            "image": article['image']
                        }
                        
                        newsletters.append(newsletter_data)
                        print(f"Successfully scraped: {article['title']}")
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"Error scraping article: {str(e)}")
                        continue
                
                # Save results
                with open("weekly_wizdom_newsletters.json", "w", encoding="utf-8") as f:
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
    scraper = WizdomScraper()
    scraper.scrape_newsletters()

if __name__ == "__main__":
    main()
