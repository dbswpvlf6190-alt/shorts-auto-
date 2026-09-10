import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(BASE_DIR, "credentials", "token.json")
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube",
]

creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())

youtube = build("youtube", "v3", credentials=creds)

channels = youtube.channels().list(part="contentDetails", mine=True).execute()
uploads_playlist = channels["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

items = []
page_token = None
while True:
    resp = youtube.playlistItems().list(
        part="contentDetails,snippet",
        playlistId=uploads_playlist,
        maxResults=50,
        pageToken=page_token,
    ).execute()
    items.extend(resp["items"])
    page_token = resp.get("nextPageToken")
    if not page_token:
        break

video_ids = [it["contentDetails"]["videoId"] for it in items]

results = []
for i in range(0, len(video_ids), 50):
    batch = video_ids[i:i+50]
    vresp = youtube.videos().list(part="status,snippet", id=",".join(batch)).execute()
    for v in vresp["items"]:
        title = v["snippet"]["title"]
        privacy = v["status"]["privacyStatus"]
        results.append((privacy, v["id"], title))

out_path = os.path.join(BASE_DIR, "output", "privacy_check.txt")
with open(out_path, "w", encoding="utf-8") as f:
    for privacy, vid, title in results:
        f.write(f"{privacy}\t{vid}\t{title}\n")

non_public = [r for r in results if r[0] != "public"]
print(f"TOTAL={len(results)} NON_PUBLIC={len(non_public)}")
for privacy, vid, title in non_public:
    print(f"{privacy}\t{vid}")
