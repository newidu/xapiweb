"""DMs: inbox read, DM block, send (confirm-gated), destroy."""
import json

from .. import errors as E
from ._base import BaseResource


class DMs(BaseResource):
    def inbox(self, count=3):
        """DM inbox events. Proven: test_dm_list.py"""
        return self._s.rest_get("direct_messages/events/list.json", {"count": count})

    def block(self, user_id):
        """DM-specific block. Proven: test_dm_block_pair.py"""
        return self._client.moderation.dm_block(user_id)

    def unblock(self, user_id):
        """Proven: test_dm_block_pair.py"""
        return self._client.moderation.dm_unblock(user_id)

    def set_nsfw_filter(self, user_id=None, dm_nsfw_media_filter=None, confirm=False):
        """NEVER auto-fire: no read API exists to restore the current value.
        Shape proven (422 names vars): test_dm_nsfw_shape.py. Pass confirm=True to fire."""
        if not confirm:
            raise E.XError("set_nsfw_filter() needs confirm=True: current value is unreadable, "
                           "so the change cannot be restored automatically.")
        return self._s.gql_post("DmNsfwMediaFilterUpdate", {
            "userId": str(user_id or self._me()), "dmNsfwMediaFilter": dm_nsfw_media_filter})

    def send(self, recipient_id, text, confirm=False):
        """Send a DM. Proven live 2026-09-20 (200 + event id; test message deleted
        right after via destroy). Pass confirm=True to fire.
        Event id at .get('event','id')."""
        if not confirm:
            raise E.XError("dms.send() needs confirm=True (sends a REAL message to a REAL person).")
        if not text:
            raise ValueError("text is required")
        return self._s.call(
            "POST", "https://x.com/i/api/1.1/direct_messages/events/new.json",
            json.dumps({"event": {"type": "message_create", "message_create": {
                "target": {"recipient_id": str(recipient_id)},
                "message_data": {"text": text}}}}))

    def destroy(self, event_id):
        """Delete a DM event. Proven live 2026-09-20 (204 on real id, 404 on bogus)."""
        return self._s.call(
            "DELETE",
            f"https://x.com/i/api/1.1/direct_messages/events/destroy.json?id={event_id}")
