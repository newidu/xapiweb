"""Session: auth, txn-id, pacing, and low-level HTTP for X web APIs.

Engine ported from the proven x_api_pack (common.py, live 2026-09-19),
repackaged as a class so secrets are never module-global.
Stdlib only.
"""
import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from ._txn import ClientTransaction
from .qids import QIDS
from .response import Response
from . import errors as E

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
DEFAULT_BEARER = ("AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D"
                  "1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA")
DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:154.0) "
              "Gecko/20100101 Firefox/154.0")
TXN_TTL = 600  # one homepage load serves many calls, like a browser tab


class Session:
    def __init__(self, cookie, csrf_token, bearer=None, user_agent=None,
                 txn_cache=None, min_interval=1.0, timeout=25):
        if not cookie or not csrf_token:
            raise E.XError("cookie and csrf_token are required")
        self.cookie = cookie
        self.csrf_token = csrf_token
        self.bearer = bearer or DEFAULT_BEARER
        self.user_agent = user_agent or DEFAULT_UA
        self.txn_cache = txn_cache or os.path.join(tempfile.gettempdir(), "xapiweb_txn_cache.json")
        self.min_interval = min_interval
        self.timeout = timeout
        with open(os.path.join(DATA_DIR, "features.json")) as f:
            self.features = json.load(f)
        with open(os.path.join(DATA_DIR, "fieldtoggles.json")) as f:
            self.field_toggles = json.load(f)
        self._txn = None
        self._last_call = 0.0
        self.refs = {}      # reference_ids from session file (self_id, ...)
        self.account = None

    @classmethod
    def from_session_file(cls, path, **kw):
        """Load a my_data.json-style session file (cookie + csrf_token + ...)."""
        with open(path) as f:
            d = json.load(f)
        s = cls(
            d["cookie"], d.get("csrf_token") or d.get("ct0"),
            bearer=d.get("bearer"), user_agent=d.get("user_agent"),
            txn_cache=kw.pop("txn_cache", os.path.join(
                os.path.dirname(os.path.abspath(path)), ".txn_cache.json")),
            **kw)
        s.refs = d.get("reference_ids", {}) or {}
        s.account = d.get("account")
        return s

    # ---------------- transaction id ----------------
    def _key_works(self, html):
        """True if txn-ids minted from this homepage HTML are accepted (cheap probe)."""
        try:
            t = ClientTransaction()
            t.init_from_html(html)
            tid = t.generate_transaction_id(method="GET", path="/1.1/account/settings.json")
        except Exception:
            return False
        hh = {"Authorization": f"Bearer {self.bearer}", "x-twitter-auth-type": "OAuth2Session",
              "x-csrf-token": self.csrf_token, "x-twitter-client-language": "en",
              "x-twitter-active-user": "yes", "x-client-transaction-id": tid,
              "User-Agent": self.user_agent, "Accept": "*/*", "Referer": "https://x.com/home",
              "Cookie": self.cookie}
        try:
            req = urllib.request.Request("https://api.x.com/1.1/account/settings.json",
                                         headers=hh, method="GET")
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status == 200
        except Exception:
            return False

    def _txn_html(self):
        """Logged-in homepage HTML with a WORKING key, cached on disk."""
        try:
            d = json.load(open(self.txn_cache))
            html = d.get("html", "")
            if time.time() - d.get("saved_at", 0) < TXN_TTL and self._key_works(html):
                return html
        except Exception:
            pass
        for _ in range(3):
            req = urllib.request.Request("https://x.com/home",
                                         headers={"User-Agent": self.user_agent,
                                                  "Cookie": self.cookie, "Accept": "text/html"})
            html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
            if "loading-x-anim" in html and "twitter-site-verification" in html \
                    and self._key_works(html):
                try:
                    json.dump({"saved_at": time.time(), "html": html}, open(self.txn_cache, "w"))
                except Exception:
                    pass
                return html
            time.sleep(2)
        raise RuntimeError("3 homepage loads yielded no working transaction key")

    def txn_id(self, method: str, path: str) -> str:
        """Valid x-client-transaction-id for one (method, path)."""
        if self._txn is None:
            self._txn = ClientTransaction()
            self._txn.init_from_html(self._txn_html())
        return self._txn.generate_transaction_id(method=method, path=path)

    def headers(self, method: str, path: str, referer="https://x.com/home"):
        return {
            "Authorization": f"Bearer {self.bearer}",
            "x-twitter-auth-type": "OAuth2Session",
            "x-csrf-token": self.csrf_token,
            "x-twitter-client-language": "en",
            "x-twitter-active-user": "yes",
            "x-client-transaction-id": self.txn_id(method, path),
            "User-Agent": self.user_agent, "Accept": "*/*",
            "Referer": referer, "Cookie": self.cookie,
        }

    # ---------------- HTTP ----------------
    def _pace(self):
        wait = self.min_interval - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)

    def call(self, method, url, payload=None, content_type="application/json",
             referer="https://x.com/home", timeout=None) -> Response:
        """One HTTP call with pacing + one retry on 403/429. Raises structured errors."""
        self._pace()
        path = urllib.parse.urlparse(url).path
        hh = self.headers(method, path, referer)
        data = None
        if payload is not None:
            data = payload.encode() if isinstance(payload, str) else payload
            hh["Content-Type"] = content_type
            hh["Origin"] = "https://x.com"
            hh["Content-Length"] = str(len(data))
        req = urllib.request.Request(url, data=data, headers=hh, method=method)
        to = timeout or self.timeout
        try:
            for attempt in (0, 1):
                try:
                    with urllib.request.urlopen(req, timeout=to) as resp:
                        self._last_call = time.monotonic()
                        return Response(url=url, status=resp.status,
                                        headers=dict(resp.headers),
                                        raw=resp.read().decode("utf-8", "replace"))
                except urllib.error.HTTPError as e:
                    if e.code in (403, 429) and attempt == 0:
                        time.sleep(5)
                        continue
                    raise
        except urllib.error.HTTPError as e:
            self._last_call = time.monotonic()
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")
            except Exception:
                pass
            raise E.http_error(url, e.code, body)

    # ---------------- GraphQL / REST helpers ----------------
    def gql_get(self, op, variables, with_features=True, with_toggles=True) -> Response:
        qid = QIDS[op]
        qs = {"variables": json.dumps(variables, separators=(",", ":"))}
        if with_features:
            qs["features"] = json.dumps(self.features, separators=(",", ":"))
        if with_toggles:
            qs["fieldToggles"] = json.dumps(self.field_toggles, separators=(",", ":"))
        url = f"https://x.com/i/api/graphql/{qid}/{op}?" + urllib.parse.urlencode(qs)
        return self.call("GET", url)

    def gql_post(self, op, variables, with_features=False) -> Response:
        qid = QIDS[op]
        url = f"https://x.com/i/api/graphql/{qid}/{op}"
        payload = {"variables": variables, "queryId": qid}
        if with_features:
            payload["features"] = self.features
        return self.call("POST", url, json.dumps(payload))

    def rest_get(self, path, params=None, host="https://x.com", prefix="/i/api/1.1/") -> Response:
        url = host + prefix + path.lstrip("/") + ("?" + urllib.parse.urlencode(params) if params else "")
        return self.call("GET", url)

    def rest_post_form(self, path, form, host="https://x.com", prefix="/i/api/1.1/") -> Response:
        url = host + prefix + path.lstrip("/")
        return self.call("POST", url, urllib.parse.urlencode(form),
                         "application/x-www-form-urlencoded; charset=UTF-8")

    @staticmethod
    def jget(body, *keys, default=None):
        try:
            cur = json.loads(body) if isinstance(body, str) else body
            for k in keys:
                cur = cur[k]
            return cur
        except Exception:
            return default

    @staticmethod
    def summarize(body, limit=600):
        body = body if isinstance(body, str) else json.dumps(body)
        return body[:limit] + ("…(truncated)" if len(body) > limit else "")
