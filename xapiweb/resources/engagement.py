"""Engagement: like, retweet, bookmark, downvote (all verify by re-read)."""
from .. import errors as E
from ._base import BaseResource


class Engagement(BaseResource):
    def _flag(self, tweet_id, key):
        r = self._client.tweets.get(tweet_id)
        return r.get("data", "tweetResult", "result", "legacy", key)

    # ---- like ----
    def like(self, tweet_id, verify=True):
        """Proven: test_like_pair.py"""
        resp = self._s.gql_post("FavoriteTweet", {"tweet_id": str(tweet_id)})
        E.guard(resp, "FavoriteTweet")
        if verify and self._flag(tweet_id, "favorited") is not True:
            raise E.XVerifyError(f"Tweet {tweet_id} not favorited on re-read.")
        return resp

    def unlike(self, tweet_id, verify=True):
        """Proven: test_like_pair.py"""
        resp = self._s.gql_post("UnfavoriteTweet", {"tweet_id": str(tweet_id)})
        E.guard(resp, "UnfavoriteTweet")
        if verify and self._flag(tweet_id, "favorited") is not False:
            raise E.XVerifyError(f"Tweet {tweet_id} still favorited on re-read.")
        return resp

    # ---- retweet ----
    def retweet(self, tweet_id, verify=True):
        """Returns Response; wrapper id at .get("data","create_retweet","retweet_results","result","rest_id").
        Already-retweeted => XAlreadyError (327). Proven: test_retweet_pair.py"""
        resp = self._s.gql_post("CreateRetweet", {"tweet_id": str(tweet_id)})
        E.guard(resp, "CreateRetweet")
        if verify and self._flag(tweet_id, "retweeted") is not True:
            raise E.XVerifyError(f"Tweet {tweet_id} not retweeted on re-read.")
        return resp

    def unretweet(self, original_tweet_id, verify=True):
        """Pass the ORIGINAL id, never the wrapper (wrapper delete is a silent phantom).
        Proven: test_retweet_pair.py"""
        resp = self._s.gql_post("DeleteRetweet", {"source_tweet_id": str(original_tweet_id)})
        E.guard(resp, "DeleteRetweet")
        if verify and self._flag(original_tweet_id, "retweeted") is not False:
            raise E.XVerifyError(f"Tweet {original_tweet_id} still retweeted (phantom?).")
        return resp

    # ---- bookmark ----
    def bookmark_add(self, tweet_id, verify=True):
        """CreateBookmark NEEDS txn (404 without). Proven: test_bookmark_pair.py"""
        resp = self._s.gql_post("CreateBookmark", {"tweet_id": str(tweet_id)})
        E.guard(resp, "CreateBookmark")
        if verify and self._flag(tweet_id, "bookmarked") is not True:
            raise E.XVerifyError(f"Tweet {tweet_id} not bookmarked on re-read.")
        return resp

    def bookmark_remove(self, tweet_id, verify=True):
        """Proven: test_bookmark_pair.py"""
        resp = self._s.gql_post("DeleteBookmark", {"tweet_id": str(tweet_id)})
        E.guard(resp, "DeleteBookmark")
        if verify and self._flag(tweet_id, "bookmarked") is not False:
            raise E.XVerifyError(f"Tweet {tweet_id} still bookmarked on re-read.")
        return resp

    def bookmark_search(self, query, count=5):
        """Proven: test_bookmark_search.py"""
        return self._s.gql_get("BookmarkSearchTimeline", {"rawQuery": query, "count": count})

    # ---- downvote ----
    def downvote(self, tweet_id, verify=True):
        """Proven: test_downvote_pair.py"""
        resp = self._s.gql_post("DownvoteTweet", {"tweet_id": str(tweet_id)})
        E.guard(resp, "DownvoteTweet")
        if verify and '"is_downvoted":true' not in resp.raw.replace(" ", ""):
            raise E.XVerifyError("Downvote ack missing is_downvoted:true.")
        return resp

    def undo_downvote(self, tweet_id, verify=True):
        """Proven: test_downvote_pair.py"""
        resp = self._s.gql_post("UndoDownvoteTweet", {"tweet_id": str(tweet_id)})
        E.guard(resp, "UndoDownvoteTweet")
        if verify and '"is_downvoted":false' not in resp.raw.replace(" ", ""):
            raise E.XVerifyError("Undo-downvote ack missing is_downvoted:false.")
        return resp
