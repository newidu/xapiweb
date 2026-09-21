"""Follows & friendships (REST)."""
from .. import errors as E
from ._base import BaseResource

_FULL = {"include_profile_interstitial_type": 1, "include_blocking": 1,
         "include_blocked_by": 1, "include_followed_by": 1,
         "include_want_retweets": 1, "skip_status": 1}


class Follows(BaseResource):
    def follow(self, user_id, verify=True):
        """Follow + verify via lookup. Proven: test_follow_pair.py"""
        resp = self._s.rest_post_form("friendships/create.json", {**_FULL, "user_id": str(user_id)})
        if verify:
            conns = self.lookup(user_id).get(0, "connections", default=[])
            if "following" not in (conns or []):
                raise E.XVerifyError(f"Follow of {user_id} not confirmed in lookup.")
        return resp

    def unfollow(self, user_id, verify=True):
        """Unfollow + verify lookup == ['none']. Proven: test_follow_pair.py"""
        resp = self._s.rest_post_form("friendships/destroy.json", {**_FULL, "user_id": str(user_id)})
        if verify:
            conns = self.lookup(user_id).get(0, "connections", default=None)
            if conns != ["none"]:
                raise E.XVerifyError(f"Unfollow of {user_id} not confirmed: {conns}.")
        return resp

    def lookup(self, user_ids):
        """connections:[...] per user. Proven: test_friendship_lookup.py"""
        if isinstance(user_ids, (list, tuple)):
            user_ids = ",".join(str(i) for i in user_ids)
        return self._s.rest_get("friendships/lookup.json", {"user_id": str(user_ids)})

    def show(self, source_id=None, target_id=None):
        """Pair relationship. Proven: test_friendship_show.py"""
        return self._s.rest_get("friendships/show.json", {
            "source_id": str(source_id or self._me()), "target_id": str(target_id)})

    def friends_ids(self, user_id=None):
        """Following ids. Proven: test_friends_ids.py"""
        return self._s.rest_get("friends/ids.json",
                                {"user_id": str(user_id or self._me()), "cursor": -1, "count": 5000})

    def followers_ids(self, user_id=None):
        """Proven: test_followers_ids.py"""
        return self._s.rest_get("followers/ids.json",
                                {"user_id": str(user_id or self._me()), "cursor": -1, "count": 5000})

    def friends_list(self, user_id=None):
        """Following full objects (THE real list). Proven: test_friends_list.py"""
        return self._s.rest_get("friends/list.json",
                                {"user_id": str(user_id or self._me()), "cursor": -1,
                                 "count": 200, "skip_status": 1})

    def followers_list(self, user_id=None):
        """Proven: test_followers_list.py"""
        return self._s.rest_get("followers/list.json",
                                {"user_id": str(user_id or self._me()), "cursor": -1,
                                 "count": 200, "skip_status": 1})

    def following_preview(self, user_id=None):
        """LIMITED preview list (not complete!). Proven: test_following_preview_list.py"""
        return self._s.rest_get("friends/following/list.json",
                                {"user_id": str(user_id or self._me()), "cursor": -1,
                                 "count": 200, "skip_status": 1, "with_total_count": "true"})

    def friendships_list(self, user_id=None):
        """Proven: test_friendships_list.py"""
        return self._s.rest_get("friendships/list.json",
                                {"user_id": str(user_id or self._me()), "cursor": -1})

    def incoming(self):
        """Incoming follow requests. Proven: test_friendships_incoming.py"""
        return self._s.rest_get("friendships/incoming.json", {"cursor": -1, "skip_status": 1})

    def outgoing(self):
        """Outgoing follow requests. Proven: test_friendships_outgoing.py"""
        return self._s.rest_get("friendships/outgoing.json", {"cursor": -1})

    def no_retweets_ids(self):
        """Proven: test_no_retweets_ids.py"""
        return self._s.rest_get("friendships/no_retweets/ids.json", {})

    def set_retweets(self, user_id, enabled, verify=True):
        """Mute/unmute someone's retweets (mutual). Proven: test_friendship_update_pair.py"""
        resp = self._s.rest_post_form("friendships/update.json",
                                      {"user_id": str(user_id),
                                       "retweets": "true" if enabled else "false"})
        if verify:
            want = self.show(self._me(), user_id).get("relationship", "source", "want_retweets")
            if want is not bool(enabled):
                raise E.XVerifyError(f"want_retweets={want}, expected {bool(enabled)}.")
        return resp

    def remove_follower(self, target_user_id, confirm=False):
        """Remove a follower. NEVER auto-fire: pass confirm=True explicitly.
        Shape: bogus id => UnfollowInvalidRequestResult. Proven: test_remove_follower_shape.py"""
        if not confirm:
            raise E.XError("remove_follower() needs confirm=True (irreversible-ish, unsafe to auto-fire).")
        return self._s.gql_post("RemoveFollower", {"target_user_id": str(target_user_id)})

    def accept(self, user_id):
        """Accept a pending follow request. Routing proven live (409 code 49
        'No follow request pending' when nothing pending); a REAL accept needs
        an actual pending request to fully prove."""
        return self._s.rest_post_form("friendships/accept.json", {"user_id": str(user_id)})

    def deny(self, user_id):
        """Deny a pending follow request. Routing proven live (409/49)."""
        return self._s.rest_post_form("friendships/deny.json", {"user_id": str(user_id)})

    def cancel(self, user_id):
        """Cancel an outgoing follow request. Routing proven live (409/49)."""
        return self._s.rest_post_form("friendships/cancel.json", {"user_id": str(user_id)})
