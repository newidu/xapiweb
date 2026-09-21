"""Mutes & blocks (REST + GraphQL)."""
from .. import errors as E
from ._base import BaseResource


class Moderation(BaseResource):
    # ---- mutes ----
    def mute(self, user_id, verify=True):
        """Proven: test_mute_pair.py"""
        resp = self._s.rest_post_form("mutes/users/create.json",
                                      {"user_id": str(user_id), "skip_status": 1})
        if verify and str(user_id) not in [str(i) for i in (self.mutes_ids().get("ids") or [])]:
            raise E.XVerifyError(f"Mute of {user_id} not confirmed in ids.")
        return resp

    def unmute(self, user_id, verify=True):
        """Proven: test_mute_pair.py"""
        resp = self._s.rest_post_form("mutes/users/destroy.json", {"user_id": str(user_id)})
        if verify and str(user_id) in [str(i) for i in (self.mutes_ids().get("ids") or [])]:
            raise E.XVerifyError(f"Unmute of {user_id} not confirmed in ids.")
        return resp

    def mutes_ids(self):
        """Proven: test_mutes_ids.py"""
        return self._s.rest_get("mutes/users/ids.json", {"cursor": -1})

    def mutes_list(self):
        """Proven: test_mutes_list.py"""
        return self._s.rest_get("mutes/users/list.json", {"cursor": -1})

    def muted_accounts_gql(self):
        """Proven: test_muted_accounts_gql.py"""
        return self._s.gql_get("MutedAccounts", {})

    def advanced_filters(self):
        """May 404 (dead-ish). Proven: test_mutes_advanced_filters.py"""
        return self._s.rest_get("mutes/advanced_filters.json", {})

    # ---- blocks ----
    def block(self, user_id, verify=True):
        """Proven: test_block_pair.py"""
        resp = self._s.rest_post_form("blocks/create.json",
                                      {"user_id": str(user_id), "skip_status": 1})
        if verify and str(user_id) not in [str(i) for i in (self.blocks_ids().get("ids") or [])]:
            raise E.XVerifyError(f"Block of {user_id} not confirmed in ids.")
        return resp

    def unblock(self, user_id, verify=True):
        """Proven: test_block_pair.py"""
        resp = self._s.rest_post_form("blocks/destroy.json", {"user_id": str(user_id)})
        if verify and str(user_id) in [str(i) for i in (self.blocks_ids().get("ids") or [])]:
            raise E.XVerifyError(f"Unblock of {user_id} not confirmed in ids.")
        return resp

    def blocks_ids(self):
        """Proven: test_blocks_ids.py"""
        return self._s.rest_get("blocks/ids.json", {"cursor": -1})

    def blocks_list(self):
        """Proven: test_blocks_list.py"""
        return self._s.rest_get("blocks/list.json", {"cursor": -1, "skip_status": 1})

    def blocked_accounts_gql(self, count=5):
        """Proven: test_blocked_accounts_gql.py"""
        return self._s.gql_get("BlockedAccountsAll", {"count": count})

    def blocked_imported_gql(self):
        """Proven: test_blocked_imported_gql.py"""
        return self._s.gql_get("BlockedAccountsImported", {})

    # ---- DM-specific ----
    def dm_block(self, user_id, verify=True):
        """Lowercase-dm op; ids differ from REST. Proven: test_dm_block_pair.py"""
        resp = self._s.gql_post("dmBlockUser", {"target_user_id": str(user_id)})
        if verify and "Blocked" not in resp.raw:
            raise E.XVerifyError("dmBlock ack missing 'Blocked'.")
        return resp

    def dm_unblock(self, user_id, verify=True):
        """Proven: test_dm_block_pair.py"""
        resp = self._s.gql_post("dmUnblockUser", {"target_user_id": str(user_id)})
        if verify and "Unblocked" not in resp.raw:
            raise E.XVerifyError("dmUnblock ack missing 'Unblocked'.")
        return resp
