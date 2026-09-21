"""xapiweb — unified Python library for the X web API (stdlib only).

Built from the proven x_api_pack (157/157 tests live 2026-09-19):
every method maps to a live-tested endpoint; writes verify by re-reading.
"""
from .client import XClient
from .session import Session
from .response import Response
from . import errors
from .qids import QIDS

__version__ = "1.5.0"
__all__ = ["XClient", "Session", "Response", "errors", "QIDS"]
