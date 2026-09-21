"""Communities: search, typeaheads, tweet moderation shapes."""
from ._base import BaseResource


class Communities(BaseResource):
    def post_search(self, raw_query, count=5):
        """Proven: test_communities_post_search.py"""
        return self._s.gql_get("GlobalCommunitiesPostSearchTimeline",
                               {"rawQuery": raw_query, "count": count})

    def latest_search(self, raw_query, count=5):
        """Proven: test_communities_latest_search.py"""
        return self._s.gql_get("GlobalCommunitiesLatestPostSearchTimeline",
                               {"rawQuery": raw_query, "count": count})

    def member_typeahead(self, community_id, prefix="a"):
        """Needs a REAL community id (bogus => CommunityUnavailable).
        Proven: test_community_member_typeahead.py"""
        return self._s.gql_post("CommunityMemberRelationshipTypeahead",
                                {"communityId": str(community_id), "prefix": prefix})

    def user_typeahead(self, community_id, prefix="a"):
        """Proven: test_community_user_typeahead.py"""
        return self._s.gql_post("CommunityUserRelationshipTypeahead",
                                {"communityId": str(community_id), "prefix": prefix})

    def moderate(self, tweet_id):
        """Requires conversation authorship (code 37 otherwise — safe on others' tweets).
        Proven: test_moderate_tweet_shape.py"""
        return self._s.gql_post("ModerateTweet", {"tweetId": str(tweet_id)})

    def unmoderate(self, tweet_id):
        """Proven: test_unmoderate_tweet_shape.py"""
        return self._s.gql_post("UnmoderateTweet", {"tweetId": str(tweet_id)})
