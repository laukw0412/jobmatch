"""Compare free job-page extraction methods on public job postings.

Run from the JobMatch project root:
    python tests/test_job_web_extractors.py

Optional:
    python tests/test_job_web_extractors.py --methods trafilatura bs4 playwright crawl4ai
    python tests/test_job_web_extractors.py --url https://example.com/job/123
"""

import argparse
import asyncio
import csv
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup
from trafilatura import extract as trafilatura_extract


TEST_JOBS = [
    {
        "site": "linkedin_gtalent",
        "url": "https://www.linkedin.com/jobs/view/4471593719",
        "keywords": ["Machine Learning Engineer", "Japanese", "Energy"]
    },
    {
        "site": "linkedin_spotted",
        "url": "https://jp.linkedin.com/jobs/view/machine-learning-engineer-at-spotted-4477988180",
        "keywords": ["Machine Learning Engineer", "Python", "RAG"],
    },
    {
        "site": "workday_sony",
        "url": "https://sonyglobal.wd1.myworkdayjobs.com/SonyJapanCareers/job/Tokyo---Osaki/Full-Time---AI-Application-Engineer_JR-116505",
        "keywords": ["Qualifications", "PyTorch", "Responsibilities"],
    },
    {
        "site": "lever_woven",
        "url": "https://jobs.lever.co/woven-by-toyota/d59b0f20-4b3b-49bf-b9a6-600ee7050db0",
        "keywords": ["Computer Vision", "Toyota", "Machine Learning"],
    },
    {
        "site": "greenhouse_paypay",
        "url": "https://job-boards.greenhouse.io/paypay/jobs/4918512004",
        "keywords": ["Machine Learning", "PayPay", "Qualifications"],
    },
    {
        "site": "ashby_openai",
        "url": "https://jobs.ashbyhq.com/openai/6668417f-6878-4244-940f-9a99ae4ebcb0/",
        "keywords": ["Applied AI Engineer", "Tokyo", "Python"],
    },
]

METHODS = ("trafilatura", "bs4", "playwright", "crawl4ai")
HEADERS = {"User-Agent": "JobMatchBenchmark/0.1", "Accept": "text/html"}


def validate_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Only public HTTPS URLs are supported.")
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("Credentials or nonstandard ports are not supported.")
    host = parsed.hostname.lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        raise ValueError("Local addresses are not supported.")
    # This is only a preliminary check, not an SSRF defense for hosted use.


def fetch_html(url: str) -> str:
    validate_url(url)
    with requests.get(
        url, headers=HEADERS, timeout=20, stream=True, allow_redirects=False
    ) as response:
        if 300 <= response.status_code < 400:
            raise ValueError(f"HTTP redirect {response.status_code} (not followed)")
        response.raise_for_status()
        if "text/html" not in response.headers.get("Content-Type", "").lower():
            raise ValueError("Response is not HTML")
        chunks, total = [], 0
        for chunk in response.iter_content(chunk_size=65536):
            total += len(chunk)
            if total > 5 * 1024 * 1024:
                raise ValueError("HTML exceeds 5 MiB")
            chunks.append(chunk)
        return b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")


def from_trafilatura(html: str) -> str:
    return trafilatura_extract(
        html, include_comments=False, include_tables=True, favor_recall=True
    ) or ""


def from_bs4(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for el in soup(["script", "style", "nav", "footer", "noscript", "svg"]):
        el.decompose()
    main = soup.select_one("main") or soup.select_one("article") or soup.body
    return main.get_text("\n", strip=True) if main else ""


async def from_playwright(url: str) -> str:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        try:
            page = await browser.new_page()

            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            if response is None:
                raise ValueError("No navigation response.")

            print(f"HTTP status: {response.status}")

            # Wait until the page contains meaningful text.
            try:
                await page.wait_for_function(
                    """() => {
                        const text = document.body?.innerText || "";
                        return text.trim().length >= 1000;
                    }""",
                    timeout=12000,
                )
            except Exception:
                print("Warning: Timed out waiting for content.")

            before_text = await page.locator("body").inner_text()

            clicked = await expand_job_description(page)

            if clicked:
                await page.wait_for_timeout(1000)

            after_text = await page.locator("body").inner_text()

            print(f"Final URL: {page.url}")
            print(f"Expansion buttons clicked: {clicked}")
            print(f"Before expansion: {len(before_text)} chars")
            print(f"After expansion: {len(after_text)} chars")

            # Extract main content from the rendered HTML.
            rendered_html = await page.content()

            extracted_text = trafilatura_extract(
                rendered_html,
                include_comments=False,
                include_tables=True,
                favor_recall=True,
            ) or ""

            print(f"Body text length: {len(after_text)}")
            print(f"Trafilatura text length: {len(extracted_text)}")

            return extracted_text

        finally:
            await browser.close()


async def from_crawl4ai(url: str) -> str:
    from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
        )
        if not result.success:
            raise ValueError(result.error_message or "Crawler failed")
        markdown = result.markdown
        return str(getattr(markdown, "raw_markdown", markdown) or "")


