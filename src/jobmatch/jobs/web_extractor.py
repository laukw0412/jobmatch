import ipaddress
from urllib.parse import urlsplit

import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from trafilatura import extract as trafilatura_extract


HEADERS = {
    "User-Agent": "JobMatch/0.1",
    "Accept": "text/html",
}

JOB_MARKERS = [
    "requirements",
    "qualifications",
    "responsibilities",
    "job description",
    "what you'll do",
    "what you will do",
    "about the role",
    "required skills",
    "応募資格",
    "必須要件",
    "歓迎要件",
    "仕事内容",
    "業務内容",
    "岗位职责",
    "任职要求",
]

BLOCK_MARKERS = [
    "too many requests",
    "verify you are human",
    "access denied",
    "enable javascript",
    "captcha",
]


def validate_url(url: str) -> None:
    parsed = urlsplit(url)

    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("A valid HTTPS URL is required.")

    if parsed.username or parsed.password:
        raise ValueError("URL credentials are not allowed.")

    if parsed.port not in (None, 443):
        raise ValueError("Non-standard ports are not supported.")

    hostname = parsed.hostname.lower()

    if hostname == "localhost" or hostname.endswith(".local"):
        raise ValueError("Local URLs are not allowed.")

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        if not ip.is_global:
            raise ValueError("Private IP addresses are not allowed.")


def is_valid_job_text(text: str) -> bool:
    if len(text.strip()) < 400:
        return False

    lowered = text.lower()

    if any(marker in lowered[:1500] for marker in BLOCK_MARKERS):
        return False

    return any(marker in lowered for marker in JOB_MARKERS)


def extract_from_html(html: str) -> str:
    return trafilatura_extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_recall=True,
    ) or ""


def extract_with_requests(url: str) -> str:
    with requests.Session() as session:
        session.trust_env = False

        with session.get(
            url,
            headers=HEADERS,
            timeout=15,
            stream=True,
            allow_redirects=False,
        ) as response:

            if response.status_code == 429:
                raise ValueError("Website rate limit exceeded.")

            if 300 <= response.status_code < 400:
                raise ValueError("HTTP redirect not supported.")

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type", ""
            ).lower()

            if "text/html" not in content_type:
                raise ValueError("Response is not HTML.")

            chunks = []
            total = 0

            for chunk in response.iter_content(65536):
                total += len(chunk)

                if total > 5 * 1024 * 1024:
                    raise ValueError("HTML response is too large.")

                chunks.append(chunk)

            html = b"".join(chunks).decode(
                response.encoding or "utf-8",
                errors="replace",
            )

    return extract_from_html(html)


def extract_with_playwright(url: str) -> str:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            page = browser.new_page()

            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            if response is None:
                raise ValueError("No navigation response.")

            if response.status == 429:
                raise ValueError("Website rate limit exceeded.")

            if response.status >= 400:
                raise ValueError(
                    f"Website returned HTTP {response.status}."
                )

            # Verify the page was not redirected elsewhere.
            original = urlsplit(url)
            final = urlsplit(page.url)

            if (
                final.hostname != original.hostname
                or final.path.rstrip("/") != original.path.rstrip("/")
            ):
                raise ValueError(
                    "Website redirected away from the job page."
                )

            # Wait for meaningful job-related content.
            try:
                page.wait_for_function(
                    """(markers) => {
                        const text = (
                            document.body?.innerText || ""
                        ).toLowerCase();

                        return text.length >= 400 &&
                            markers.some(m => text.includes(m));
                    }""",
                    arg=JOB_MARKERS,
                    timeout=12000,
                )
            except PlaywrightTimeoutError:
                pass

            # Extract from the rendered HTML.
            rendered_html = page.content()
            extracted = extract_from_html(rendered_html)

            if is_valid_job_text(extracted):
                return extracted.strip()

            # Fallback to visible browser text.
            body_text = page.locator("body").inner_text()

            if is_valid_job_text(body_text):
                return body_text.strip()

            raise ValueError(
                "No valid job description found in browser."
            )

        finally:
            browser.close()


def extract_job_text_from_url(url: str) -> str:
    url = url.strip()
    validate_url(url)

    try:
        text = extract_with_requests(url)

        if is_valid_job_text(text):
            return text.strip()

    except (requests.RequestException, ValueError):
        pass

    try:
        return extract_with_playwright(url)

    except Exception as exc:
        raise ValueError(
            "Unable to extract job description. "
            "Please paste the job text manually."
        ) from exc
