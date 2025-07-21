import re
from typing import List
from backend.models.email import Email
from bs4 import BeautifulSoup, Tag
from urllib.parse import unquote
from email.parser import HeaderParser

def normalize_headers(headers):
    if isinstance(headers, dict):
        return {k.lower(): v for k, v in headers.items()}
    if isinstance(headers, str):
        return {k.lower(): v for k, v in HeaderParser().parsestr(headers).items()}
    return {}

def extract_unsubscribe_links(email: Email) -> List[str]:
    links = set()
    # 1. Normalize headers
    headers = normalize_headers(email.headers)
    print(f"Debug - Normalized headers: {headers}")
    unsub_header = headers.get('list-unsubscribe')
    print(f"Debug - list-unsubscribe header: {unsub_header}")
    if unsub_header:
        for part in re.split(r',\s*', unsub_header):
            url = part.strip().strip('<>"')
            # Remove trailing punctuation
            url = re.sub(r'[),.]+$', '', url)
            if url.startswith('http') or url.startswith('mailto:'):
                links.add(url)
    # 2. Check for List-Unsubscribe header in raw (legacy fallback)
    header_matches = re.findall(r'List-Unsubscribe:\s*([^\n]+)', email.raw, re.IGNORECASE)
    for match in header_matches:
        for part in re.split(r',\s*', match):
            url = part.strip().strip('<>"')
            url = re.sub(r'[),.]+$', '', url)
            if url.startswith('http') or url.startswith('mailto:'):
                links.add(url)
    # 3. Try to extract HTML part if present
    html = None
    html_match = re.search(r'<html[\s\S]*?</html>', email.raw, re.IGNORECASE)
    if html_match:
        html = html_match.group(0)
    elif email.raw.strip().startswith('<html'):
        html = email.raw
    # 4. Parse HTML for unsubscribe links
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.find_all('a', href=True):
            if isinstance(a, Tag):
                href = a.get('href', '')
                text = a.get_text(strip=True)
                if 'unsubscribe' in text.lower() or 'unsubscribe' in str(href).lower():
                    # Remove trailing punctuation from href
                    href = re.sub(r'[),.]+$', '', href)
                    links.add(str(href))
    # 5. Parse plain text for unsubscribe URLs
    url_regex = r'https?://[^\s<>"\)\(]+'
    for match in re.findall(url_regex, email.raw):
        url = unquote(match)
        url = re.sub(r'[),.]+$', '', url)
        if 'unsubscribe' in url.lower():
            links.add(url)
    print(f"Debug - Final unsubscribe links: {list(links)}")
    return list(links) 