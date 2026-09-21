# xapiweb — X Web API Python Library 🐦 (v1.5.2)

**Stdlib only. No pip install needed.** `x_api_pack` එකේ proven API 157ම (157/157 live 2026-09-19) + recipes + rules ඔක්කොම එකතු කරලා හදපු unified Python library එක — ඊට උඩින් අලුත් features live prove කරලා එකතු කරලා තියෙනවා.

## 🆕 What's new

| Version | Added |
|---|---|
| **v1.5.2** | 🔔 **Notifications list** (`notifications.list()` All/Verified/Mentions + `extract_notifications()` parser + paging, user-captured qid, live proven) |
| **v1.4.0** | 🗳️ **Polls** (`create_poll_card`/`post_poll`, 2-4 choices, full cycle proven) · 🧵 **Threads** (`post_thread`, proven) · 🎬 **Video upload** (`upload_video`, chunked+processing, attach proven) · 🤝 **accept/deny/cancel** follow requests (routing proven 409/49) · ✉️ **DM send** (confirm-gated, proven live) + `destroy` (proven, 204) |
| v1.3.1 | `misc.log_promoted_view()` — parameterized promoted-impression beacon (honest docs: NOT organic views) |
| v1.3.0 | 📸🎬 **Media download**: `tweets.media(id)` + `media.download()` / `download_tweet_media()` (photo + best-mp4, live proven) |
| v1.2.0 | 👀 **Views**: `tweets.views(id)`, `tweets.stats(id)`, feed parser එකට `views` key එක (live proven) |
| v1.1.0 | 🔌 `CONNECT_GUIDE.md` (Sinhala setup guide) + `examples/make_session.py` auto-setup |
| v1.0.0 | 14 resources, 157 endpoints, verify-by-reread, structured errors |

## Install

```bash
unzip xapiweb-v1.5.2.zip && cd xapiweb-v1.5.2
# zero dependencies — just use the folder
cp -r xapiweb /your/project/
# or
pip install -e .
```

## Session setup

> 🆕 **First time? Read [`CONNECT_GUIDE.md`](CONNECT_GUIDE.md)** — step-by-step Sinhala guide:
> DevTools වලින් Cookie+ct0 copy කරන හැටි + auto-setup:
> ```bash
> python3 examples/make_session.py   # paste cookie + ct0 → tests + writes my_data.json
> ```

```python
from xapiweb import XClient

# 1. from session file (recommended)
x = XClient.from_session_file("my_data.json")

# 2. explicit
x = XClient(cookie="...", csrf_token="...")  # csrf_token == ct0 cookie value

print(x.health().status)  # 200 => CONNECTED ✅
print(x.me())             # {'id': ..., 'screen_name': ...}
```

> 🔴 `my_data.json` has a LIVE session — keep it private, never share. 401s? Recapture cookies + ct0.

## Quickstart

```python
from xapiweb import XClient
from xapiweb.resources.timelines import extract_tweets

x = XClient.from_session_file("my_data.json")

# ---- reads ----
tweets = extract_tweets(x.timelines.home(count=10))
print(tweets[0]["author"], "👁️", tweets[0]["views"], tweets[0]["text"][:60])

x.timelines.search("from:elonmusk", count=5)     # search (POST-only)
x.trends.place(1)                                # trends by place
x.trends.geo_search("Colombo")                   # geo search
x.notifications.badge_counts()                   # unread polling
from xapiweb.resources.notifications import extract_notifications
for n in extract_notifications(x.notifications.list(count=10)):
    print(n["type"], [u["screen_name"] for u in n["users"]], n["text"][:50])

# ---- impressions (views) ----
x.tweets.views("2101278282700226824")            # → 12855
x.tweets.stats("2101278282700226824")            # → views/likes/retweets/replies/quotes/bookmarks

# ---- media download (photo/video) ----
x.tweets.media("2101284467285401660")            # → [{type, url(best mp4), bitrate, ...}]
x.media.download_tweet_media("2101284467285401660", "./dl")  # → ['./dl/..._0.mp4']

# ---- writes (all verify by re-reading) ----
t = x.tweets.post("hello from xapiweb")             # → t.tweet_id (XTxnError if not posted)
x.tweets.post("nice!", reply_to="2101278282700226824")
mid = x.media.upload_image(open("pic.jpg","rb").read(), alt_text="pic")
x.tweets.post("with pic", media_ids=[mid])
vmid = x.media.upload_video(open("clip.mp4","rb").read())   # chunked + processing poll
x.tweets.post("with video", media_ids=[vmid])
x.tweets.delete(t.tweet_id)                      # verified gone

# ---- polls + threads ----
x.tweets.post_poll("Best language?", ["Python", "JS", "Rust"], duration_minutes=1440)
x.tweets.post_thread(["1/3 hello 🧵", "2/3 middle", "3/3 end"])  # → [id1, id2, id3]

x.engagement.like("2101278282700226824")
x.engagement.retweet("2101278282700226824")      # unretweet() takes the ORIGINAL id!
x.engagement.bookmark_add("2101278282700226824")

x.follows.follow("333357345")                    # verified via lookup
x.follows.accept("2053716980167806978")          # 409/49 when nothing pending
x.moderation.mute("333357345")                   # verified via ids

x.dms.send("2053716980167806978", "hi!", confirm=True)  # REAL send — confirm required

lid = x.lists.create("reading", mode="private").get("id_str")
x.lists.add_member(lid, "333357345")
x.lists.pin(lid); x.lists.unpin(lid); x.lists.destroy(lid)
```

