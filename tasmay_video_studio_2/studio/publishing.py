from pathlib import Path
import os, time, requests
from studio.config import env

def upload_youtube(video_path, title, description, tags=None, privacy="private", thumbnail=None):
    """OAuth desktop flow; first run opens browser and stores token locally."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    scopes=["https://www.googleapis.com/auth/youtube.upload"]
    secrets=env("YOUTUBE_CLIENT_SECRETS","client_secrets.json")
    token=env("YOUTUBE_TOKEN_FILE","youtube_token.json")
    creds=None
    if Path(token).exists(): creds=Credentials.from_authorized_user_file(token,scopes)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not Path(secrets).exists(): raise RuntimeError(f"Missing OAuth file: {secrets}")
        flow=InstalledAppFlow.from_client_secrets_file(secrets,scopes)
        creds=flow.run_local_server(port=0)
        Path(token).write_text(creds.to_json(),encoding="utf-8")
    yt=build("youtube","v3",credentials=creds)
    body={"snippet":{"title":title[:100],"description":description[:5000],
                     "tags":(tags or [])[:500],"categoryId":"24"},
          "status":{"privacyStatus":privacy,"selfDeclaredMadeForKids":True}}
    req=yt.videos().insert(part="snippet,status",body=body,
        media_body=MediaFileUpload(str(video_path),chunksize=-1,resumable=True))
    response=None
    while response is None:
        status,response=req.next_chunk()
        if status: print(f"YouTube upload {int(status.progress()*100)}%")
    video_id=response["id"]
    if thumbnail and Path(thumbnail).exists():
        yt.thumbnails().set(videoId=video_id,media_body=MediaFileUpload(str(thumbnail))).execute()
    return "https://www.youtube.com/watch?v="+video_id

def publish_instagram(media_url, caption, media_type="REELS", image=False):
    """Requires public media URL, IG professional account and approved publishing permissions."""
    token=env("INSTAGRAM_ACCESS_TOKEN"); account=env("INSTAGRAM_ACCOUNT_ID")
    version=env("META_GRAPH_VERSION","v27.0")
    if not token or not account: raise RuntimeError("Set Instagram professional account ID and access token in .env")
    host="https://graph.instagram.com"
    params={"access_token":token,"caption":caption}
    if image:
        params["image_url"]=media_url
    else:
        params["media_type"]="REELS" if media_type=="REELS" else "VIDEO"
        params["video_url"]=media_url
        params["share_to_feed"]="true"
    r=requests.post(f"{host}/{version}/{account}/media",data=params,timeout=60); r.raise_for_status()
    creation_id=r.json()["id"]
    # Poll container status before publishing.
    for _ in range(30):
        q=requests.get(f"{host}/{version}/{creation_id}",
            params={"fields":"status_code","access_token":token},timeout=30)
        q.raise_for_status()
        status=q.json().get("status_code")
        if status=="FINISHED": break
        if status=="ERROR": raise RuntimeError("Instagram media processing failed.")
        time.sleep(10)
    else: raise TimeoutError("Instagram media processing timed out.")
    p=requests.post(f"{host}/{version}/{account}/media_publish",
        data={"creation_id":creation_id,"access_token":token},timeout=60)
    p.raise_for_status()
    return p.json().get("id")
