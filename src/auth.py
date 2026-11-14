#!/usr/bin/env python3
"""One-time TikTok OAuth helper.

Prints an authorization URL, you approve it in the browser, then paste the
`code` from the redirect URL back here. Exchanges it for tokens and writes
.env (client key/secret + refresh token) next to the project root.

Usage:
  python3 src/auth.py --client-key XXX --client-secret YYY \
      --redirect-uri https://00hideo00-ship-it.github.io/yutai-auto-poster/callback.html
The redirect URI must exactly match the one registered in the TikTok app
(Login Kit settings). After approval the browser may fail to load the
localhost page - that is fine; copy the `code=...` value from the address bar.
"""
import argparse, json, os, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"


def _env_file():
    vals = {}
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip()
    return vals


def main():
    env = _env_file()
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-key", default=env.get("TIKTOK_CLIENT_KEY"))
    ap.add_argument("--client-secret", default=env.get("TIKTOK_CLIENT_SECRET"))
    ap.add_argument("--redirect-uri", default="https://00hideo00-ship-it.github.io/yutai-auto-poster/callback.html")
    ap.add_argument("--scope", default="user.info.basic,video.upload")
    args = ap.parse_args()
    if not args.client_key or not args.client_secret:
        ap.error("--client-key/--client-secret are required when .env has none")

    q = urllib.parse.urlencode({
        "client_key": args.client_key, "scope": args.scope,
        "response_type": "code", "redirect_uri": args.redirect_uri,
        "state": "yutai"})
    print("\n1) Open this URL and approve with your TikTok account:\n")
    print(f"{AUTH_URL}?{q}")
    print("\n2) After approval, copy the `code` value from the redirect URL.")
    code = input("Paste code: ").strip()
    if code.startswith("http"):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(code).query)
        code = qs.get("code", [""])[0]

    body = urllib.parse.urlencode({
        "client_key": args.client_key, "client_secret": args.client_secret,
        "code": code, "grant_type": "authorization_code",
        "redirect_uri": args.redirect_uri}).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, headers={
        "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode())
    if "refresh_token" not in data:
        print("Token exchange failed:", data)
        return 1
    env_path = os.path.join(ROOT, ".env")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f"TIKTOK_CLIENT_KEY={args.client_key}\n")
        f.write(f"TIKTOK_CLIENT_SECRET={args.client_secret}\n")
        f.write(f"TIKTOK_REFRESH_TOKEN={data['refresh_token']}\n")
    print(f"\nSaved {env_path}")
    print(f"open_id: {data.get('open_id')}")
    print(f"access token expires in {data.get('expires_in')}s; "
          f"refresh token expires in {data.get('refresh_expires_in')}s")
    print("For GitHub Actions, register the same 3 values as repository Secrets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