def assess(text: str, keywords: list[str]) -> dict:
    compact = re.sub(r"\s+", " ", text).strip()
    found = [word for word in keywords if word.casefold() in compact.casefold()]
    blocked = any(
        marker in compact.casefold()[:1500]
        for marker in ("access denied", "enable javascript", "captcha", "verify you are human")
    )
    # Heuristic only; inspect the saved text to confirm complete JD extraction.
    status = "review" if len(compact) >= 400 and len(found) >= 2 and not blocked else "poor"
    return {"status": status, "chars": len(compact), "keyword_hits": len(found), "keywords": ", ".join(found)}


async def expand_job_description(page) -> int:
    # Search for expansion buttons near the job description.
    container_selectors = [
        "main",
        "article",
        "[class*='job-description']",
        "[class*='jobDescription']",
        "[class*='job-details']",
        "[class*='description']",
    ]

    button_pattern = re.compile(
        r"^(show more|read more|see more|"
        r"view more|もっと見る|続きを読む|展开更多|显示更多)$",
        re.IGNORECASE,
    )

    clicked = 0

    for selector in container_selectors:
        containers = page.locator(selector)

        for i in range(min(await containers.count(), 10)):
            container = containers.nth(i)
            buttons = container.get_by_role(
                "button",
                name=button_pattern,
            )

            for j in range(min(await buttons.count(), 5)):
                button = buttons.nth(j)

                try:
                    if await button.is_visible():
                        await button.click(timeout=2000)
                        clicked += 1
                        break
                except Exception:
                    continue

    return clicked


async def run_one(method: str, url: str, html: str | None) -> str:
    if method == "trafilatura":
        return from_trafilatura(html) if html is not None else ""
    if method == "bs4":
        return from_bs4(html) if html is not None else ""
    if method == "playwright":
        return await from_playwright(url)
    if method == "crawl4ai":
        return await from_crawl4ai(url)
    raise ValueError(f"Unknown method: {method}")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--methods", nargs="+", choices=METHODS, default=list(METHODS))
    parser.add_argument("--url", help="Test a single trusted public HTTPS job URL")
    args = parser.parse_args()

    jobs = [{"site": "custom", "url": args.url, "keywords": []}] if args.url else TEST_JOBS
    output_dir = Path("data") / "benchmarks" / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    for job in jobs:
        site, url = job["site"], job["url"]
        print(f"\n=== {site} ===\n{url}", flush=True)
        try:
            validate_url(url)
        except Exception as exc:
            print(f"Invalid URL: {exc}")
            continue

        html, html_error = None, ""
        if any(x in args.methods for x in ("trafilatura", "bs4")):
            try:
                html = await asyncio.to_thread(fetch_html, url)
            except Exception as exc:
                html_error = f"{type(exc).__name__}: {exc}"

        for method in args.methods:
            started = time.perf_counter()
            try:
                if method in ("trafilatura", "bs4") and html is None:
                    raise ValueError(html_error or "No HTML")
                text = await run_one(method, url, html)
                metrics = assess(text, job["keywords"])
                error = ""
            except Exception as exc:
                text = ""
                metrics = assess(text, job["keywords"])
                error = f"{type(exc).__name__}: {exc}"
            seconds = round(time.perf_counter() - started, 2)
            (output_dir / f"{site}_{method}.txt").write_text(text, encoding="utf-8")
            row = {"site": site, "method": method, "seconds": seconds, **metrics, "error": error, "url": url}
            rows.append(row)
            print(
                f"{method:12s} {metrics['status']:6s} chars={metrics['chars']:6d} "
                f"hits={metrics['keyword_hits']}/{len(job['keywords'])} "
                f"time={seconds:5.1f}s {error[:100]}",
                flush=True,
            )

    with (output_dir / "results.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "site", "method", "seconds", "status", "chars", "keyword_hits", "keywords", "error", "url"
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved results to: {output_dir.resolve()}")
    print("'review' means potentially useful, not confirmed full JD. Inspect .txt files.")


if __name__ == "__main__":
    asyncio.run(main())
