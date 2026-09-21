"""Settings & preferences (reads + safe writes; blind writes need confirm=True)."""
from .. import errors as E
from ._base import BaseResource


class Settings(BaseResource):
    def account(self):
        """Txn-gated, alt host. Proven: test_account_settings.py"""
        return self._s.rest_get("account/settings.json", {"include_mention_filter": "true"},
                                host="https://api.x.com", prefix="/1.1/")

    def help_config(self):
        """Proven: test_help_settings.py"""
        return self._s.rest_get("help/settings.json", {})

    def email_phone_info(self):
        """PRIVATE account emails/phones — handle with care. Proven: test_email_phone_info.py"""
        return self._s.rest_get("users/email_phone_info.json", {})

    def saved_searches(self):
        """Txn-gated, alive. Proven: test_saved_searches.py"""
        return self._s.rest_get("saved_searches/list.json", {})

    def alt_text_get(self):
        """Proven: test_alt_text_preference.py"""
        return self._s.gql_get("getAltTextPromptPreference", {},
                               with_features=False, with_toggles=False)

    def alt_text_set(self, prompt_type="None", verify=True):
        """'None' = app default (default-equivalent). Proven: test_alt_text_pair.py"""
        resp = self._s.gql_post("updateAltTextPromptPreference", {"promptType": prompt_type})
        E.guard(resp, "updateAltTextPromptPreference")
        if verify:
            back = self._s.gql_post("getAltTextPromptPreference", {})
            if f'"{prompt_type}"' not in back.raw:
                raise E.XVerifyError("Alt-text read-back mismatch.")
        return resp

    def creator_subscriptions(self, user_id=None):
        """Proven: test_creator_subscriptions.py"""
        return self._s.gql_get("UserCreatorSubscriptions",
                               {"userId": str(user_id or self._me()),
                                "includePromotedContent": False})

    def creator_subscribers(self, user_id=None):
        """Proven: test_creator_subscribers.py"""
        return self._s.gql_get("UserCreatorSubscribers",
                               {"userId": str(user_id or self._me()),
                                "includePromotedContent": False})

    def phone_state(self):
        """Proven: test_profile_phone_state.py"""
        return self._s.gql_get("ProfileUserPhoneState", {})

    def multi_accounts(self):
        """Proven: test_multi_accounts.py"""
        return self._s.rest_get("account/multi/list.json", {})

    def oauth_apps(self):
        """Authorized apps. Proven: test_oauth_apps.py"""
        return self._s.rest_get("oauth/list.json", {})

    def rate_limits(self):
        """Proven: test_rate_limits.py"""
        return self._s.rest_get("application/rate_limit_status.json", {})

    def client_education_flag(self, flag="NewUserPromptEducation"):
        """Proven: test_client_education_flag.py"""
        resp = self._s.gql_post("PutClientEducationFlag", {"flag": flag})
        return E.guard(resp, "PutClientEducationFlag")

    def phone_label_enable(self):
        """Code 37 'Cannot find user phone' when no phone. Proven: test_verified_phone_pair.py"""
        return self._s.gql_post("EnableVerifiedPhoneLabel", {})

    def phone_label_disable(self):
        """Proven: test_verified_phone_pair.py"""
        return self._s.gql_post("DisableVerifiedPhoneLabel", {})

    def data_saver_mode(self, device_id="Windows/Firefox"):
        """Proven: test_data_saver_mode.py"""
        return self._s.gql_get("DataSaverMode", {"device_id": device_id},
                               with_features=False, with_toggles=False)

    def write_data_saver(self, data_saver_enabled, device_id=None, video_autoplay=None, confirm=False):
        """NEVER auto-fire: current videoAutoplay is unreadable. Shape: test_write_datasaver_shape.py."""
        if not confirm:
            raise E.XError("write_data_saver() needs confirm=True (current value unreadable).")
        v = {"dataSaverEnabled": bool(data_saver_enabled)}
        if device_id is not None:
            v["deviceId"] = device_id
        if video_autoplay is not None:
            v["videoAutoplay"] = video_autoplay
        return self._s.gql_post("WriteDataSaverPreferences", v)

    def write_audiospaces_sharing(self, user_id=None, sharing=None, confirm=False):
        """NEVER auto-fire: no read API. Shape: test_sharing_audiospaces_shape.py."""
        if not confirm:
            raise E.XError("write_audiospaces_sharing() needs confirm=True (no read API to restore).")
        return self._s.gql_post("SharingAudiospacesListeningDataWithFollowersUpdate", {
            "userId": str(user_id or self._me()),
            "sharingAudiospacesListeningDataWithFollowers": sharing})
