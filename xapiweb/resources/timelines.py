"""Timelines: home, user timelines, search, followers, pins + URT parsing helpers."""
from ._base import BaseResource


def extract_tweets(resp_or_data, limit=50):
    """Pull [{rest_id, author, text, views, retweeted, favorited, counts}] out of any
    timeline response (walks URT instructions). xapiweb helper."""
    data = resp_or_data.data if hasattr(resp_or_data, "data") else resp_or_data
    tweets, seen = [], set()

    def walk(obj):
        if len(tweets) >= limit:
            return
        if isinstance(obj, dict):
            tr = obj.get("tweet_results")
            if isinstance(tr, dict):
                r = tr.get("result", {})
                rid = r.get("rest_id") if isinstance(r, dict) else None
                if rid and rid not in seen:
                    seen.add(rid)
                    leg = r.get("legacy", {}) or {}
                    author = "?"
                    try:
                        author = r["core"]["user_results"]["result"]["legacy"]["screen_name"]
                    except Exception:
                        try:
                            author = r["core"]["user_results"]["result"]["core"]["screen_name"]
                        except Exception:
                            pass
                    tweets.append({"rest_id": rid, "author": author,
                                   "text": leg.get("full_text") or "",
                                   "views": _views(r),
                                   "retweeted": leg.get("retweeted"),
                                   "favorited": leg.get("favorited"),
                                   "retweet_count": leg.get("retweet_count"),
                                   "favorite_count": leg.get("favorite_count")})
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    walk(data.get("data", data) if isinstance(data, dict) else data)
    return tweets


def _views(result):
    """result.views.count -> int (or None). Lives at result level, not legacy."""
    try:
        return int((result.get("views") or {}).get("count"))
    except (TypeError, ValueError):
        return None


def cursors(resp_or_data):
    """Return {'top': ..., 'bottom': ...} pagination cursors (may be None). xapiweb helper."""
    data = resp_or_data.data if hasattr(resp_or_data, "data") else resp_or_data
    out = {"top": None, "bottom": None}

    def walk(obj):
        if isinstance(obj, dict):
            if obj.get("cursorType") in ("Top", "Bottom") and obj.get("value"):
                out[obj["cursorType"].lower()] = obj["value"]
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    walk(data)
    return out


