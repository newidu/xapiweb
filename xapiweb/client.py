"""XClient: one object for the whole X web API (stdlib only)."""
from .session import Session
from .resources import (Tweets, Engagement, Timelines, Users, Follows, Moderation,
                        Lists, DMs, Communities, Trends, Notifications, Settings, Media, Misc)


class XClient:
    """Unified client. Writes verify by re-reading; calls are paced (>=1s apart).

    Usage:
        from xapiweb import XClient
        x = XClient.from_session_file("my_data.json")   # cookie + csrf_token
        x.timelines.home()
        x.tweets.post("hello", verify=True)
    """

    def __init__(self, cookie=None, csrf_token=None, session=None, **session_kw):
        self.session = session or Session(cookie, csrf_token, **session_kw)
        self._me_cache = None
        self.tweets = Tweets(self)
        self.engagement = Engagement(self)
        self.timelines = Timelines(self)
        self.users = Users(self)
        self.follows = Follows(self)
        self.moderation = Moderation(self)
        self.lists = Lists(self)
        self.dms = DMs(self)
        self.communities = Communities(self)
        self.trends = Trends(self)
        self.notifications = Notifications(self)
        self.settings = Settings(self)
        self.media = Media(self)
        self.misc = Misc(self)

    @classmethod
    def from_session_file(cls, path, **session_kw):
        return cls(session=Session.from_session_file(path, **session_kw))

    @property
    def me_id(self):
        """Session owner's user id (from session file refs, else fetched+cached)."""
        if self.session.refs.get("self_id"):
            return self.session.refs["self_id"]
        return self.me()["id"]

    def me(self):
        """Cached {id, screen_name, name} of the session owner."""
        return self.users.me()

    def health(self):
        """Cheap liveness probe (badge counts). 200 => session alive."""
        return self.notifications.badge_counts()
