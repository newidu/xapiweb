"""Live smoke: 3 cheap reads via xapiweb. Run: python3 xapiweb_smoke_live.py"""
import sys
from xapiweb import XClient

session_path = sys.argv[1] if len(sys.argv) > 1 else "my_data.json"
x = XClient.from_session_file(session_path)
print("health:", x.health().status)
print("me:", x.me()["screen_name"], x.me()["id"])
print("viewer:", x.users.viewer().status)
print("home:", x.timelines.home(count=3).status)
print("SMOKE OK")
