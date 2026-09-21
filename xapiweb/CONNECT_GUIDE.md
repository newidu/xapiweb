# 🔌 xapiweb — X Account එකට Connect කරන හැටි (Step-by-Step)

මේ guide එකෙන් ඔයාගෙ **X (Twitter) account එක** xapiweb එකට connect කරගන්න පුළුවන්. OAuth app එකක් අවශ්‍ය **නැහැ** — ඔයාගෙම browser login session එක reuse කරනවා.

> ⏱️ වෙලාව: විනාඩි 5යි · 😟 අමාරු නැහැ — copy-paste විතරයි

---

## 0. අවශ්‍ය දේ

- 💻 Computer එකේ **Chrome / Edge / Firefox** (phone browser එකෙන් බැහැ)
- 🐦 X account එකට browser එකේ **login වෙලා** ඉන්න ඕන
- 🐍 **Python 3.8+** (`python3 --version` කියලා check කරන්න)
- 📦 මේ zip එක unzip කරලා තියෙන්න ඕන

---

## 1. X.com එකට login වෙන්න

1. Browser එකේ https://x.com/home අරින්න
2. ඔයාගෙ account එකට **login** වෙන්න (තවම නැත්නම්)
3. Home timeline එක පේනවා කියලා confirm කරගන්න ✅

---

## 2. Cookie + Token (ct0) දෙක copy කරගන්න

මේ තමයි වැදගත්ම step එක. හරියටම පිළිපදින්න 👇

### Chrome / Edge වලින්:

1. `x.com/home` page එකේ **`F12`** ඔබන්න (DevTools ඇරෙනවා)
2. DevTools එකේ **`Network`** tab එක click කරන්න
3. Filter box එකේ **`graphql`** කියලා type කරන්න
4. Page එක **`F5`** (refresh) කරන්න — graphql requests පේන්න ගනී
5. List එකෙන් **`UserByScreenName`** වගේ එකක් click කරන්න
   (නැත්නම් ඕනෑම graphql request එකක් — කමක් නැහැ)
6. දකුණු පැත්තේ **`Headers`** tab එකේ පහළට scroll කරන්න:
   - **`Cookie:`** — ඉස්සරහා තියෙන දිග value එක **සම්පූර්ණයෙන්ම copy** කරන්න
     (Right-click → Copy value). මේක අකුරු ~1500-2000ක් දිගයි — කෑල්ලක් නෙවෙයි, **මුල්ලම** ඕන!
   - **`x-csrf-token:`** — මේ value එකත් copy කරන්න (ct0 cookie එකේ value එකම තමයි)

### Firefox වලින්:

1. `x.com/home` page එකේ **`F12`** → **`Network`** tab
2. Page refresh (`F5`) → request එකක් click (උදා: `HomeTimeline`)
3. දකුණේ **Headers → Request headers** වලින් **`Cookie`** + **`x-csrf-token`** copy කරන්න (උඩ වගේම)

> ✅ හරි නම්: Cookie එක `auth_token=...; ct0=...; ...` වගේ දිග string එකක්.
> ✅ `x-csrf-token` value එක Cookie එක ඇතුළේ තියෙන `ct0=...` value එකට **සමාන වෙන්නම** ඕන.

---

## 3. `my_data.json` හදන්න (ක්‍රම 2ක් — ලේසි එක තෝරගන්න)

### 🅰️ Auto ක්‍රමය (recommended — විනාඩියයි)

```bash
cd xapiweb-v1.1.0
python3 examples/make_session.py
```

Script එක අහනවා:
1. `Cookie` එක paste කරන්න (Step 2 එකේ copy කරපු දිග එක)
2. `x-csrf-token` (ct0) එක paste කරන්න
3. Enter → script එක **connection එක test කරලා** `my_data.json` හදලා දෙනවා 🎉
   (ඔයාගෙ user id + screen name එයාම අරගෙන fill කරනවා)

### 🅱️ Manual ක්‍රමය

`my_data.json` කියලා file එකක් හදලා මේ template එකට values දාන්න:

```json
{
  "account": "my_x_account",
  "cookie": "PASTE_FULL_COOKIE_HERE",
  "csrf_token": "PASTE_CT0_HERE",
  "reference_ids": {},
  "exported_at": "2026-09-20",
  "warning": "PRIVATE - never share this file"
}
```

