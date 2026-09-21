"""Media: image/video upload + tweet media (photo/video) download."""
import json
import os
import time
import urllib.parse
import urllib.request

from .. import errors as E
from ._base import BaseResource


class Media(BaseResource):
    def upload_image(self, image_bytes, media_type="image/png",
                     category="tweet_image", alt_text=None):
        """Upload image bytes; returns media_id_string. Orphaned uploads (never attached
        to a tweet) expire unattached. Proven: test_media_upload_cycle.py"""
        p = "/i/media/upload.json"
        init = self._s.call(
            "POST", f"https://upload.x.com{p}?command=INIT&total_bytes={len(image_bytes)}"
                    f"&media_type={media_type}&media_category={category}", "")
        mid = init.get("media_id_string")
        if init.status != 202 or not mid:
            raise E.XError(f"Media INIT failed: {init.status} {init.raw[:200]}")
        boundary = "----xapiweb1234"
        mp = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; "
              f"filename=\"p.png\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode() \
             + image_bytes + f"\r\n--{boundary}--\r\n".encode()
        app = self._s.call(
            "POST", f"https://upload.x.com{p}?command=APPEND&media_id={mid}&segment_index=0",
            mp, f"multipart/form-data; boundary={boundary}")
        if app.status != 204:
            raise E.XError(f"Media APPEND failed: {app.status} {app.raw[:200]}")
        fin = self._s.call("POST", f"https://upload.x.com{p}?command=FINALIZE&media_id={mid}", "")
        if fin.status != 201:
            raise E.XError(f"Media FINALIZE failed: {fin.status} {fin.raw[:200]}")
        if alt_text:
            meta = self._s.call("POST", "https://x.com/i/api/1.1/media/metadata/create.json",
                                json.dumps({"media_id": mid, "alt_text": {"text": alt_text}}))
            if meta.status != 200:
                raise E.XError(f"Alt-text failed: {meta.status} {meta.raw[:200]}")
        return mid

    def upload_video(self, video_bytes, media_type="video/mp4", category="tweet_video",
                     chunk_size=1024 * 1024, poll_timeout=180):
        """Chunked video upload (INIT->APPEND*->FINALIZE) + processing poll.

        Returns media_id_string once processing succeeds; attach via
        tweets.post(text, media_ids=[mid]). Orphaned uploads expire unattached.
        Proven live by xapiweb 2026-09-20."""
        p = "/i/media/upload.json"
        total = len(video_bytes)
        init = self._s.call(
            "POST", f"https://upload.x.com{p}?command=INIT&total_bytes={total}"
                    f"&media_type={media_type}&media_category={category}", "")
        mid = init.get("media_id_string")
        if init.status != 202 or not mid:
            raise E.XError(f"Video INIT failed: {init.status} {init.raw[:200]}")
        boundary = "----xapiwebvid"
        for n, start in enumerate(range(0, total, chunk_size)):
            mp = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; "
                  f"filename=\"v.mp4\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode() \
                 + video_bytes[start:start + chunk_size] + f"\r\n--{boundary}--\r\n".encode()
            app = self._s.call(
                "POST", f"https://upload.x.com{p}?command=APPEND&media_id={mid}&segment_index={n}",
                mp, f"multipart/form-data; boundary={boundary}", timeout=90)
            if app.status != 204:
                raise E.XError(f"Video APPEND seg {n} failed: {app.status} {app.raw[:200]}")
        fin = self._s.call("POST", f"https://upload.x.com{p}?command=FINALIZE&media_id={mid}",
                           "", timeout=90)
        if fin.status not in (200, 201):  # video: 200, image: 201
            raise E.XError(f"Video FINALIZE failed: {fin.status} {fin.raw[:200]}")
        info = fin.get("processing_info") or {}
        state = info.get("state")
        t0 = time.time()
        while state in ("pending", "in_progress"):
            if time.time() - t0 > poll_timeout:
                raise E.XError(f"Video processing timed out (media_id={mid}, last={state})")
            time.sleep(info.get("check_after_secs") or 3)
            st = self._s.call("GET", f"https://upload.x.com{p}?command=STATUS&media_id={mid}")
            info = st.get("processing_info") or {}
            state = info.get("state")
        if state == "failed":
            raise E.XError(f"Video processing failed: {json.dumps(info.get('error', info))[:250]}")
        if state != "succeeded":
            raise E.XError(f"Video processing state={state} (media_id={mid})")
        return mid

    def download(self, url, dest_path, timeout=60):
        """Download a media URL (pbs/video CDN, no auth needed) to dest_path.
        Returns dest_path. Proven live by xapiweb 2026-09-20."""
        req = urllib.request.Request(url, headers={"User-Agent": self._s.user_agent})
        total = 0
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
        if total == 0:
            raise E.XError(f"Downloaded 0 bytes from {url}")
        return dest_path

    def download_tweet_media(self, tweet_id, dest_dir="."):
        """Download ALL media of a tweet into dest_dir (photo/video/gif).
        Returns [paths]. Proven live by xapiweb 2026-09-20."""
        os.makedirs(dest_dir, exist_ok=True)
        paths = []
        for i, m in enumerate(self._client.tweets.media(tweet_id)):
            if not m.get("url"):
                continue
            if m["type"] in ("video", "animated_gif"):
                ext = ".mp4"
            else:
                ext = os.path.splitext(urllib.parse.urlparse(m["url"]).path)[1] or ".jpg"
            paths.append(self.download(m["url"], os.path.join(dest_dir, f"{tweet_id}_{i}{ext}")))
        return paths

    # NOTE: image upload stays single-segment (proven); video uses upload_video().


def parse_media_entities(leg):
    """legacy -> [{type, url, thumb, width, height, duration_ms, bitrate, variants}].

    photo -> direct image url; video/animated_gif -> best (max-bitrate) mp4 url.
    Pure function (offline-testable). Proven live by xapiweb 2026-09-20."""
    out = []
    entities = leg.get("extended_entities") or leg.get("entities") or {}
    for m in entities.get("media") or []:
        if not isinstance(m, dict):
            continue
        typ = m.get("type")
        info = m.get("original_info") or {}
        item = {"type": typ, "id": m.get("id_str"), "thumb": m.get("media_url_https"),
                "width": info.get("width"), "height": info.get("height"),
                "allow_download": ((m.get("allow_download_status") or {}).get("allow_download"))}
        if typ == "photo":
            item["url"] = m.get("media_url_https")
        else:
            vinfo = m.get("video_info") or {}
            variants = vinfo.get("variants") or []
            mp4s = [v for v in variants
                    if isinstance(v, dict) and v.get("content_type") == "video/mp4" and v.get("url")]
            best = max(mp4s, key=lambda v: v.get("bitrate") or 0) if mp4s else None
            item["url"] = best["url"] if best else None
            item["bitrate"] = best.get("bitrate") if best else None
            item["duration_ms"] = vinfo.get("duration_millis")
            item["variants"] = variants
        out.append(item)
    return out
