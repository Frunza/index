import unittest
import json
from pathlib import Path
from typing import Optional, Tuple

from playwright.sync_api import sync_playwright

ENTRIES_FILE = Path("entries.json")


def check_url(url: str) -> Tuple[str, Optional[int], Optional[str]]:
    """
    Check a URL and classify the result.

    Returns: (verdict, status_code, info)
      verdict:
        - "ok"       : reachable (HTTP < 400)
        - "missing"  : truly broken (HTTP 404 or 410)
        - "blocked"  : exists but access denied / rate limited (HTTP 403 or 429)
        - "timeout"  : navigation timed out
        - "error"    : other errors (DNS, network, etc.)
        - "bad"      : other HTTP >= 400 (treated as broken)
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-site-isolation-trials",
                ],
            )

            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )

            page = context.new_page()

            page.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                """
            )

            response = page.goto(url, timeout=15000, wait_until="domcontentloaded")

            # Optional small wait so sites that do redirects / late navigation settle a bit
            page.wait_for_timeout(1000)

            status = response.status if response is not None else None
            browser.close()

            if status is None:
                return ("error", None, "No response returned")

            if status < 400:
                return ("ok", status, None)

            if status in (404, 410):
                return ("missing", status, None)

            if status in (403, 429):
                return ("blocked", status, None)

            # Any other HTTP error code
            return ("bad", status, None)

    except Exception as e:
        msg = str(e)
        # Playwright timeouts typically include "Timeout" in the message
        if "Timeout" in msg or "timed out" in msg.lower():
            return ("timeout", None, msg)
        return ("error", None, msg)


def get_all_urls_from_entries():
    """Extract all URLs from entries.json with their context."""
    if not ENTRIES_FILE.exists():
        raise FileNotFoundError(f"Missing {ENTRIES_FILE}")

    data = json.loads(ENTRIES_FILE.read_text(encoding="utf-8"))

    urls_with_context = []
    for i, entry in enumerate(data):
        for j, link in enumerate(entry.get("links", [])):
            if "url" in link:
                urls_with_context.append(
                    {
                        "url": link["url"],
                        "context": f"Entry #{i}, Link #{j}: {entry.get('title', 'Untitled')}",
                    }
                )
    return urls_with_context


class TestGenerateReadme(unittest.TestCase):
    def test_all_links_are_reachable(self):
        urls = get_all_urls_from_entries()
        self.assertGreater(len(urls), 0, "No URLs found in entries.json")

        broken_links = []
        warnings = []

        for item in urls:
            verdict, status, info = check_url(item["url"])

            if verdict == "missing":
                broken_links.append(f"{item['context']}: {item['url']} (HTTP {status})")
            elif verdict in ("blocked", "timeout"):
                # Warn, but do not fail
                detail = f"HTTP {status}" if status is not None else (info or verdict)
                warnings.append(f"{item['context']}: {item['url']} ({detail})")
            elif verdict in ("bad", "error"):
                # Keep this as a failure by default (non-404/410 errors are still meaningful)
                detail = f"HTTP {status}" if status is not None else (info or verdict)
                broken_links.append(f"{item['context']}: {item['url']} ({detail})")

        if warnings:
            print(f"\nWARN: {len(warnings)} link(s) could not be verified due to blocking/rate-limit/timeouts:\n"
                + "\n".join(warnings) + "\n")

        if broken_links:
            self.fail(f"Found {len(broken_links)} broken link(s) (404/410 or other hard errors):\n" + "\n".join(broken_links))


if __name__ == "__main__":
    unittest.main()
