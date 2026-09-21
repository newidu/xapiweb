"""xapiweb quickstart (reads only — writes are commented). Run: python3 examples/quickstart.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xapiweb import XClient
from xapiweb.resources.timelines import extract_tweets, cursors

SESSION = os.environ.get("XAPIWEB_SESSION", "my_data.json")

x = XClient.from_session_file(SESSION)
print("health:", x.health().status)
print("me:", x.me()["screen_name"], x.me()["id"])

# home timeline, parsed
home = x.timelines.home(count=5)
for t in extract_tweets(home)[:3]:
    print(f"- @{t['author']}: {t['text'][:70]!r} (RT:{t['retweet_count']} Fav:{t['favorite_count']})")
print("cursors:", cursors(home))

# search + trends + badges
print("search hits:", len(extract_tweets(x.timelines.search("xapiweb", count=5))))
print("trends woeids:", len(x.trends.available().get(default=[]) or []))
print("badges:", x.notifications.badge_counts().get(
    "data", "viewer_v2", "user_results", "result", "badge_counts"))

# ---- writes (uncomment to run; each verifies by re-reading) ----
# t = x.tweets.post("hello from xapiweb")
# print("posted:", t.tweet_id)
# x.tweets.delete(t.tweet_id)
# print("deleted + verified gone")
