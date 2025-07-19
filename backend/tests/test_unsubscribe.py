from utils.unsubscribe import extract_unsubscribe_links
from models.email import Email

def test_extract_unsubscribe_links_html_and_text():
    raw = (
        'List-Unsubscribe: <https://unsubscribe.example.com/unsub>\n'
        '<html><body>'
        '<a href="https://unsubscribe.example.com/unsub">Unsubscribe here</a>'
        '<a href="https://other.example.com/keep">Keep</a>'
        'Or visit https://unsubscribe.example.com/unsub2 in your browser.'
        '</body></html>'
    )
    email = Email(
        id=1, subject="Test", from_email="a@b.com", category_id=1,
        summary="s", raw=raw, user_email="u@e.com", gmail_id="gid"
    )
    links = extract_unsubscribe_links(email)
    assert "https://unsubscribe.example.com/unsub" in links
    assert "https://unsubscribe.example.com/unsub2" in links
    assert all("keep" not in l for l in links) 