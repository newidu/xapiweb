"""Trends, explore, search helpers, geo."""
from ._base import BaseResource


class Trends(BaseResource):
    def available(self):
        """Trend locations (woeids). Proven: test_trends_available.py"""
        return self._s.rest_get("trends/available.json", {})

    def place(self, woeid=1):
        """Proven: test_trends_place.py"""
        return self._s.rest_get("trends/place.json", {"id": woeid})

    def history(self, trend_id):
        """Proven: test_trend_history.py"""
        return self._s.gql_get("TrendHistory", {"trendId": str(trend_id)})

    def relevant_users(self, trend_id):
        """Proven: test_trend_relevant_users.py"""
        return self._s.gql_get("TrendRelevantUsers", {"trendId": str(trend_id)})

    def sidebar(self):
        """Explore sidebar. Proven: test_explore_sidebar.py"""
        return self._s.gql_get("ExploreSidebar", {}, with_toggles=False)

    def explore_page(self, candidate="news", tab="news"):
        """Proven: test_explore_page.py"""
        return self._s.gql_get("ExplorePage", {"candidateId": candidate, "tabId": tab})

    def connect_tab(self, count=5):
        """Proven: test_connect_tab.py"""
        return self._s.gql_get("ConnectTabTimeline", {"count": count})

    def creator_studio_tab(self):
        """Proven: test_creator_studio_tab.py"""
        return self._s.gql_get("CreatorStudioTabBarItemQuery", {},
                               with_features=False, with_toggles=False)

    def finance_tags(self, query):
        """Proven: test_finance_tags.py"""
        return self._s.gql_get("FinanceSearchTags", {"query": query})

    def geo_search(self, query):
        """E.g. 'Colombo'. Proven: test_geo_search.py"""
        return self._s.rest_get("geo/search.json", {"query": query})

    def typeahead(self, q):
        """Search typeahead. Proven: test_search_typeahead.py"""
        return self._s.rest_get("search/typeahead.json", {"q": q, "src": "search_box"})
