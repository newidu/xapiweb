"""Live smoke: 3 cheap reads via xapiweb. Run: python3 xapiweb_smoke_live.py"""
import sys
from xapiweb import XClient

x = XClient.from_session_file("my_data.json")
print("health:", x.health().status)
print("me:", x.me()["screen_name"], x.me()["id"])
print("viewer:", x.users.viewer().status)
print("home:", x.timelines.home(count=3).status)
print("SMOKE OK")
