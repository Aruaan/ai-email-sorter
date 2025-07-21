from utils.unsubscribe import extract_unsubscribe_links
from models.email import Email

def test_extract_unsubscribe_links_from_real_headers():
    # Simulate a real email object using your actual header values and raw content
    headers = {
        "list-unsubscribe": "<https://buttondown.com/unsubscribe/656c6374-6515-43c7-ab1c-143acab86d67?email=dce1b8fc-f39f-432c-b188-80be5ae71de0>",
        "from": '"Mladen Boškov" <boskov@buttondown.email>',
        "to": "boskov.ml@gmail.com",
        "subject": "yoooo"
    }

    # Add this header into the raw text block, simulating a real raw message
    raw = (
        "List-Unsubscribe: <https://buttondown.com/unsubscribe/656c6374-6515-43c7-ab1c-143acab86d67?email=dce1b8fc-f39f-432c-b188-80be5ae71de0>\n"
        "\n"
        "<html><body>"
        '<a href="https://buttondown.com/unsubscribe/656c6374-6515-43c7-ab1c-143acab86d67?email=dce1b8fc-f39f-432c-b188-80be5ae71de0">'
        "Click here to unsubscribe</a>"
        "</body></html>"
    )

    email = Email(
        id=1,
        subject="yoooo",
        from_email="boskov@buttondown.email",
        category_id=1,
        summary="test",
        raw=raw,
        headers=headers,
        user_email="user@example.com",
        gmail_id="abc123"
    )

    links = extract_unsubscribe_links(email)

    assert "https://buttondown.com/unsubscribe/656c6374-6515-43c7-ab1c-143acab86d67?email=dce1b8fc-f39f-432c-b188-80be5ae71de0" in links
    assert all("unsubscribe" in link.lower() for link in links)

def test_extract_unsubscribe_links_various_formats():
    from utils.unsubscribe import extract_unsubscribe_links
    from models.email import Email
    # HTML, plain text, malformed, etc.
    email = Email(
        id=1, subject="s", from_email="f", category_id=1, summary="s", raw='List-Unsubscribe: <http://a.com/unsub>\n<a href="http://b.com/unsub">Unsub</a>', user_email="u", gmail_id="g"
    )
    links = extract_unsubscribe_links(email)
    assert "http://a.com/unsub" in links or "http://b.com/unsub" in links