class Timelines(BaseResource):
    def home(self, count=5, seen_ids=None):
        """Home/For-you (POST). Proven: test_home_timeline.py"""
        return self._s.gql_post("HomeTimeline", {
            "count": count, "includePromotedContent": True,
            "requestContext": "launch", "withCommunity": True,
            "seenTweetIds": seen_ids or []}, with_features=True)

    # ---- user timelines (GET) ----
    def _user_tl(self, op, user_id, count, extra=None):
        v = {"userId": str(user_id or self._me()), "count": count,
             "includePromotedContent": False, "withVoice": True}
        if extra:
            v.update(extra)
        return self._s.gql_get(op, v)

    def user_tweets(self, user_id=None, count=5):
        """Proven: test_user_tweets.py"""
        return self._user_tl("UserTweets", user_id, count,
                             {"includePromotedContent": True})

    def user_replies(self, user_id=None, count=5):
        """Proven: test_user_replies.py"""
        return self._s.gql_get("UserRepliesTimeline",
                               {"userId": str(user_id or self._me()), "count": count,
                                "includePromotedContent": False, "withVoice": True})

    def user_media(self, user_id=None, count=5):
        """Proven: test_user_media.py"""
        return self._user_tl("UserMedia", user_id, count, {"withClientEventToken": False})

    def user_likes(self, user_id=None, count=5):
        """Proven: test_user_likes.py"""
        return self._user_tl("Likes", user_id, count, {"withClientEventToken": False})

    def user_reposts(self, user_id=None, count=5):
        """Proven: test_user_reposts.py"""
        return self._user_tl("UserRepostsTimeline", user_id, count)

    def user_video(self, user_id=None, count=5):
        """Proven: test_user_video_timeline.py"""
        return self._user_tl("UserVideoTimeline", user_id, count, {"withClientEventToken": False})

    def user_highlights(self, user_id=None, count=5):
        """Proven: test_user_highlights.py"""
        return self._user_tl("UserHighlightsTweets", user_id, count)

    def user_articles(self, user_id=None, count=5):
        """Proven: test_user_articles.py"""
        return self._user_tl("UserArticlesTweets", user_id, count)

    def user_photo(self, user_id=None, count=5):
        """Proven: test_user_photo_timeline.py"""
        return self._user_tl("UserPhotoTimeline", user_id, count)

    def user_originals(self, user_id=None, count=5):
        """Proven: test_user_originals_timeline.py"""
        return self._s.gql_get("UserOriginalsTimeline",
                               {"userId": str(user_id or self._me()), "count": count,
                                "includePromotedContent": True,
                                "withQuickPromoteEligibilityTweetFields": True, "withVoice": True})

    def user_tweets_and_replies(self, user_id=None, count=5):
        """POST-only. Proven: test_user_tweets_and_replies.py"""
        return self._s.gql_post("UserTweetsAndReplies", {
            "userId": str(user_id or self._me()), "count": count,
            "includePromotedContent": False, "withVoice": True}, with_features=True)

    def user_super_follow(self, user_id=None, count=5):
        """Proven: test_user_super_follow_tweets.py"""
        return self._user_tl("UserSuperFollowTweets", user_id, count)

    def user_promoted(self, user_id=None, count=5):
        """Proven: test_user_promoted_tweets.py"""
        return self._s.gql_get("UserPromotedTweets",
                               {"userId": str(user_id or self._me()), "count": count})

    def user_promotable(self, user_id=None, count=5):
        """Proven: test_user_promotable_tweets.py"""
        return self._s.gql_get("UserPromotableTweets",
                               {"userId": str(user_id or self._me()), "count": count})

    # ---- follow graphs (GraphQL) ----
    def followers(self, user_id=None, count=5):
        """POST-only (GET 404s). Proven: test_followers_gql.py"""
        return self._s.gql_post("Followers", {
            "userId": str(user_id or self._me()), "count": count,
            "includePromotedContent": False}, with_features=True)

    def following(self, user_id=None, count=5):
        """Proven: test_following_gql.py"""
        return self._s.gql_get("Following", {
            "userId": str(user_id or self._me()), "count": count,
            "includePromotedContent": False}, with_toggles=False)

    def blue_verified_followers(self, user_id=None, count=5):
        """Proven: test_blue_verified_followers.py"""
        return self._s.gql_get("BlueVerifiedFollowers", {
            "userId": str(user_id or self._me()), "count": count,
            "includePromotedContent": False}, with_toggles=False)

    def followers_you_know(self, user_id=None, count=5):
        """Proven: test_followers_you_know.py"""
        return self._s.gql_get("FollowersYouKnow", {
            "userId": str(user_id or self._me()), "count": count,
            "includePromotedContent": False})

    # ---- search ----
    def search(self, raw_query, count=5, product="Top"):
        """POST-only. Proven: test_search_timeline.py"""
        return self._s.gql_post("SearchTimeline", {
            "rawQuery": raw_query, "count": count,
            "querySource": "typed_query", "product": product}, with_features=True)

    def list_search(self, list_id, raw_query, count=5):
        """Proven: test_list_search.py"""
        return self._s.gql_get("ListSearchTimeline",
                               {"listId": str(list_id), "rawQuery": raw_query, "count": count})

    def communities_post_search(self, raw_query, count=5):
        """Proven: test_communities_post_search.py"""
        return self._s.gql_get("GlobalCommunitiesPostSearchTimeline",
                               {"rawQuery": raw_query, "count": count})

    def communities_latest_search(self, raw_query, count=5):
        """Proven: test_communities_latest_search.py"""
        return self._s.gql_get("GlobalCommunitiesLatestPostSearchTimeline",
                               {"rawQuery": raw_query, "count": count})

    # ---- misc timelines ----
    def generic_by_id(self, timeline_id):
        """Ids are opaque server handles; bogus id => routed 200 error. Proven: test_generic_timeline.py"""
        return self._s.gql_get("GenericTimelineById", {"timelineId": str(timeline_id)},
                               with_features=False, with_toggles=False)

    def moderated(self, root_tweet_id, count=5):
        """Community moderation queue view. Proven: test_moderated_timeline.py"""
        return self._s.gql_get("ModeratedTimeline", {
            "rootTweetId": str(root_tweet_id), "count": count, "includePromotedContent": False})

    def pinned(self, user_id=None):
        """Profile pinned timelines. Proven: test_pinned_timelines.py"""
        return self._s.gql_get("PinnedTimelines", {"userId": str(user_id or self._me())},
                               with_toggles=False)

    def pinnable(self):
        """Proven: test_pinnable_timelines.py"""
        return self._s.gql_get("PinnableTimelines", {})

    def profile_filter(self, user_id=None, bucket="posts"):
        """BROKEN server-side (timeline.bucket 500s for every user, 2026-09-19).
        Other buckets => 422. Proven: test_profile_filter.py"""
        return self._s.gql_post("ProfileFilter", {
            "userId": str(user_id or self._me()), "includePromotedContent": False,
            "withVoice": True, "bucket": bucket})
