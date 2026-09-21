"""Interactive session builder: paste cookie + ct0 -> tests connection -> writes my_data.json.

Run: python3 examples/make_session.py
See: xapiweb/CONNECT_GUIDE.md (Step 2 for how to copy cookie + ct0 from DevTools)
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xapiweb import XClient, Session  # noqa: E402


def main():
    print("=" * 60)
    print("  xapiweb session setup  (see xapiweb/CONNECT_GUIDE.md Step 2)")
    print("=" * 60)
    cookie = input("\n1) Paste FULL Cookie header value:\n> ").strip().strip('"').strip("'")
    csrf = input("\n2) Paste x-csrf-token (ct0) value:\n> ").strip().strip('"').strip("'")
    if len(cookie) < 200:
        print("\n❌ Cookie looks too short — copy the ENTIRE Cookie header (usually 1500+ chars).")
        sys.exit(1)
    if len(csrf) < 20:
        print("\n❌ csrf token looks too short — copy x-csrf-token from request Headers.")
        sys.exit(1)
    if csrf not in cookie:
        print("\n⚠️  WARNING: ct0 value not found inside Cookie — they may be from different "
              "requests. Continuing anyway, but connection may fail.")

    print("\n🔌 Testing connection...")
    try:
        x = XClient(cookie=cookie, csrf_token=csrf)
        h = x.health()
        print("   health:", h.status)
        if h.status != 200:
            print("❌ Session rejected. Re-copy fresh Cookie + ct0 from a logged-in tab.")
            sys.exit(1)
        me = x.me()
        print(f"   me: @{me['screen_name']} ({me['id']})")
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}: {str(e)[:250]}")
        print("   Re-copy fresh Cookie + ct0 and try again.")
        sys.exit(1)

    out = {
        "account": me["screen_name"],
        "cookie": cookie,
        "csrf_token": csrf,
        "bearer": Session(cookie="x", csrf_token="y").bearer,
        "user_agent": Session(cookie="x", csrf_token="y").user_agent,
        "reference_ids": {"self_id": me["id"], "self_screen_name": me["screen_name"]},
        "exported_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "warning": "PRIVATE - live X session. Never share this file.",
    }
    out_path = os.path.join(os.getcwd(), "my_data.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n✅ Wrote {out_path} — keep it PRIVATE!")
    print("   Next: python3 xapiweb_smoke_live.py")


if __name__ == "__main__":
    main()
