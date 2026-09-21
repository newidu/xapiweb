import sys, time
sys.path.insert(0, "/home/user")
from xapiweb import XClient
x = XClient.from_session_file("/home/user/unzipped/x_api_pack/my_data.json")
jpg = open("/tmp/real.jpg","rb").read()
mid = x.media.upload_image(jpg, media_type="image/jpeg", alt_text="xapiweb proof photo")
print("media_id:", mid)
t = x.tweets.post(f"xapiweb photo test {int(time.time())} - auto-deleting", media_ids=[mid])
nid = t.tweet_id
print("posted:", nid)
back = x.tweets.get(nid)
leg = back.get("data","tweetResult","result","legacy", default={}) or {}
attached = any(str(m.get("media_id_string") or m.get("id_str")) == str(mid)
               for key in ("entities","extended_entities")
               for m in ((leg.get(key) or {}).get("media") or []))
print("attached:", attached)
x.tweets.delete(nid, verify=True)
print("deleted + verified gone")
print("MEDIA PROOF:", "OK" if attached else "ATTACH-NOT-CONFIRMED")
