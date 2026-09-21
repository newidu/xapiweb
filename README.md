# xapiweb

**xapiweb** is a zero-dependency Python client library for selected X web API operations. It provides one client, structured responses, resource modules, pacing, transaction IDs, verification for writes, and typed error handling.

> **Security:** This library uses a browser session supplied by the user. Never commit `my_data.json`, cookies, CSRF tokens, bearer tokens, or any other session material to GitHub or PyPI.

## Installation

```bash
pip install xapiweb
```

The package requires Python 3.8 or newer and has no runtime dependencies.

## Quick start

Create a private session file with your own X browser session, then:

```python
from xapiweb import XClient
from xapiweb.resources.timelines import extract_tweets

x = XClient.from_session_file("my_data.json")

print(x.health().status)  # 200 means the session is connected
print(x.me())

response = x.timelines.home(count=10)
for tweet in extract_tweets(response):
    print(tweet["author"], tweet["text"][:80])
```

You can also pass credentials directly:

```python
x = XClient(cookie="<full-cookie>", csrf_token="<ct0-value>")
```

Keep credentials outside source control. The `xapiweb` distribution does not contain a live session file.

## Main capabilities

- Timelines, search, trends, users, notifications, lists, communities, and settings.
- Tweet reads, posts, replies, threads, polls, deletes, pins, and disclosures.
- Image and chunked video upload, media inspection, and downloads.
- Likes, reposts, bookmarks, follows, moderation, and direct-message operations.
- Structured `Response` objects with `.status`, `.data`, `.raw`, `.ok`, `.get()`, and `.summary()`.
- Pacing between requests, one retry for rate-limit responses, transaction ID handling, and write verification.

Operations with real-world side effects require explicit confirmation arguments where applicable. Use the library only with an account and session you are authorized to control, and respect X terms, rate limits, privacy requirements, and applicable law.

## Authentication guide

1. Sign in to `x.com` in a desktop browser.
2. In browser developer tools, copy the complete `Cookie` request header and the `x-csrf-token` request header.
3. Confirm that the `x-csrf-token` value matches the `ct0` cookie value.
4. Store the values in a local, private session file. Do not upload that file.
5. Run a low-cost health check before other operations.

See [`xapiweb/CONNECT_GUIDE.md`](xapiweb/CONNECT_GUIDE.md) for the detailed Sinhala guide.

## Response and errors

Every request returns a `Response` object. Common exceptions include `XAuthError`, `XRateLimitError`, `XTxnError`, `XValidationError`, `XApiError`, and `XVerifyError`. A successful HTTP acknowledgement does not always mean that a state-changing operation completed; write verification is enabled by default.

## Tests

The package includes offline tests that do not contact X:

```bash
python3 xapiweb/tests/test_offline.py
```

The smoke and quickstart scripts require a private session file and live network access. Run them only with your own account and at a conservative request pace.

## Project layout

```text
xapiweb/
├── xapiweb/                  Python package and resource modules
├── examples/                 Local setup and quickstart examples
├── docs/index.html           Standalone black-and-white documentation page
├── pyproject.toml            Build metadata
├── xapiweb_smoke_live.py     Optional low-cost live health check
└── xapiweb_media_proof.py    Optional self-cleaning media proof
```

## License and status

Review and add the license that applies to your project before publishing future releases. This library is an unofficial client and may require maintenance when X changes its web application or request contracts.

## Links

- [PyPI package](https://pypi.org/project/xapiweb/)
- [TestPyPI package](https://test.pypi.org/project/xapiweb/)
- [Standalone documentation](docs/index.html)