> `bearer` / `user_agent` නොදාත් කමක් නැහැ — library එකේ defaults වැඩ කරනවා.

---

## 4. Connect කරලා test කරන්න 🧪

```python
from xapiweb import XClient

x = XClient.from_session_file("my_data.json")

print(x.health().status)   # 200 ආවොත් = CONNECTED ✅
print(x.me())              # {'id': ..., 'screen_name': 'ඔයාගෙ නම', ...}
```

Terminal එකෙන් එකපාරම:
```bash
python3 xapiweb_smoke_live.py
```

```
health: 200
me: snewidu 1953022725322358788
viewer: 200
home: 200
SMOKE OK
```

වගේ ආවොත් **සේරම හරි!** 🎉 ඊළඟට `python3 examples/quickstart.py` run කරලා බලන්න.

---

## 5. දැන් මොනවද කරන්න පුළුවන්?

```python
from xapiweb.resources.timelines import extract_tweets

tweets = extract_tweets(x.timelines.home(count=10))  # home කියවනවා
x.timelines.search("from:elonmusk")                   # search
x.tweets.post("hello!")                               # tweet
x.engagement.like("2101278282700226824")              # like
x.follows.follow("333357345")                         # follow
```

සම්පූර්ණ list එක: [`README.md`](README.md) බලන්න.

---

## 6. Troubleshooting 🔧

| ප්‍රශ්නේ | හේතුව | විසඳුම |
|---|---|---|
| `XAuthError` / HTTP 401 | cookies expire වෙලා (සති/මාස ගානකින් වෙනවා) | **Step 2-3 ආයෙ කරලා** අලුත් `my_data.json` හදන්න |
| `XTxnError` / 404 code 34 | txn key අවුලක් (library එක auto-handle කරනවා, කලාතුරකින්) | `.txn_cache.json` delete කරලා retry; හරි නැත්නම් ටිකක් ඉඳලා retry |
| `XAutomationFlag` (226) | calls වැඩියි / burst එකක් | විනාඩි කීපයක් නවතින්න; `min_interval` වැඩි කරන්න (`XClient(..., min_interval=2.0)`) |
| `XVerifyError` | ack එක බොරු / state change නැහැ | re-read කරලා බලන්න; retweet නම් **original id** දුන්නද කියලා බලන්න |
| Cookie short / login page එනවා | copy එක අඩුයි / login නැහැ | Cookie **මුල්ලම** copy වුණාද බලන්න; browser එකේ loginද බලන්න |
| `ct0` mismatch | csrf වැරදි field එකක් | `x-csrf-token` header එකෙන්ම copy කරන්න (DevTools → Headers) |

---

## 7. ආරක්ෂාව 🛡️ (වැදගත්!)

1. 🔴 **`my_data.json` කාටවත් දෙන්න එපා** — මේකේ ඔයාගෙ LIVE login session එක තියෙනවා. මේකෙන් කෙනෙක්ට ඔයා වගේ X use කරන්න පුළුවන්!
2. 🔴 `my_data.json` **GitHub / zip / screenshot** වලට දාන්න එපා.
3. 🟡 Account එකේ **2FA on** කරලා තියාගන්න (අමතර ආරක්ෂාවට).
4. 🟡 Library එක unofficial — calls අතර gap තියාගන්න (default 1s ඇති), flooding කරන්න එපා.
5. 🟢 වෙන කෙනෙක්ට library එක දෙනවා නම් **මේ zip එක විතරක්** දෙන්න — `my_data.json` නැතුව. එයා එයාගෙම session එකෙන් Step 2-3 කරගනී.

---

## 8. Session අලුත් කරන හැටි 🔄

Cookies කවදාහරි expire වුණොත් (401 errors එනවා):
1. Browser එකේ x.com refresh කරලා තාම loginද බලන්න
2. Step 2 එකෙන් අලුත් Cookie + ct0 copy කරන්න
3. `python3 examples/make_session.py` ආයෙ run කරන්න (overwrite වෙනවා)
4. `python3 xapiweb_smoke_live.py` — 200 ආවොත් හරි ✅

---

**හිරවුණොත්?** Error message එකේ type එක බලලා (§6 table) ඒ අනුව කරන්න. `health()` 200 නම් session එක හොඳයි — ප්‍රශ්නේ වෙන තැනක.
