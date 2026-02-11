import unittest
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ENTRIES_FILE = Path("entries.json")

def check_url(url):
    """Return True if URL is reachable using stealth Playwright, False otherwise."""
    try:
        with sync_playwright() as p:
            # Use a real Chrome profile and more stealthy options
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials'
                ]
            )
            
            # Create context with realistic viewport and user agent
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            # Remove webdriver property
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            response = page.goto(url, timeout=15000, wait_until='domcontentloaded')
            page.wait_for_timeout(10000)
            browser.close()
            
            return response.status < 400
            
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return False

def get_all_urls_from_entries():
    """Extract all URLs from entries.json with their context."""
    if not ENTRIES_FILE.exists():
        raise FileNotFoundError(f"Missing {ENTRIES_FILE}")
    
    data = json.loads(ENTRIES_FILE.read_text(encoding="utf-8"))
    
    urls_with_context = []
    for i, entry in enumerate(data):
        for j, link in enumerate(entry.get("links", [])):
            if "url" in link:
                urls_with_context.append({
                    "url": link["url"],
                    "context": f"Entry #{i}, Link #{j}: {entry.get('title', 'Untitled')}"
                })
    return urls_with_context

class TestGenerateReadme(unittest.TestCase):

    def test_all_links_are_reachable(self):
        urls = get_all_urls_from_entries()
        self.assertGreater(len(urls), 0, "No URLs found in entries.json")

        broken_links = []
        for item in urls:
            is_ok = check_url(item["url"])
            if not is_ok:
                broken_links.append(f"{item['context']}: {item['url']}")

        if broken_links:
            self.fail(f"Found {len(broken_links)} broken link(s):\n" + "\n".join(broken_links))

if __name__ == '__main__':
    unittest.main()
