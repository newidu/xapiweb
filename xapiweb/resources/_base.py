"""Shared base for all resources."""


class BaseResource:
    def __init__(self, client):
        self._client = client

    @property
    def _s(self):
        return self._client.session

    def _me(self):
        return self._client.me_id
