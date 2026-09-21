"""Users: profiles, batches, recommendations, credentials."""
from ._base import BaseResource


class Users(BaseResource):
    def by_screen_name(self, screen_name, grok_bio=True):
        """Proven: test_user_by_screen_name.py"""
        return self._s.gql_get("UserByScreenName",
                               {"screen_name": screen_name, "withGrokTranslatedBio": grok_bio})

    def by_id(self, user_id, grok_bio=True):
        """Proven: test_user_by_rest_id.py"""
        return self._s.gql_get("UserByRestId",
                               {"userId": str(user_id), "withGrokTranslatedBio": grok_bio})

    def batch_by_ids(self, user_ids):
        """POST-only (GET 404s). Proven: test_users_by_rest_ids.py"""
        return self._s.gql_post("UsersByRestIds", {"userIds": [str(i) for i in user_ids]})

    def batch_by_names(self, screen_names):
        """snake_case var! Proven: test_users_by_screen_names.py"""
        return self._s.gql_get("UsersByScreenNames", {"screen_names": list(screen_names)})

    def viewer(self):
        """Viewer/me object. Proven: test_viewer.py"""
        return self._s.gql_get("Viewer", {})

    def username_availability(self, username, suggestions=True):
        """Proven: test_username_availability.py"""
        return self._s.gql_post("GetUsernameAvailabilityAndSuggestions", {
            "username": username, "include_suggestions": suggestions, "session_token": ""})

    def show(self, user_id):
        """REST, txn-gated (404 without). Proven: test_user_show.py"""
        return self._s.rest_get("users/show.json", {"user_id": str(user_id), "skip_status": 1})

    def lookup(self, user_ids):
        """REST batch, txn-gated. Proven: test_users_lookup.py"""
        if isinstance(user_ids, (list, tuple)):
            user_ids = ",".join(str(i) for i in user_ids)
        return self._s.rest_get("users/lookup.json", {"user_id": user_ids})

    def verify_credentials(self):
        """REST, txn-gated. Proven: test_verify_credentials.py"""
        return self._s.rest_get("account/verify_credentials.json", {"skip_status": 1})

    def recommendations(self, limit=3, user_id=None):
        """Proven: test_user_recommendations.py"""
        return self._s.rest_get("users/recommendations.json", {
            "limit": limit, "user_id": str(user_id or self._me()),
            "display_location": "profile-cluster-follow", "skip_status": 1})

    def verified_avatars(self, user_ids):
        """Proven: test_users_verified_avatars.py"""
        return self._s.gql_get("UsersVerifiedAvatars",
                               {"userIds": [str(i) for i in user_ids]}, with_toggles=False)

    def spotlights(self, screen_name):
        """Proven: test_profile_spotlights.py"""
        return self._s.gql_get("ProfileSpotlightsQuery", {"screen_name": screen_name},
                               with_features=False, with_toggles=False)

    def claims(self):
        """Proven: test_user_claims.py"""
        return self._s.gql_get("GetUserClaims", {})

    def preferences(self):
        """Proven: test_user_preferences.py"""
        return self._s.gql_get("UserPreferences", {})

    def sessions(self):
        """Active sessions list. Proven: test_user_sessions.py"""
        return self._s.gql_get("UserSessionsList", {})

    def upsells(self):
        """Proven: test_upsells.py"""
        return self._s.gql_get("Upsells", {})

    def me(self):
        """Cached {id, screen_name, ...} of the session owner (via verify_credentials)."""
        if self._client._me_cache is None:
            r = self.verify_credentials()
            self._client._me_cache = {"id": r.get("id_str"), "screen_name": r.get("screen_name"),
                                      "name": r.get("name"), "raw": r}
        return self._client._me_cache
