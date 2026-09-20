import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(BASE, "output", "_analysis")
creds = Credentials.from_authorized_user_file(os.path.join(BASE, "credentials", "token.json"))
an = build("youtubeAnalytics", "v2", credentials=creds)
END = "2026-09-20"


def q(name, **kw):
    try:
        r = an.reports().query(ids="channel==MINE", endDate=kw.pop("endDate", END), **kw).execute()
        rows = r.get("rows", [])
        heads = [h["name"] for h in r["columnHeaders"]]
        json.dump({"heads": heads, "rows": rows}, open(os.path.join(OUT, f"{name}.json"), "w", encoding="utf-8"), ensure_ascii=False)
        print(f"OK  {name}: {len(rows)} rows")
        return heads, rows
    except Exception as e:
        print(f"ERR {name}: {str(e)[:160]}")
        return None, None


core = "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost,likes,comments,shares"
q("daily", startDate="2026-05-01", dimensions="day", metrics="views,subscribersGained,subscribersLost,averageViewPercentage", sort="day")
q("traffic_auto", startDate="2026-08-15", dimensions="insightTrafficSourceType", metrics="views,estimatedMinutesWatched,subscribersGained", sort="-views")
q("traffic_pre", startDate="2026-06-01", endDate="2026-08-14", dimensions="insightTrafficSourceType", metrics="views,estimatedMinutesWatched,subscribersGained", sort="-views")
q("subscribed_status", startDate="2026-08-15", dimensions="subscribedStatus", metrics="views,estimatedMinutesWatched,averageViewPercentage")
q("content_type", startDate="2026-06-01", dimensions="creatorContentType", metrics=core)
q("age_gender", startDate="2026-08-15", dimensions="ageGroup,gender", metrics="viewerPercentage")
q("country", startDate="2026-08-15", dimensions="country", metrics="views", sort="-views", maxResults=8)
q("device", startDate="2026-08-15", dimensions="deviceType", metrics="views,averageViewPercentage")
q("per_video", startDate="2026-01-01", dimensions="video",
  metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,likes,comments,shares",
  sort="-views", maxResults=200)
q("engaged", startDate="2026-08-15", dimensions="day", metrics="views,engagedViews", sort="day")
