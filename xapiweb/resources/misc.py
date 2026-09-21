"""Misc: mixers, beacons, probes, and one-off queries."""
import json
import urllib.error
from ._base import BaseResource


class Misc(BaseResource):
    def authenticate_periscope(self):
        """JWT for live/periscope calls. Proven: test_authenticate_periscope.py"""
        return self._s.gql_get("AuthenticatePeriscope", {}, with_features=False, with_toggles=False)

    def urt_fixtures(self):
        """Proven: test_urt_fixtures.py"""
        return self._s.gql_get("UrtFixtures", {}, with_features=False, with_toggles=False)

    def bakery(self):
        """Cookie catalog. Proven: test_bakery_cookies.py"""
        return self._s.gql_get("BakeryQuery", {})

    def supported_languages(self):
        """Proven: test_supported_languages.py"""
        return self._s.gql_get("SupportedLanguages", {})

    def story_topic(self, rest_id="For You", limit=3):
        """Proven: test_story_topic.py"""
        return self._s.gql_get("useStoryTopicQuery", {"rest_id": rest_id, "limit": limit},
                               with_features=False, with_toggles=False)

    def nfl_follow(self):
        """Proven: test_nfl_follow.py"""
        return self._s.gql_get("NflScoresSidebarFollow", {}, with_features=False, with_toggles=False)

    def tv_home_mixer(self):
        """Proven: test_tv_home_mixer.py"""
        return self._s.gql_get("TVHomeMixer", {})

    def payments_typeahead(self, prefix="e"):
        """Proven: test_payments_typeahead.py"""
        return self._s.gql_get("PaymentsUsersTypeahead", {"prefix": prefix})

    def media_tab_videos(self, user_id=None):
        """Proven: test_media_tab_videos.py"""
        return self._s.gql_get("MediaTabVideoMixer", {"userId": str(user_id or self._me())})

    def fleetline(self):
        """Proven: test_fleetline.py"""
        return self._s.rest_get("fleets/v1/fleetline", {"only_spaces": "true"},
                                host="https://x.com", prefix="/i/api/")

    def avatar_content(self, user_id=None):
        """Proven: test_avatar_content.py"""
        return self._s.rest_get("fleets/v1/avatar_content",
                                {"user_ids": str(user_id or self._me()), "only_spaces": "true"},
                                host="https://x.com", prefix="/i/api/")

    def biz_team_timeline(self, team_name="x", user_id=None):
        """Bogus team => empty timeline. Proven: test_biz_team_timeline.py"""
        return self._s.gql_post("UserBusinessProfileTeamTimeline", {
            "userId": str(user_id or self._me()), "teamName": team_name,
            "includePromotedContent": False})

    def sidebar_recommendations(self, user_id=None):
        """Proven: test_sidebar_recommendations.py"""
        return self._s.gql_get("SidebarUserRecommendations",
                               {"profileUserId": str(user_id or self._me())}, with_toggles=False)

    def super_followers(self, user_id=None, count=5):
        """Proven: test_super_followers.py"""
        return self._s.gql_get("SuperFollowers", {
            "userId": str(user_id or self._me()), "count": count, "includePromotedContent": False})

    def premium_paywall(self):
        """Proven: test_premium_paywall.py"""
        return self._s.gql_post("usePremiumPaywallOnLoadMutation", {})

    def season_schedule(self, user_id=None, days_back=7, days_fwd=14):
        """Proven: test_profile_season_schedule.py"""
        import time
        now = int(time.time() * 1000)
        return self._s.gql_get("ProfileSeasonSchedule", {
            "rest_id": str(user_id or self._me()),
            "start_time": str(now - days_back * 86400 * 1000),
            "end_time": str(now + days_fwd * 86400 * 1000)},
            with_features=False, with_toggles=False)

    def team_roster(self, user_id=None):
        """Proven: test_profile_team_roster.py"""
        return self._s.gql_get("ProfileTeamRoster", {"rest_id": str(user_id or self._me())},
                               with_features=False, with_toggles=False)

    def vo_upsell(self, screen_name):
        """Proven: test_vo_upsell_eligibility.py"""
        return self._s.gql_get("isEligibleForVoButtonUpsellQuery",
                               {"screenName": screen_name,
                                "promptPurpose": "x_vo_business_promotion"},
                               with_features=False, with_toggles=False)

    def csp_report(self):
        """CSP beacon sink. Proven: test_csp_report.py"""
        payload = json.dumps({"csp-report": {
            "document-uri": "https://x.com/home", "blocked-uri": "https://example.com/x.js",
            "violated-directive": "script-src", "original-policy": "test",
            "disposition": "enforce"}})
        return self._s.call("POST", "https://x.com/i/csp_report?a=1&ro=0", payload)

    def log_promoted_view(self, trend_id="117896", impression_id="6752072595616677896",
                          event="trend_view"):
        """Promoted-trend impression beacon.

        NOTE: this is for PROMOTED (ad) content, NOT organic tweet views — it takes a
        trend id, not a tweet id, so it cannot register a view for a post. There is no
        proven endpoint for organic view-logging in the pack. Proven: test_promoted_log.py"""
        return self._s.rest_post_form("promoted_content/log.json", {
            "promoted_trend_id": str(trend_id), "event": event,
            "impression_id": str(impression_id)})

    def promoted_log(self, trend_id="117896", impression_id="6752072595616677896"):
        """Alias of log_promoted_view() with default test params. Proven: test_promoted_log.py"""
        return self.log_promoted_view(trend_id, impression_id)

    def manifest_sw(self):
        """Returns (manifest_resp, sw_resp). Proven: test_manifest_sw.py"""
        return (self._s.call("GET", "https://x.com/manifest.json"),
                self._s.call("GET", "https://x.com/sw.js"))

    def feedback_shape(self):
        """Bogus-token shape only (real fire = irreversible algo signal).
        Proven: test_timelines_feedback_shape.py"""
        return self._s.gql_post("timelinesFeedback",
                                {"encoded_feedback_request": "x", "undo": False})

    def unmention_shape(self, tweet_id):
        """Proven: test_unmention_shape.py (clean error when not mentioned)."""
        return self._s.gql_post("UnmentionUserFromConversation", {"tweet_id": str(tweet_id)})

    def probe_removed(self):
        """Re-verify legacy endpoints are still gone (expect 404/410, enrollment 403).
        Proven: test_removed_endpoints.py"""
        paths = ["statuses/show.json?id=1", "statuses/lookup.json?id=1", "favorites/list.json",
                 "search/adaptive.json?q=x", "guide/topic.json?slug=news", "topics/discover.json",
                 "collections/list.json", "people_discovery/modules_urt.json",
                 "settings/trends.json", "settings/devices.json", "notifications/all.json",
                 "account/login_verification_enrollment.json", "graphql/viewer_context.json"]
        got = {}
        for p in paths:
            try:
                got[p] = self._s.rest_get(p).status
            except urllib.error.HTTPError as e:
                got[p] = e.code
            except Exception as e:
                got[p] = getattr(e, "status", f"ERR {e}"[:40])
        return got

    def probe_deprecated(self):
        """Re-verify deprecated endpoints still 200-empty. Proven: test_deprecated_empty.py"""
        out = {}
        r1 = self._s.rest_get("users/search.json", {"q": "elon"})
        out["users/search"] = (r1.status, len(r1.raw))
        r2 = self._s.rest_get("statuses/home_timeline.json", {"count": 3})
        out["statuses/home_timeline"] = (r2.status, len(r2.raw))
        r3 = self._s.rest_get("statuses/user_timeline.json",
                              {"user_id": self._me(), "count": 3})
        out["statuses/user_timeline"] = (r3.status, len(r3.raw))
        return out
