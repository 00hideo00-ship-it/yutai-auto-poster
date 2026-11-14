#!/usr/bin/env python3
"""TikTok Content Posting API client (stdlib only).

Modes:
- draft  (scope video.upload): video goes to the creator's TikTok inbox;
  the creator finishes/publishes in the app. No audit needed for that step.
- direct (scope video.publish): publishes straight to the profile.
  Until the app passes TikTok's audit, posts are forced SELF_ONLY and the
  account must be private. Public posting needs the audit.

Tokens: access_token expires in 24h, so we refresh with the refresh_token
on every run (client_key/client_secret/refresh_token from env or .env).
"""
import json, os, time, urllib.error, urllib.parse, urllib.request

BASE = "https://open.tiktokapis.com/v2"

def _post_json(url, token, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8",
                 "User-Agent": "yutai-auto-poster/1.0"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code} from {url}: {body}") from None

def refresh_access_token(client_key, client_secret, refresh_token):
    body = urllib.parse.urlencode({
        "client_key": client_key, "client_secret": client_secret,
        "grant_type": "refresh_token", "refresh_token": refresh_token}).encode()
    req = urllib.request.Request(f"{BASE}/oauth/token/", data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded",
                                          "User-Agent": "yutai-auto-poster/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code} from token endpoint: {body}") from None
    if "access_token" not in data:
        raise RuntimeError(f"token refresh failed: {data}")
    return data  # contains access_token and a NEW refresh_token (rotate it!)

def creator_info(token):
    return _post_json(f"{BASE}/post/publish/creator_info/query/", token, {})

def _chunks(file_size):
    # TikTok rules: chunk 5-64MB; a file under 64MB can go as one chunk
    return file_size, 1

def init_direct(token, title, privacy_level, file_size):
    chunk_size, total = _chunks(file_size)
    return _post_json(f"{BASE}/post/publish/video/init/", token, {
        "post_info": {"title": title, "privacy_level": privacy_level,
                      "disable_comment": False, "disable_duet": False, "disable_stitch": False},
        "source_info": {"source": "FILE_UPLOAD", "video_size": file_size,
                        "chunk_size": chunk_size, "total_chunk_count": total}})

def init_draft(token, file_size):
    chunk_size, total = _chunks(file_size)
    return _post_json(f"{BASE}/post/publish/inbox/video/init/", token, {
        "source_info": {"source": "FILE_UPLOAD", "video_size": file_size,
                        "chunk_size": chunk_size, "total_chunk_count": total}})

def upload_file(upload_url, file_path):
    size = os.path.getsize(file_path)
    with open(file_path, "rb") as f:
        data = f.read()
    req = urllib.request.Request(upload_url, data=data, method="PUT", headers={
        "Content-Type": "video/mp4", "Content-Length": str(size),
        "Content-Range": f"bytes 0-{size-1}/{size}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.status

def fetch_status(token, publish_id):
    return _post_json(f"{BASE}/post/publish/status/fetch/", token, {"publish_id": publish_id})

def post_video(token, file_path, title, mode="draft", privacy_level="SELF_ONLY",
               poll_seconds=120):
    size = os.path.getsize(file_path)
    info = creator_info(token)
    creator = info.get("data", {})
    if mode == "direct":
        max_dur = creator.get("max_video_post_duration_sec", 180)
        if 30 > max_dur:
            raise RuntimeError(f"creator max duration {max_dur}s < 30s")
        options = creator.get("privacy_level_options", [])
        if options and privacy_level not in options:
            raise RuntimeError(f"privacy {privacy_level} not in creator options {options}")
        res = init_direct(token, title, privacy_level, size)
    else:
        res = init_draft(token, size)
    data = res.get("data", {})
    publish_id, upload_url = data.get("publish_id"), data.get("upload_url")
    if not publish_id or not upload_url:
        raise RuntimeError(f"init failed: {res}")
    upload_file(upload_url, file_path)
    deadline = time.time() + poll_seconds
    last = None
    while time.time() < deadline:
        st = fetch_status(token, publish_id)
        status = st.get("data", {}).get("status")
        last = st
        if status in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
            return {"publish_id": publish_id, "status": status, "raw": st}
        if status == "FAILED":
            raise RuntimeError(f"publish failed: {st}")
        time.sleep(5)
    return {"publish_id": publish_id, "status": "TIMEOUT", "raw": last}
