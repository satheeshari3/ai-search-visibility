import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from urllib.robotparser import RobotFileParser
import time

import ipaddress
import socket

from urllib.parse import urljoin, urlparse


id="7l0z9p"

MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2 MB
MAX_REDIRECTS = 5


def fetch_page(url: str):
    current_url = validate_url(url)

    with httpx.Client(
        timeout=httpx.Timeout(10.0),
        follow_redirects=False,
    ) as client:

        for redirect_count in range(MAX_REDIRECTS + 1):
            # Validate every destination before requesting it.
            validate_url(current_url)

            with client.stream("GET", current_url) as response:

                # Handle redirects ourselves instead of following blindly.
                if response.status_code in {301, 302, 303, 307, 308}:
                    if redirect_count >= MAX_REDIRECTS:
                        raise ValueError("Too many redirects")

                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("Redirect has no destination")

                    current_url = validate_url(
                        urljoin(current_url, location)
                    )
                    continue

                response.raise_for_status()

                content_type = response.headers.get(
                    "content-type", ""
                )

                if "text/html" not in content_type.lower():
                    raise ValueError(
                        f"Not an HTML page: {content_type}"
                    )

                # Reject oversized responses when the size is declared.
                content_length = response.headers.get("content-length")

                if content_length:
                    try:
                        if int(content_length) > MAX_RESPONSE_BYTES:
                            raise ValueError("Page is too large")
                    except ValueError as error:
                        if str(error) == "Page is too large":
                            raise
                        raise ValueError(
                            "Invalid Content-Length header"
                        ) from error

                # Also enforce the limit while downloading.
                body = bytearray()

                for chunk in response.iter_bytes():
                    body.extend(chunk)

                    if len(body) > MAX_RESPONSE_BYTES:
                        raise ValueError("Page is too large")

                print("STATUS:", response.status_code)
                print("URL:", current_url)

                return BeautifulSoup(
                    bytes(body), "html.parser"
                )

    raise ValueError("Could not fetch the page")

def validate_url(url: str):
    parsed = urlparse(url)

    # Allow only HTTP and HTTPS.
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs are allowed")

    # Require a valid hostname.
    hostname = parsed.hostname

    if not hostname:
        raise ValueError("URL must contain a hostname")

    # Reject embedded credentials, such as user:pass@host.
    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed")

    # Resolve the hostname and reject non-public IP addresses.
    try:
        addresses = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as error:
        raise ValueError("Could not resolve hostname") from error

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if not ip.is_global:
            raise ValueError(
                "URLs resolving to non-public IP addresses are not allowed"
            )

    return url

def extract_page_data(soup: BeautifulSoup):
    # Extract title
    title = soup.title.get_text(strip=True) if soup.title else None

    # Extract meta description
    description_tag = soup.find(
        "meta",
        attrs={"name": "description"}
    )

    description = (
        description_tag.get("content", "").strip()
        if description_tag
        else None
    )

    # Extract headings before removing unwanted elements
    headings = [
        heading.get_text(" ", strip=True)
        for heading in soup.find_all(["h1", "h2", "h3"])
    ]

    # Work on a copy so we don't modify the original soup
    content_soup = BeautifulSoup(str(soup), "html.parser")

    # Remove elements that usually contain UI or non-content text
    unwanted_tags = [
        "script",
        "style",
        "noscript",
        "nav",
        "header",
        "footer",
        "aside",
        "form",
        "button",
        "svg",
    ]

    for tag in content_soup.find_all(unwanted_tags):
        tag.decompose()

    # Remove common non-content areas identified by HTML attributes
    unwanted_selectors = [
        "[role='navigation']",
        "[role='banner']",
        "[role='contentinfo']",
        "[aria-label*='cookie' i]",
        "[id*='cookie' i]",
        "[class*='cookie' i]",
        "[id*='sidebar' i]",
        "[class*='sidebar' i]",
        "[id*='theme' i]",
        "[class*='theme' i]",
    ]

    for selector in unwanted_selectors:
        for element in content_soup.select(selector):
            element.decompose()

    # Prefer the main content container when the website provides one
    main_content = (
        content_soup.find("main")
        or content_soup.find("article")
        or content_soup.find(id="content")
        or content_soup.body
        or content_soup
    )

    text = main_content.get_text(" ", strip=True)

    # Keep links from the original soup for crawling
    links = [
        link.get("href")
        for link in soup.find_all("a", href=True)
    ]

    return {
        "title": title,
        "description": description,
        "headings": headings,
        "text": text,
        "links": links,
    }

