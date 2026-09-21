"""Offline self-test for xapiweb (no network). Run: python3 xapiweb/tests/test_offline.py"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from xapiweb import XClient, Session, Response, errors, QIDS
from xapiweb.resources.timelines import extract_tweets, cursors


class TestPack(unittest.TestCase):
    def test_qids(self):
        self.assertGreaterEqual(len(QIDS), 115, f"only {len(QIDS)} qids")
        for op in ("CreateTweet", "HomeTimeline", "Followers", "SearchTimeline",
                   "DeleteRetweet", "dmBlockUser", "ViewerBadgeCounts"):
            self.assertIn(op, QIDS)

    def test_features(self):
        s = Session(cookie="c", csrf_token="t")
        self.assertEqual(len(s.features), 40)
        self.assertIn("withPayments", s.field_toggles)
        self.assertEqual(s.min_interval, 1.0)

    def test_session_file(self):
        d = {"cookie": "abc", "csrf_token": "ct0", "bearer": "B", "user_agent": "U",
             "reference_ids": {"self_id": "123", "self_screen_name": "me"}}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(d, f)
            path = f.name
        try:
            s = Session.from_session_file(path)
            self.assertEqual(s.cookie, "abc")
            self.assertEqual(s.refs["self_id"], "123")
            c = XClient.from_session_file(path)
            self.assertEqual(c.me_id, "123")  # no network: from refs
        finally:
            os.unlink(path)
            cache = os.path.join(os.path.dirname(path), ".txn_cache.json")
            if os.path.exists(cache):
                os.unlink(cache)

    def test_response(self):
        r = Response(url="u", status=200, headers={}, raw='{"a":{"b":[1,2]}}')
        self.assertTrue(r.ok)
        self.assertEqual(r.get("a", "b", 1), 2)
        self.assertIsNone(r.get("x", "y"))
        self.assertEqual(r.get("x", default="d"), "d")
        self.assertIn("a", r.summary(10))

    def test_http_error_map(self):
        self.assertIsInstance(errors.http_error("u", 401, ""), errors.XAuthError)
        self.assertIsInstance(errors.http_error("u", 429, ""), errors.XRateLimitError)
        self.assertIsInstance(errors.http_error("u", 406, ""), errors.XMethodError)
        self.assertIsInstance(errors.http_error("u", 422, ""), errors.XValidationError)
        e = errors.http_error("u", 404, '{"code":34,"message":"Sorry"}')
        self.assertIsInstance(e, errors.XTxnError)
        self.assertIsInstance(errors.http_error("u", 404, "other"), errors.XHttpError)

    def test_guard(self):
        def resp(code, msg="m"):
            return Response(url="u", status=200, headers={},
                            raw=json.dumps({"errors": [{"code": code, "message": msg}]}))
        self.assertIs(errors.guard(Response(url="u", status=200, headers={}, raw='{"data":{}}'), "op").ok, True)
        for code, exc in ((226, errors.XAutomationFlag), (37, errors.XGateError),
                          (214, errors.XBadRequest), (327, errors.XAlreadyError),
                          (344, errors.XDailyLimit), (999, errors.XApiError)):
            with self.assertRaises(exc, msg=code):
                errors.guard(resp(code), "op")

    def test_client_composition(self):
        c = XClient(cookie="c", csrf_token="t")
        for name in ("tweets", "engagement", "timelines", "users", "follows", "moderation",
                     "lists", "dms", "communities", "trends", "notifications", "settings",
                     "media", "misc"):
            self.assertTrue(hasattr(c, name), name)
        # spot-check method surface
        self.assertTrue(callable(c.tweets.post) and callable(c.tweets.set_reply_control))
        self.assertTrue(callable(c.engagement.unretweet) and callable(c.dms.inbox))
        self.assertTrue(callable(c.media.upload_image))
        with self.assertRaises(errors.XError):
            c.dms.send("1", "hi")  # confirm=True required
        # pure-client validation (no network: raises before any call)
        with self.assertRaises(ValueError):
            c.tweets.create_poll_card(["only-one"])
        with self.assertRaises(ValueError):
            c.tweets.create_poll_card(["a", "b", "c", "d", "e"])
        with self.assertRaises(ValueError):
            c.tweets.create_poll_card(["ok", "x" * 26])
        with self.assertRaises(ValueError):
            c.tweets.create_poll_card(["a", "b"], duration_minutes=2)
        with self.assertRaises(ValueError):
            c.tweets.post_thread([])
        with self.assertRaises(errors.XError):
            c.dms.set_nsfw_filter(confirm=False)
        with self.assertRaises(errors.XError):
            c.follows.remove_follower("1")

    def test_extract_tweets(self):
        data = {"data": {"home": {"home_timeline_urt": {"instructions": [
            {"entries": [
                {"content": {"itemContent": {"tweet_results": {"result": {
                    "rest_id": "1",
                    "views": {"count": "99", "state": "EnabledWithCount"},
                    "legacy": {"full_text": "hi", "retweeted": False, "favorited": True,
                               "retweet_count": 2, "favorite_count": 3},
                    "core": {"user_results": {"result": {"legacy": {"screen_name": "bob"}}}}}}}}},
                {"content": {"cursorType": "Bottom", "value": "CUR123"}}]}]}}}}
        tw = extract_tweets(data)
        self.assertEqual(len(tw), 1)
        self.assertEqual(tw[0]["author"], "bob")
        self.assertEqual(tw[0]["text"], "hi")
        self.assertEqual(tw[0]["views"], 99)
        self.assertEqual(cursors(data)["bottom"], "CUR123")

    def test_parse_media(self):
        from xapiweb.resources.media import parse_media_entities
        leg = {"extended_entities": {"media": [
            {"type": "photo", "id_str": "1",
             "media_url_https": "https://pbs.twimg.com/media/a.jpg",
             "original_info": {"width": 100, "height": 50}},
            {"type": "video", "id_str": "2",
             "media_url_https": "https://pbs.twimg.com/thumb.jpg",
             "video_info": {"duration_millis": 5000, "variants": [
                 {"content_type": "application/x-mpegURL", "url": "https://x.m3u8"},
                 {"content_type": "video/mp4", "bitrate": 100, "url": "https://low.mp4"},
                 {"content_type": "video/mp4", "bitrate": 900, "url": "https://hi.mp4"}]}}]}}
        m = parse_media_entities(leg)
        self.assertEqual(len(m), 2)
        self.assertEqual(m[0]["url"], "https://pbs.twimg.com/media/a.jpg")
        self.assertEqual(m[1]["url"], "https://hi.mp4")  # max bitrate mp4
        self.assertEqual(m[1]["bitrate"], 900)
        self.assertEqual(parse_media_entities({}), [])

    def test_extract_notifications(self):
        from xapiweb.resources.notifications import extract_notifications
        data = {"data": {"viewer_v2": {"user_results": {"result": {"notification_timeline": {
            "timeline": {"instructions": [{"entries": [
                {"entryId": "notification-1", "content": {
                    "clientEventInfo": {"element": "users_liked_your_tweet"},
                    "itemContent": {
                        "__typename": "TimelineNotification", "id": "n1",
                        "notification_icon": "heart_icon",
                        "notification_url": {"url": "https://twitter.com/me/status/123"},
                        "timestamp_ms": "2026-09-20T01:02:03.000Z",
                        "rich_message": {"text": "Bob liked your post", "entities": [
                            {"ref": {"user_results": {"result": {
                                "core": {"screen_name": "bob", "name": "Bob"}}}}}]}}}},
                {"entryId": "cursor-bottom", "content": {"itemContent": {
                    "__typename": "TimelineTimelineCursor", "cursorType": "Bottom",
                    "value": "BOT123"}}}]}]}}}}}}}
        n = extract_notifications(data)
        self.assertEqual(len(n), 1)
        self.assertEqual(n[0]["type"], "users_liked_your_tweet")
        self.assertEqual(n[0]["tweet_id"], "123")
        self.assertEqual(n[0]["users"][0]["screen_name"], "bob")


if __name__ == "__main__":
    unittest.main(verbosity=2)