Every call returns a `Response`: `.status` · `.data` (parsed JSON) · `.raw` · `.get(*keys, default)` · `.ok` · `.summary()`.

## Resources (14) — full method reference

### `x.tweets` — tweets
| Method | What |
|---|---|
| `get(id)` / `get_many(ids)` | tweet(s) by id |
| `detail(id)` | conversation/thread + replies |
| `views(id)` | impressions count (int) or None |
| `stats(id)` | views/likes/retweets/replies/quotes/bookmarks in ONE call |
| `media(id)` | attached media list (photo url / best mp4 + bitrate/duration) |
| `oembed(url)`, `similar(id)`, `quick_promote_eligibility(id)`, `moderated_view(id)` | read helpers |
| `drafts()`, `scheduled()` | draft/scheduled reads |
| `post(text, reply_to=None, media_ids=None)` | post, reply, photo/video tweet (verifies id) |
| `post_poll(text, choices[2-4], duration_minutes)` 🆕 | poll tweet (verifies card; `.poll_card`) |
| `create_poll_card(choices, duration)` 🆕 | card_uri only (single-use cards) |
| `post_thread([texts])` 🆕 | chained thread → [ids] (partial ids on `err.posted_ids`) |
| `delete(id)` | delete (verifies gone) |
| `pin(id)` / `unpin(id)` | pin own tweet |
| `set_reply_control(id, mode)` / `remove_reply_control(id)` | ByInvitation/Verified/Subscribers/Community… |
| `add_ad_disclosure` / `add_ai_disclosure` / `remove_disclosure` | labels (verified) |
| `create_note`, `create_highlight`, `delete_highlight` | gated (Premium/eligibility) |

### `x.engagement` — likes etc. (all verified)
`like` / `unlike` · `retweet` / `unretweet(original_id!)` · `bookmark_add` / `bookmark_remove` / `bookmark_search(query)` · `downvote` / `undo_downvote`

### `x.timelines` — timelines + parser
`home(count, seen_ids)` · 14 user timelines (`user_tweets/replies/media/likes/reposts/video/highlights/articles/photo/originals/tweets_and_replies(POST)/super_follow/promoted/promotable`) · `followers(POST-only!)/following/blue_verified_followers/followers_you_know` · `search(query, product)` (POST) · `list_search` / `communities_post_search` / `communities_latest_search` · `generic_by_id` · `moderated` · `pinned` / `pinnable` · `profile_filter` (⚠️ broken server-side) · helpers: `extract_tweets(resp)` (with `views`!), `cursors(resp)` (top/bottom for paging)

### `x.users` — users
`by_screen_name` / `by_id` / `batch_by_ids(POST)` / `batch_by_names` · `viewer` · `username_availability` · `show` / `lookup` (REST, txn-gated) · `verify_credentials` · `recommendations` · `verified_avatars` · `spotlights` · `claims` / `preferences` / `sessions` / `upsells` · `me()` (cached owner)

### `x.follows` — follows (REST, verified)
`follow` / `unfollow` · `lookup` / `show` · `friends_ids` / `followers_ids` / `friends_list` (THE real list) / `followers_list` / `following_preview` (⚠️ limited!) · `friendships_list` / `incoming` / `outgoing` / `no_retweets_ids` · `set_retweets(id, on)` · `accept` / `deny` / `cancel` 🆕 (409/49 when nothing pending) · `remove_follower(id, confirm🔒)`

### `x.moderation` — mutes & blocks (verified)
`mute` / `unmute` / `mutes_ids` / `mutes_list` / `muted_accounts_gql` · `block` / `unblock` / `blocks_ids` / `blocks_list` / `blocked_accounts_gql` / `blocked_imported_gql` · `dm_block` / `dm_unblock`

### `x.lists` — lists + profile pins
`create(name, mode, description)` → `.get("id_str")` · `destroy` · `add_member` / `remove_member` · `mine` / `ownerships` / `memberships` / `subscriptions` · `search(list_id, query)` · `pin` / `unpin` / `update_pins` (⚠️ members READ 404s — add/remove only)

### `x.dms` — DMs
`inbox(count)` · `block` / `unblock` · `set_nsfw_filter(confirm🔒)` · `send(id, text, confirm🔒)` 🆕 (proven live) · `destroy(event_id)` 🆕 (proven live, 204)

### `x.communities` — communities
`post_search` / `latest_search` · `member_typeahead` / `user_typeahead` (need REAL community id) · `moderate` / `unmoderate` (need authorship → code 37 otherwise)

