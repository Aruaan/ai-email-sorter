import re
from typing import List
from models.email import Email
from bs4 import BeautifulSoup, Tag
from urllib.parse import unquote

def extract_unsubscribe_links(email: Email) -> List[str]:
    links = set()
    # 1. Check for List-Unsubscribe header in headers dict
    if email.headers:
        unsub_header = email.headers.get('List-Unsubscribe')
        if unsub_header:
            # Can be comma-separated, may have <...> or "..."
            for part in unsub_header.split(','):
                url = part.strip().strip('<>"')
                if url.startswith('http') or url.startswith('mailto:'):
                    links.add(url)
    # 2. Check for List-Unsubscribe header in raw (legacy fallback, multi-format)
    header_matches = re.findall(r'List-Unsubscribe:\s*([<\"].*?[>\"])', email.raw, re.IGNORECASE)
    for match in header_matches:
        url = match.strip('<>"')
        if url.startswith('http') or url.startswith('mailto:'):
            links.add(url)
    # 3. Try to extract HTML part if present
    html = None
    # Try to find an HTML part in raw
    html_match = re.search(r'<html[\s\S]*?</html>', email.raw, re.IGNORECASE)
    if html_match:
        html = html_match.group(0)
    # If not, treat the whole raw as HTML if it looks like HTML
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
                    links.add(str(href))
    # 5. Parse plain text for unsubscribe URLs
    # Remove HTML if present to avoid duplicate extraction
    plain = email.raw
    if html:
        plain = re.sub(r'<html[\s\S]*?</html>', '', plain, flags=re.IGNORECASE)
    url_regex = r'https?://\S+'
    for match in re.findall(url_regex, plain):
        url = unquote(match)
        if 'unsubscribe' in url.lower():
            links.add(url)
    return list(links) 