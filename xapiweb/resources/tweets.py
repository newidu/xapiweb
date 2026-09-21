"""Tweets: read, post, delete, pin, reply-controls, disclosures."""
from .. import errors as E
from ._base import BaseResource
from .media import parse_media_entities

REPLY_MODES = ("ByInvitation", "Verified", "Subscribers", "Community", "MyNetwork", "CountryOfOrigin")


class Tweets(BaseResource):
    # ---------------- read ----------------
    def get(self, tweet_id):
        """Tweet by id. Proven: test_tweet_by_id.py"""
        return self._s.gql_get("TweetResultByRestId", {
            "tweetId": str(tweet_id), "withCommunity": False,
            "withVoice": True, "includePromotedContent": False})

    def get_many(self, tweet_ids):
        """Batch tweets by ids. Proven: test_tweet_results_by_rest_ids.py"""
        return self._s.gql_get("TweetResultsByRestIds", {
            "tweetIds": [str(i) for i in tweet_ids], "includePromotedContent": False,
            "withVoice": True, "withCommunity": False})

    def detail(self, focal_tweet_id):
        """Conversation/detail (thread + replies). Proven: test_tweet_detail.py"""
        return self._s.gql_get("TweetDetail", {
            "focalTweetId": str(focal_tweet_id), "with_rux_injections": False,
            "rankingMode": "Relevance", "includePromotedContent": True,
            "withCommunity": True, "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True, "withBirdwatchNotes": False})

    def oembed(self, tweet_url):
        """oEmbed card for a tweet URL. Proven: test_oembed.py"""
        return self._s.rest_get("statuses/oembed.json", {"url": tweet_url})

    def quick_promote_eligibility(self, tweet_id):
        """Proven: test_quick_promote_eligibility.py"""
        return self._s.gql_get("QuickPromoteEligibility", {"tweetId": str(tweet_id)},
                               with_features=False, with_toggles=False)

    def moderated_view(self, root_tweet_id, count=5):
        """Proven: test_moderated_timeline.py"""
        return self._s.gql_get("ModeratedTimeline", {
            "rootTweetId": str(root_tweet_id), "count": count, "includePromotedContent": False})

    def similar(self, tweet_id):
        """Similar posts (snake_case var!). Proven: test_similar_posts.py"""
        return self._s.gql_get("SimilarPosts", {"tweet_id": str(tweet_id)})

    def views(self, tweet_id):
        """Impressions/views count (int) or None if unavailable.
        Lives at result.views.count (sibling of legacy, NOT inside it).
        Proven live by xapiweb 2026-09-20."""
        r = self.get(tweet_id)
        v = r.get("data", "tweetResult", "result", "views", default=None) or {}
        try:
            return int(v.get("count"))
        except (TypeError, ValueError):
            return None

    def stats(self, tweet_id):
        """All public counts in ONE call: views/likes/retweets/replies/quotes/bookmarks.
        Proven live by xapiweb 2026-09-20."""
        r = self.get(tweet_id)
        res = r.get("data", "tweetResult", "result", default={}) or {}
        leg = res.get("legacy", {}) or {}
        views = None
        try:
            views = int((res.get("views") or {}).get("count"))
        except (TypeError, ValueError):
            pass
        return {"views": views,
                "likes": leg.get("favorite_count"),
                "retweets": leg.get("retweet_count"),
                "replies": leg.get("reply_count"),
                "quotes": leg.get("quote_count"),
                "bookmarks": leg.get("bookmark_count")}

    def media(self, tweet_id):
        """Attached media: [{type, url, thumb, width, height, duration_ms, bitrate, ...}].

        type: photo | video | animated_gif. url = direct image url, or best mp4
        (max bitrate) for video/gif. Empty list when no media.
        Proven live by xapiweb 2026-09-20."""
        r = self.get(tweet_id)
        leg = r.get("data", "tweetResult", "result", "legacy", default={}) or {}
        return parse_media_entities(leg)

    def drafts(self):
        """Draft tweets. Proven: test_draft_tweets.py"""
        return self._s.gql_get("FetchDraftTweets", {"ascending": False},
                               with_features=False, with_toggles=False)

    def scheduled(self):
        """Scheduled tweets (read). Proven: test_scheduled_tweets.py"""
        return self._s.gql_get("FetchScheduledTweets", {"ascending": True},
                               with_features=False, with_toggles=False)

    # ---------------- write ----------------
    def post(self, text, reply_to=None, media_ids=None, possibly_sensitive=False, verify=True):
        """Post a tweet; optionally as a reply and/or with uploaded media.

        reply_to: tweet id this is a reply to (proven live by xapiweb).
        media_ids: list from media.upload_image() (proven live by xapiweb self-test).
        Returns Response; new id at .get("data","create_tweet","tweet_results","result","rest_id").
        No rest_id => NOT posted (bad txn) => raises XTxnError.
        Proven: test_post_and_delete_tweet.py (+ xapiweb reply/media proofs).
        """
        media = {"media_entities": [], "possibly_sensitive": bool(possibly_sensitive)}
        if media_ids:
            media["media_entities"] = [{"media_id": str(m), "tagged_users": []} for m in media_ids]
        variables = {"tweet_text": text, "media": media,
                     "semantic_annotation_ids": [], "disallowed_reply_options": None}
        if reply_to:
            variables["reply"] = {"in_reply_to_tweet_id": str(reply_to), "exclude_reply_user_ids": []}
        resp = self._s.gql_post("CreateTweet", variables, with_features=True)
        E.guard(resp, "CreateTweet")
        nid = resp.get("data", "create_tweet", "tweet_results", "result", "rest_id")
        if not nid:
            raise E.XTxnError("CreateTweet 200 with empty tweet_results: bad/missing txn-id; NOT posted.")
        resp.tweet_id = nid
        if verify and reply_to:
            back = self.get(nid)
            got = back.get("data", "tweetResult", "result", "legacy", "in_reply_to_status_id_str")
            if got != str(reply_to):
                self.delete(nid, verify=False)
                raise E.XVerifyError(f"Reply posted standalone (in_reply_to={got}); stray tweet deleted.")
        return resp

    def create_poll_card(self, choices, duration_minutes=1440):
        """Create a poll card (caps API). choices: 2-4 labels (1-25 chars each).
        duration_minutes: 5..10080. Returns card_uri like 'card://...'.
        Proven live by xapiweb 2026-09-20 (2- and 4-choice, full post cycle)."""
        import json as _json
        import urllib.parse as _up
        labels = list(choices)
        if not (2 <= len(labels) <= 4):
            raise ValueError("polls need 2-4 choices")
        for c in labels:
            if not c or len(c) > 25:
                raise ValueError("poll choice labels must be 1-25 chars")
        if not (5 <= int(duration_minutes) <= 10080):
            raise ValueError("duration_minutes must be 5..10080")
        n = len(labels)
        card = {"twitter:card": f"poll{n}choice_text_only",
                f"twitter:api:poll{n}choice_text_only": True,
                "twitter:api:api:endpoint": "1",
                "twitter:long:duration_minutes": str(int(duration_minutes))}
        for i, c in enumerate(labels, 1):
            card[f"twitter:string:choice{i}_label"] = c
        r = self._s.call("POST", "https://caps.twitter.com/v2/cards/create",
                         _up.urlencode({"card_data": _json.dumps(card)}),
                         "application/x-www-form-urlencoded; charset=UTF-8")
        uri = r.get("card_uri")
        if r.status != 200 or not uri:
            raise E.XError(f"Poll card create failed: {r.status} {r.raw[:200]}")
        return uri

    def post_poll(self, text, choices, duration_minutes=1440, verify=True):
        """Post a tweet with an attached poll. Returns Response (id at .tweet_id,
        card at .poll_card). Cards are single-use. Proven live by xapiweb 2026-09-20."""
        uri = self.create_poll_card(choices, duration_minutes)
        resp = self._s.gql_post("CreateTweet", {
            "tweet_text": text, "card_uri": uri,
            "media": {"media_entities": [], "possibly_sensitive": False},
            "semantic_annotation_ids": [], "disallowed_reply_options": None},
            with_features=True)
        E.guard(resp, "CreateTweet")
        nid = resp.get("data", "create_tweet", "tweet_results", "result", "rest_id")
        if not nid:
            raise E.XTxnError("CreateTweet 200 with empty tweet_results: bad txn; NOT posted.")
        resp.tweet_id = nid
        resp.poll_card = uri
        if verify and "choice1_label" not in self.get(nid).raw:
            raise E.XVerifyError(f"Poll card missing on re-read of {nid}.")
        return resp

    def post_thread(self, texts, verify=True):
        """Post a thread (first tweet + chained replies). Returns [ids], in order.
        On mid-thread failure, already-posted ids are attached as err.posted_ids
        (delete them yourself). Proven live by xapiweb 2026-09-20."""
        texts = list(texts)
        if not texts:
            raise ValueError("post_thread needs >= 1 text")
        ids = []
        try:
            reply_to = None
            for t in texts:
                r = self.post(t, reply_to=reply_to, verify=verify)
                reply_to = r.tweet_id
                ids.append(reply_to)
        except E.XError as e:
            e.posted_ids = ids
            raise
        return ids

    def delete(self, tweet_id, verify=True):
        """Delete own tweet. Proven: test_post_and_delete_tweet.py"""
        resp = self._s.gql_post("DeleteTweet", {"tweet_id": str(tweet_id)})
        E.guard(resp, "DeleteTweet")
        if verify:
            back = self.get(tweet_id)
            if '"tweetResult":{}' not in back.raw.replace(" ", ""):
                raise E.XVerifyError(f"Tweet {tweet_id} still readable after delete.")
        return resp

    def pin(self, tweet_id):
        """Pin own tweet. Proven: test_pin_cycle.py"""
        resp = self._s.gql_post("PinTweet", {"tweet_id": str(tweet_id)})
        return E.guard(resp, "PinTweet")

    def unpin(self, tweet_id):
        """Unpin own tweet. Proven: test_pin_cycle.py"""
        resp = self._s.gql_post("UnpinTweet", {"tweet_id": str(tweet_id)})
        return E.guard(resp, "UnpinTweet")

    def set_reply_control(self, tweet_id, mode, allowed_country_codes=None, verify=True):
        """Limit who can reply. Modes: ByInvitation|Verified|Subscribers|Community|
        MyNetwork(gated)|CountryOfOrigin(+codes). Proven: test_conversation_control_pair.py"""
        if mode not in REPLY_MODES:
            raise ValueError(f"mode must be one of {REPLY_MODES}")
        variables = {"tweet_id": str(tweet_id), "mode": mode}
        if allowed_country_codes:
            variables["allowed_country_codes"] = list(allowed_country_codes)
        resp = self._s.gql_post("ConversationControlChange", variables)
        E.guard(resp, "ConversationControlChange")
        if verify:
            back = self.get(tweet_id)
            if f'"mode":"{mode}"' not in back.raw.replace(" ", ""):
                raise E.XVerifyError(f"Reply-control marker {mode} not found on re-read.")
        return resp

    def remove_reply_control(self, tweet_id):
        """Revert reply limits (idempotent 'Done'). Proven: test_conversation_control_pair.py"""
        resp = self._s.gql_post("ConversationControlDelete", {"tweet_id": str(tweet_id)})
        return E.guard(resp, "ConversationControlDelete")

    def add_ad_disclosure(self, tweet_id, verify=True):
        """Paid-promotion label. Proven: test_content_disclosure_pair.py"""
        resp = self._s.gql_post("AddContentDisclosure", {
            "tweet_id": str(tweet_id), "advertising_disclosure": {"is_paid_promotion": True}})
        E.guard(resp, "AddContentDisclosure")
        if verify:
            self._assert_disclosure(tweet_id, True)
        return resp

    def add_ai_disclosure(self, tweet_id, verify=True):
        """AI-generated-media label. Proven: test_content_disclosure_pair.py"""
        resp = self._s.gql_post("AddContentDisclosure", {
            "tweet_id": str(tweet_id),
            "ai_generated_disclosure": {"has_ai_generated_media": True}})
        E.guard(resp, "AddContentDisclosure")
        if verify:
            self._assert_disclosure(tweet_id, True)
        return resp

    def remove_disclosure(self, tweet_id, verify=True):
        """Remove disclosure label. Proven: test_content_disclosure_pair.py"""
        resp = self._s.gql_post("DeleteContentDisclosure", {"tweet_id": str(tweet_id)})
        E.guard(resp, "DeleteContentDisclosure")
        if verify:
            import time
            self._assert_disclosure(tweet_id, False)
        return resp

    def _assert_disclosure(self, tweet_id, present):
        import time
        d = self.detail(tweet_id)
        has = "disclosure" in d.raw.lower()
        if present and not has:
            raise E.XVerifyError("Disclosure marker missing on re-read.")
        if not present and has:
            time.sleep(3)
            d = self.detail(tweet_id)
            if "disclosure" in d.raw.lower():
                raise E.XVerifyError("Disclosure marker still present after remove.")

    # ---------------- gated (documented, not usable on this account type) ----------------
    def create_note(self, text):
        """Long-form note. GATED: needs Premium (code 37 without). Proven: test_note_tweet_guard.py"""
        return self._s.gql_post("CreateNoteTweet", {"tweet_text": text})

    def create_highlight(self, tweet_id):
        """GATED: needs unknown eligibility. Proven: test_create_highlight_shape.py"""
        return self._s.gql_post("CreateHighlight", {"tweet_id": str(tweet_id)})

    def delete_highlight(self, tweet_id):
        """GATED: mirrors create. Proven: test_delete_highlight_shape.py"""
        return self._s.gql_post("DeleteHighlight", {"tweet_id": str(tweet_id)})
