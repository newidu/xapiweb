"""Lists (REST) + profile timeline pins (GraphQL)."""
from .. import errors as E
from ._base import BaseResource


class Lists(BaseResource):
    def create(self, name, mode="private", description=""):
        """Returns Response; id at .get("id_str"). Proven: test_list_cycle.py"""
        return self._s.rest_post_form("lists/create.json",
                                      {"name": name, "mode": mode, "description": description})

    def destroy(self, list_id):
        """Proven: test_list_cycle.py"""
        return self._s.rest_post_form("lists/destroy.json", {"list_id": str(list_id)})

    def add_member(self, list_id, user_id):
        """Proven: test_list_cycle.py"""
        return self._s.rest_post_form("lists/members/create.json",
                                      {"list_id": str(list_id), "user_id": str(user_id)})

    def remove_member(self, list_id, user_id):
        """Proven: test_list_cycle.py"""
        return self._s.rest_post_form("lists/members/destroy.json",
                                      {"list_id": str(list_id), "user_id": str(user_id)})

    def mine(self, user_id=None):
        """Own lists (verify [] when clean). Proven: test_lists_mine.py"""
        return self._s.rest_get("lists/list.json", {"user_id": str(user_id or self._me())})

    def ownerships(self, user_id=None, count=5):
        """Proven: test_lists_ownerships.py"""
        return self._s.rest_get("lists/ownerships.json",
                                {"user_id": str(user_id or self._me()), "count": count})

    def memberships(self, user_id=None, count=5):
        """Proven: test_lists_memberships.py"""
        return self._s.rest_get("lists/memberships.json",
                                {"user_id": str(user_id or self._me()), "count": count})

    def subscriptions(self, user_id=None):
        """Proven: test_lists_subscriptions.py"""
        return self._s.rest_get("lists/subscriptions.json",
                                {"user_id": str(user_id or self._me())})

    def search(self, list_id, raw_query, count=5):
        """Proven: test_list_search.py"""
        return self._s.gql_get("ListSearchTimeline",
                               {"listId": str(list_id), "rawQuery": raw_query, "count": count})

    # NOTE: lists/members.json READ 404s with every variant — add/remove work, reading does not.

    # ---- profile pins ----
    def pin(self, item_id, item_type="List", verify=True):
        """Pin a List/Community to the profile (Tag pins are silently ignored).
        Proven: test_pin_timeline_pair.py"""
        item = {"id": str(item_id), "pinned_timeline_type": item_type}
        resp = self._s.gql_post("PinTimeline", {"pinnedTimelineItem": item})
        E.guard(resp, "PinTimeline")
        if verify and "PinTimelineSuccessResult" not in resp.raw:
            raise E.XVerifyError("Pin ack missing PinTimelineSuccessResult.")
        return resp

    def unpin(self, item_id, item_type="List", verify=True):
        """Proven: test_pin_timeline_pair.py"""
        item = {"id": str(item_id), "pinned_timeline_type": item_type}
        resp = self._s.gql_post("UnpinTimeline", {"pinnedTimelineItem": item})
        E.guard(resp, "UnpinTimeline")
        if verify and "UnpinTimelineSuccessResult" not in resp.raw:
            raise E.XVerifyError("Unpin ack missing UnpinTimelineSuccessResult.")
        return resp

    def update_pins(self, items):
        """Echo current list = safe no-op. Proven: test_pin_timeline_pair.py"""
        resp = self._s.gql_post("UpdatePinnedTimelines", {"pinnedTimelineItems": items})
        return E.guard(resp, "UpdatePinnedTimelines")
