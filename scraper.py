from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import csv

BASE_URL = "https://www.decentralised.co/archive"
CSV_FILE = "newsletters.csv"

def get_newsletter_links():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)
        # Wait for content to load (adjust time if needed)
        page.wait_for_timeout(3000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for article in soup.select('div.flex.flex-col.gap-2 a[href*="/archive/"]'):
        href = article.get('href')
        full_url = urljoin(BASE_URL, href)
        links.append(full_url)
    return list(set(links))

def extract_newsletter_content(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(2000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, 'html.parser')
    
    title = soup.select_one('h1.text-4xl').get_text(strip=True)
    # Extract date from metadata (example: "Dec 23, 2024")
    date = soup.select_one('time').get_text(strip=True) if soup.select_one('time') else 'No Date'
    content = '\n'.join([p.get_text(strip=True) for p in soup.select('div.prose p')])
    
    return {'title': title, 'date': date, 'content': content, 'url': url}