def normalize_url(base_url: str, link: str):
    return urljoin(base_url, link)

def canonicalize_url(url: str):
    parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")

    if not path:
        path = "/"

    return f"{scheme}://{netloc}{path}"

def is_same_domain(base_url: str, url: str):
    base = urlparse(base_url)
    candidate = urlparse(url)

    return (
        candidate.hostname is not None
        and base.hostname is not None
        and candidate.hostname.lower() == base.hostname.lower()
        and candidate.scheme in {"http", "https"}
    )

def get_robots_parser(start_url: str):
    parsed = urlparse(start_url)
    robots_url = (
        f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    )

    parser = RobotFileParser()
    parser.set_url(robots_url)

    try:
        with httpx.Client(
            timeout=httpx.Timeout(5.0),
            follow_redirects=False,
        ) as client:
            with client.stream("GET", robots_url) as response:
                if response.status_code == 404:
                    # No robots.txt file published.
                    parser.parse([])
                    return parser

                response.raise_for_status()

                content_type = response.headers.get(
                    "content-type", ""
                )

                if (
                    "text/plain" not in content_type.lower()
                    and "text/" not in content_type.lower()
                ):
                    raise ValueError(
                        "Unexpected robots.txt content type"
                    )

                body = bytearray()

                for chunk in response.iter_bytes():
                    body.extend(chunk)

                    if len(body) > 512 * 1024:
                        raise ValueError(
                            "robots.txt is too large"
                        )

                parser.parse(
                    bytes(body).decode(
                        "utf-8", errors="replace"
                    ).splitlines()
                )

    except (httpx.HTTPError, ValueError) as error:
        # Fail closed: don't crawl if we cannot verify the rules.
        raise ValueError(
            f"Could not safely read robots.txt: {error}"
        ) from error

    return parser

###########################################################################################

def crawl(start_url: str, max_pages: int = 5):
    validate_url(start_url)

    if not 1 <= max_pages <= 50:
        raise ValueError("max_pages must be between 1 and 50")

    start_url = canonicalize_url(start_url)

    visited = set()
    queued = {start_url}
    queue = [start_url]

    robots_parser = get_robots_parser(start_url)

    while queue and len(visited) < max_pages:
        current_url = queue.pop(0)
        queued.discard(current_url)

        if current_url in visited:
            continue

        if not robots_parser.can_fetch("*", current_url):
            print(f"Blocked by robots.txt: {current_url}")
            visited.add(current_url)
            continue

        time.sleep(1)

        try:
            soup = fetch_page(current_url)
        except (httpx.HTTPError, ValueError) as error:
            print(f"Failed at crawl {current_url}: {error}")
            visited.add(current_url)
            continue

        visited.add(current_url)

        data = extract_page_data(soup)
        yield {"url": current_url, **data}

        for link in data["links"]:
            full_url = normalize_url(current_url, link)
            parsed = urlparse(full_url)

            # Ignore unsupported schemes and links with no hostname.
            if parsed.scheme not in {"http", "https"}:
                continue

            if not is_same_domain(start_url, full_url):
                continue

            # Remove fragments so /page#section and /page
            # are treated as the same page.
            full_url = canonicalize_url(full_url)

            if full_url in visited or full_url in queued:
                continue

            # Bound the queue to avoid collecting thousands of URLs.
            if len(visited) + len(queued) >= max_pages:
                continue

            queued.add(full_url)
            queue.append(full_url)