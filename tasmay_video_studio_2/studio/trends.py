import os, requests, feedparser
from datetime import datetime, timezone
from studio.config import env

def youtube_search(query, region="IN", max_results=15, api_key=None):
    key=api_key or env("YOUTUBE_API_KEY")
    if not key: raise RuntimeError("Set YOUTUBE_API_KEY in .env for YouTube trend research.")
    r=requests.get("https://www.googleapis.com/youtube/v3/search",params={
        "part":"snippet","q":query,"type":"video","order":"viewCount","regionCode":region,
        "maxResults":min(max_results,50),"key":key
    },timeout=30); r.raise_for_status()
    items=r.json().get("items",[])
    ids=",".join(x["id"]["videoId"] for x in items if x.get("id",{}).get("videoId"))
    stats={}
    if ids:
        s=requests.get("https://www.googleapis.com/youtube/v3/videos",params={
            "part":"statistics,contentDetails","id":ids,"key":key
        },timeout=30); s.raise_for_status()
        stats={x["id"]:x.get("statistics",{}) for x in s.json().get("items",[])}
    out=[]
    for x in items:
        vid=x.get("id",{}).get("videoId")
        sn=x.get("snippet",{})
        out.append({"title":sn.get("title"),"channel":sn.get("channelTitle"),
                    "published":sn.get("publishedAt"),"url":f"https://youtube.com/watch?v={vid}",
                    "views":int(stats.get(vid,{}).get("viewCount",0)),"video_id":vid})
    return sorted(out,key=lambda x:x["views"],reverse=True)

def youtube_most_popular(region="IN", max_results=20):
    key=env("YOUTUBE_API_KEY")
    if not key: raise RuntimeError("Set YOUTUBE_API_KEY in .env")
    r=requests.get("https://www.googleapis.com/youtube/v3/videos",params={
        "part":"snippet,statistics","chart":"mostPopular","regionCode":region,
        "maxResults":min(max_results,50),"key":key
    },timeout=30); r.raise_for_status()
    return [{"title":x["snippet"]["title"],"channel":x["snippet"]["channelTitle"],
             "views":int(x.get("statistics",{}).get("viewCount",0)),
             "url":"https://youtube.com/watch?v="+x["id"]} for x in r.json().get("items",[])]

def google_trends_unofficial(keyword, geo="IN", timeframe="now 7-d"):
    # pytrends is an unofficial interface; Google Trends API alpha is access-controlled.
    from pytrends.request import TrendReq
    py=TrendReq(hl="en-US",tz=330)
    py.build_payload([keyword],timeframe=timeframe,geo=geo)
    df=py.interest_over_time()
    if df.empty: return []
    return [{"date":str(i),"interest":int(row[keyword])} for i,row in df.iterrows()]

def rss_news(query="AI innovation", language="en", limit=15):
    # Google News RSS search feed. Results are headlines + source links, not a full-text archive.
    import urllib.parse
    hl="mr" if language=="mr" else "en-US"
    gl="IN"; ceid="IN:mr" if language=="mr" else "IN:en"
    url="https://news.google.com/rss/search?q="+urllib.parse.quote(query)+"&hl="+hl+"&gl="+gl+"&ceid="+ceid
    feed=feedparser.parse(url)
    out=[]
    for e in feed.entries[:limit]:
        out.append({"title":e.get("title",""),"link":e.get("link",""),
                    "published":e.get("published",""),"source":e.get("source",{}).get("title","Google News RSS")})
    return out
