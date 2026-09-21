"""Response: one parsed wrapper for every xapiweb call."""
import json
from dataclasses import dataclass, field


@dataclass
class Response:
    url: str
    status: int
    headers: dict
    raw: str
    _data: object = field(default=None, repr=False, compare=False)

    @property
    def data(self):
        if self._data is None:
            try:
                self._data = json.loads(self.raw)
            except Exception:
                self._data = {}
        return self._data

    @property
    def ok(self):
        return 200 <= self.status < 300

    def get(self, *keys, default=None):
        """Safe nested walk over parsed JSON (dict keys or list indices)."""
        cur = self.data
        try:
            for k in keys:
                cur = cur[k]
            return cur
        except Exception:
            return default

    def summary(self, limit=600):
        body = self.raw if isinstance(self.raw, str) else json.dumps(self.raw)
        return body[:limit] + ("…(truncated)" if len(body) > limit else "")
