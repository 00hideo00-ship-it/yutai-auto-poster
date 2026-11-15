# Demo video fact-check (tiktok_demo_v1.mp4, 52s, built 2026-11-15)

All segments are real screen recordings from 2026-11-15 on the owner's PC; edited for length only, no fabricated screens.

| Segment | Time in demo | Claim shown | Source |
|---|---|---|---|
| A | 0–5.5s | auth.py prints the TikTok authorize URL (scopes user.info.basic, video.upload) and waits at "Paste code:" | take2.mp4 0–5.5s, actual run |
| B | 5.5–13.7s | Browser opens the authorize URL; callback page shows "Authorization succeeded. Your code:" | take2.mp4 12.8–21.0s, GitHub Pages callback |
| C | 13.7–16.4s | Code pasted; "Saved ...\.env", open_id, access/refresh token expiry printed | take1.mp4 34.5–37.2s, actual successful exchange. The command line containing the sandbox client secret is blurred (y 306–362) — verified unreadable in out_15.jpg |
| D | 16.4–52s | main.py: "fact-check OK", "video built", "posted: SEND_TO_USER_INBOX (v_inbox_file~v2.7708154203637598214)" | take2.mp4 107.5–143.1s, actual run |

Checks performed: frames extracted at 3s/10s/15s/25s/48s of the finished file and read; secret blur verified; duration 52.0s; no other credentials visible (one-time auth codes shown are already consumed).
