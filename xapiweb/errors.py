"""Structured errors for xapiweb (mapped from the pack's error catalog, guide §9)."""


class XError(Exception):
    """Base error for all xapiweb failures."""


class XHttpError(XError):
    """HTTP-level failure."""

    def __init__(self, url, status, body=""):
        self.url = url
        self.status = status
        self.body = body or ""
        super().__init__(f"HTTP {status} {url}: {self.body[:200]}")


class XAuthError(XHttpError):
    """401 — session dead (recapture cookies + ct0)."""


class XRateLimitError(XHttpError):
    """403/429 — throttle/challenge (already retried once; cool off)."""


class XTxnError(XError):
    """Bad/missing x-client-transaction-id masquerading as another error
    (REST 404 code 34, CreateTweet 200 with empty tweet_results, CreateBookmark 404,
    or 344 'daily limit' MISTEXT on a fresh account)."""


class XValidationError(XHttpError):
    """422 GRAPHQL_VALIDATION_FAILED — missing/wrong variable (see body path)."""


class XMethodError(XHttpError):
    """406 — mutation called via GET (use POST)."""


class XApiError(XError):
    """GraphQL data-level error (HTTP 200 with errors[])."""

    def __init__(self, code, message, op=""):
        self.code = code
        self.message = message or ""
        self.op = op
        super().__init__(f"[{op}] code {code}: {self.message[:250]}" if op else f"code {code}: {self.message[:250]}")


class XAutomationFlag(XApiError):
    """226 — 'looks like it might be automated' (slow down, cool off)."""


class XGateError(XApiError):
    """37 — Authorization: not author / no phone / no Premium / no eligibility."""


class XBadRequest(XApiError):
    """214 — BadRequest: bad token / invalid target."""


class XAlreadyError(XApiError):
    """327 — already retweeted (unretweet first)."""


class XDailyLimit(XApiError):
    """344 — daily limit (often MISTEXT when txn is bad — fix txn first)."""


class XVerifyError(XError):
    """Verify-by-reread failed: the ack lied or state did not change."""


def http_error(url, status, body):
    """Map an HTTP failure to a structured exception (guide §9)."""
    body = body or ""
    compact = body.replace(" ", "")
    if status == 401:
        return XAuthError(url, status, body)
    if status in (403, 429):
        return XRateLimitError(url, status, body)
    if status == 406:
        return XMethodError(url, status, body)
    if status == 422:
        return XValidationError(url, status, body)
    if status == 404 and '"code":34' in compact:
        return XTxnError(
            f"404 code 34 on {url}: almost certainly a bad/missing "
            f"x-client-transaction-id (not a dead endpoint). Regenerate txn for "
            f"the exact (method, path); probe account/settings (must 200)."
        )
    return XHttpError(url, status, body)


def guard(resp, op=""):
    """Raise on GraphQL data-level errors[]; return resp otherwise."""
    data = resp.data
    errs = data.get("errors") if isinstance(data, dict) else None
    if not errs:
        return resp
    e0 = errs[0] if isinstance(errs, list) else errs
    code = e0.get("code") if isinstance(e0, dict) else None
    msg = (e0.get("message", "") if isinstance(e0, dict) else str(e0)) or ""
    if code == 226:
        raise XAutomationFlag(code, msg, op)
    if code == 37:
        raise XGateError(code, msg, op)
    if code == 214:
        raise XBadRequest(code, msg, op)
    if code == 327:
        raise XAlreadyError(code, msg, op)
    if code == 344:
        raise XDailyLimit(code, msg, op)
    raise XApiError(code, msg, op)
