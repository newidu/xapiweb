"""Notifications: full list + badge-count polling + realtime SSE."""
import http.client
import re

from ._base import BaseResource


def extract_notifications(resp_or_data, limit=50):
    """Pull [{id, type, icon, text, users, time, url, tweet_id}] out of a
    NotificationsTimeline response. type = element like 'users_liked_your_tweet',
    'users_followed_you', 'mention'. users = [{screen_name, name, id}].
    Page with xapiweb.resources.timelines.cursors(resp)['bottom']. xapiweb helper."""
    data = resp_or_data.data if hasattr(resp_or_data, "data") else resp_or_data
    out = []

    def walk(o):
        if len(out) >= limit:
            return
        if isinstance(o, dict):
            it = o.get("itemContent")
            if isinstance(it, dict) and it.get("__typename") == "TimelineNotification":
                rm = it.get("rich_message") or {}
                users = []
                for ent in rm.get("entities") or []:
                    ur = (((ent.get("ref") or {}).get("user_results") or {}).get("result") or {})
                    core = ur.get("core") or {}
                    leg = ur.get("legacy") or {}
                    sn = core.get("screen_name") or leg.get("screen_name")
                    if sn:
                        users.append({"screen_name": sn,
                                      "name": core.get("name") or leg.get("name"),
                                      "id": core.get("rest_id") or ur.get("rest_id")})
                url = (it.get("notification_url") or {}).get("url") or ""
                m = re.search(r"/status/(\d+)", url)
                out.append({"id": it.get("id"),
                            "type": (o.get("clientEventInfo") or {}).get("element"),
                            "icon": it.get("notification_icon"),
                            "text": rm.get("text") or "",
                            "users": users,
                            "time": it.get("timestamp_ms"),
                            "url": url,
                            "tweet_id": m.group(1) if m else None})
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    return out


class Notifications(BaseResource):
    def list(self, timeline_type="All", count=20, cursor=None):
        """Full notifications list. timeline_type: 'All'|'Verified'|'Mentions'
        (all 200-proven). Parse with extract_notifications(resp); page with
        timelines.cursors(resp)['bottom'] -> cursor=. Proven live 2026-09-20
        (user-captured qid)."""
        v = {"timeline_type": timeline_type, "count": count}
        if cursor:
            v["cursor"] = cursor
        return self._s.gql_get("NotificationsTimeline", v, with_toggles=False)

    def badge_counts(self):
        """{dm_unread_count, ntab_unread_count, total_unread_count, ...} — the polling
        endpoint. Proven: test_viewer_badge_counts.py"""
        return self._s.gql_get("ViewerBadgeCounts", {},
                               with_features=False, with_toggles=False)

    def live_events(self, seconds=6, topic=None):
        """Hold the SSE stream ~`seconds` and return {'status':, 'sample':}.
        Full notifications timeline (AuthTimeline) is UNTESTED. Proven: test_live_pipeline.py"""
        topic = topic or f"/live_content/{self._me()}"
        conn = http.client.HTTPSConnection("api.x.com", timeout=seconds + 6)
        conn.request("GET", f"/live_pipeline/events?topic={topic}",
                     headers=self._s.headers("GET", "/live_pipeline/events"))
        resp = conn.getresponse()
        try:
            conn.sock.settimeout(seconds)
            sample = resp.read(300).decode("utf-8", "replace")
        except Exception:
            sample = "(connected, quiet window)"
        conn.close()
        return {"status": resp.status, "topic": topic, "sample": sample[:300]}