### `x.trends` — trends & explore
`available` (woeids) / `place(woeid)` / `history` / `relevant_users` · `sidebar` / `explore_page` / `connect_tab` / `creator_studio_tab` · `finance_tags` · `geo_search("Colombo")` · `typeahead(q)`

### `x.notifications` — notifications
`list(timeline_type, count, cursor)` 🆕 ← full list: All/Verified/Mentions + `extract_notifications(resp)` parser (type/users/text/time/tweet_id) + page via `cursors(resp)['bottom']` · `badge_counts()` ← polling endpoint · `live_events(seconds)` ← SSE sample

### `x.settings` — settings
`account` (txn-gated) / `help_config` / `email_phone_info` (🔴PRIVATE) / `saved_searches` · `alt_text_get` / `alt_text_set` · `creator_subscriptions` / `creator_subscribers` · `phone_state` / `multi_accounts` / `oauth_apps` / `rate_limits` · `client_education_flag` · `phone_label_enable/disable` · `data_saver_mode` · `write_data_saver(confirm🔒)` / `write_audiospaces_sharing(confirm🔒)`

### `x.media` — media
`upload_image(bytes, media_type, alt_text)` → media_id (orphans expire) · `upload_video(bytes)` 🆕 → media_id (chunked + processing poll) · `download(url, path)` · `download_tweet_media(id, dir)`

### `x.misc` — misc
`authenticate_periscope` (JWT) · `urt_fixtures` / `bakery` / `supported_languages` / `story_topic` / `nfl_follow` / `tv_home_mixer` / `payments_typeahead` / `media_tab_videos` / `fleetline` / `avatar_content` / `biz_team_timeline` / `sidebar_recommendations` / `super_followers` / `premium_paywall` / `season_schedule` / `team_roster` / `vo_upsell` · `log_promoted_view()` beacon (promoted only, NOT organic views) / `csp_report` · `feedback_shape` / `unmention_shape` (shape-only) · `probe_removed` / `probe_deprecated`

🔒 = needs explicit `confirm=True` (no restore path / unsafe to auto-fire / real-world side effect).

## Rules the library enforces (from pack guide §10)

1. **Writes verify by re-reading** (`verify=True` default) — raises `XVerifyError` on phantom acks (e.g. DeleteRetweet with wrapper id, CreateTweet with no id).
2. **Pacing** — ≥1s between calls (`XClient(..., min_interval=1.0)`); one retry on 403/429.
3. **Txn-id auto** — minted per (method, path) from a cached, probe-validated homepage key (dud keys rejected).
4. **Structured errors** (`xapiweb.errors`): `XAuthError`(401) · `XRateLimitError`(403/429) · `XTxnError`(404/34, empty tweet_results, 344-mistext) · `XValidationError`(422) · `XMethodError`(406) · `XApiError` → `XAutomationFlag`(226) / `XGateError`(37) / `XBadRequest`(214) / `XAlreadyError`(327) / `XDailyLimit`(344) · `XVerifyError`.

## Gotchas (read before debugging)

- **Unretweet needs the ORIGINAL id** — wrapper id deletes are silent phantoms.
- **No rest_id ⇒ NOT posted** — `post()` raises `XTxnError` in that case.
- **`retweet_count` lags minutes** — trust `legacy.retweeted`, not the number.
- **POST-only ops 404 on GET**: `Followers`, `UsersByRestIds`, `SearchTimeline`, `HomeTimeline`, `UserTweetsAndReplies`.
- **`views` lives at `result.views.count`** — NOT inside `legacy` (hence `tweets.views()`).
- **Poll cards are single-use** — one card_uri per tweet; orphans expire.
- **Video FINALIZE returns 200** (images: 201) + async processing — `upload_video()` polls STATUS.
- **Bogus ids can 404 on ROUTED endpoints** (accept/deny/dm-destroy) — real-id probes discriminate.
- **Code 327** = already retweeted · **344 on fresh account** = usually bad txn, not a real limit.
- **Bursts → 226/404 storms**: one txn key, ≥1s gaps, cool off on flags.

## NOT included (proven impossible / out of scope — researched 2026-09-20)

Tweet edit (no op in bundle) · scheduled-post (no endpoint found) · `lists/members` read (404) · liker/reposter **lists** (no such op — counts only) · organic view-logging (internal telemetry — intentionally absent) · full analytics dashboard (separate app, no API in web client).

## Zip contents

```
xapiweb-v1.5.2.zip
├── xapiweb/                  library (client, session, errors, response, qids, 14 resources)
│   ├── README.md          ← this file
│   └── CONNECT_GUIDE.md   ← Sinhala account-connect guide
├── examples/              quickstart.py, make_session.py (auto-setup)
├── pyproject.toml
├── xapiweb_smoke_live.py     3 cheap reads (health check)
└── xapiweb_media_proof.py    image upload + attach + delete proof (self-cleaning)
```

## Self-tests

```bash
python3 xapiweb/tests/test_offline.py   # 10 tests, no network (imports, qids, errors, parsing, media, validation, notifs)
python3 xapiweb_smoke_live.py           # 3 cheap reads against your session
python3 examples/quickstart.py       # end-to-end reads demo
```
