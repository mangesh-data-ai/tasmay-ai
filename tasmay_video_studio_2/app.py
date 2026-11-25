import json, re, shutil, subprocess
from pathlib import Path
import streamlit as st
import pandas as pd
from PIL import Image

from studio.config import ROOT, CHARACTERS, EPISODES, env
from studio.llm import LLM
from studio.story import create_story, create_character_profile
from studio.images import gemini_image, character_prompt, scene_prompt
from studio.audio import tts, create_ambient_music
from studio.video import render_episode
from studio.subtitles import create_srt
from studio.thumbnail import make_thumbnail
from studio.trends import youtube_search, youtube_most_popular, google_trends_unofficial, rss_news
from studio.publishing import upload_youtube, publish_instagram

st.set_page_config(page_title="Tasmay Stories Studio",page_icon="🎬",layout="wide")
st.title("🎬 Tasmay Stories — AI Video Generation Studio")
st.caption("Decoupled production workspace • Character library • Stories • Voice • Video • Trends • Publishing")

def slug(s):
    s=re.sub(r"[^\w\-]+","-",s.strip(),flags=re.UNICODE)
    return s.strip("-")[:60] or "episode"

def json_write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")

def load_json(path,default=None):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return default

def character_dirs():
    return sorted([p for p in CHARACTERS.iterdir() if p.is_dir()])

def episode_dirs():
    return sorted([p for p in EPISODES.iterdir() if p.is_dir()],reverse=True)

def make_episode_folder(story):
    p=EPISODES/slug(story["title"]); p.mkdir(parents=True,exist_ok=True)
    (p/"scene_images").mkdir(exist_ok=True); (p/"voice").mkdir(exist_ok=True)
    return p

def get_llm(provider):
    return LLM(provider)

with st.sidebar:
    st.header("Studio settings")
    provider=st.selectbox("Text LLM",["gemini","openai-compatible"],index=0 if env("LLM_PROVIDER","gemini")=="gemini" else 1)
    st.caption("Configure keys in .env. Restart Streamlit after editing.")
    st.divider()
    st.markdown("**Provider status**")
    st.write("Gemini key:", "configured" if env("GEMINI_API_KEY") else "missing")
    st.write("YouTube API key:", "configured" if env("YOUTUBE_API_KEY") else "missing")
    st.write("Veo project:", "configured" if env("GOOGLE_CLOUD_PROJECT") else "not configured")
    st.write("Instagram:", "configured" if env("INSTAGRAM_ACCESS_TOKEN") and env("INSTAGRAM_ACCOUNT_ID") else "not configured")

tabs=st.tabs(["🎭 Character Library","📖 Story Studio","🎥 Production","📈 Trends & Keywords","📰 AI News Desk","🚀 Publish","📂 Projects"])

with tabs[0]:
    st.subheader("Character library")
    st.write("Every character has a dedicated directory containing its profile, reference art, prompt history and variations.")
    c1,c2=st.columns(2)
    with c1:
        name=st.text_input("Character name",placeholder="Dhagu")
        idea=st.text_area("Character idea",placeholder="A tiny fluffy cloud who is brave, gentle and curious.")
        style=st.selectbox("Art style",["Premium cinematic 3D animation","Cute stylised 3D animation","Watercolour storybook","2D hand-drawn animation"])
        if st.button("Generate character profile",type="primary"):
            try:
                with st.spinner("Designing character..."):
                    profile=create_character_profile(name,idea,style,get_llm(provider))
                folder=CHARACTERS/slug(name); folder.mkdir(parents=True,exist_ok=True)
                json_write(folder/"profile.json",profile)
                (folder/"prompts.txt").write_text(profile.get("character_prompt",""),encoding="utf-8")
                st.session_state["new_character_folder"]=str(folder)
                st.success(f"Created character directory: {folder}")
                st.json(profile)
            except Exception as e: st.error(str(e))
    with c2:
        st.markdown("**Generate / refresh character reference art**")
        dirs=character_dirs()
        if dirs:
            selected=st.selectbox("Character folder",dirs,format_func=lambda p:p.name)
            prof=load_json(selected/"profile.json",{})
            if st.button("Generate character reference image"):
                try:
                    out=selected/"reference.png"
                    with st.spinner("Generating reference sheet..."):
                        gemini_image(character_prompt(prof),out)
                    st.image(str(out),caption=selected.name)
                    st.success("Reference image saved.")
                except Exception as e: st.error(str(e))
        else: st.info("Create your first character on the left.")
    st.divider()
    dirs=character_dirs()
    if dirs:
        cols=st.columns(3)
        for i,d in enumerate(dirs):
            with cols[i%3]:
                st.markdown(f"**{d.name}**")
                p=d/"reference.png"
                if p.exists(): st.image(str(p),use_container_width=True)
                prof=load_json(d/"profile.json",{})
                st.caption(prof.get("role","Character profile"))
                with st.expander("View profile"):
                    st.json(prof)

with tabs[1]:
    st.subheader("Story generation")
    a,b,c=st.columns(3)
    with a: topic=st.text_input("Story idea",value="A tiny cloud helps a lost star find its way home")
    with b: language=st.selectbox("Narration language",["Marathi","Hindi","English"])
    with c: age=st.selectbox("Target age",["2-4 years","3-7 years","5-9 years"])
    d,e,f=st.columns(3)
    with d: count=st.slider("Number of scenes",4,16,8)
    with e: genre=st.selectbox("Story type",["moral adventure","bedtime story","learning and discovery","funny friendship","science and innovation"])
    with f: use_cast=st.checkbox("Use saved character library",value=True)
    if st.button("✨ Generate complete story + metadata",type="primary"):
        try:
            with st.spinner("Writing story, dialogue, visual prompts, metadata and Reel script..."):
                story=create_story(topic,language,age,count,genre,get_llm(provider))
            if use_cast:
                saved=[]
                for d in character_dirs():
                    p=load_json(d/"profile.json")
                    if p: saved.append(p)
                if saved:
                    # Use saved cast only when story character name overlaps; otherwise append references as available cast guidance.
                    story["saved_character_library"]=[{"name":x.get("name"),"visual_description":x.get("visual_description")} for x in saved]
            folder=make_episode_folder(story)
            json_write(folder/"story.json",story)
            st.session_state["active_episode"]=str(folder)
            st.session_state["active_story"]=story
            st.success(f"Story saved to {folder}")
        except Exception as e: st.error(str(e))
    story=st.session_state.get("active_story")
    if story:
        st.markdown(f"### {story.get('title')}")
        st.write(story.get("synopsis",""))
        st.info("Moral: "+story.get("moral",""))
        with st.expander("Full story JSON / scene prompts"):
            st.json(story)
        st.download_button("Download story JSON",json.dumps(story,ensure_ascii=False,indent=2),file_name="story.json")

with tabs[2]:
    st.subheader("Episode production")
    eps=episode_dirs()
    active=st.session_state.get("active_episode")
    if active and Path(active).exists(): ep=Path(active)
    elif eps: ep=st.selectbox("Select episode",eps,format_func=lambda p:p.name)
    else: ep=None
    if ep:
        story=load_json(ep/"story.json",{})
        st.write(f"**Episode:** {story.get('title',ep.name)}")
        st.caption("Generation steps are separate. You can rerun one step without recreating the whole episode.")
        chars=story.get("characters",[])
        char_refs=[]
        for cdata in chars:
            folder=CHARACTERS/slug(cdata["name"])
            ref=folder/"reference.png"
            if ref.exists(): char_refs.append(ref)
        left,right=st.columns(2)
        with left:
            if st.button("1. Generate scene keyframes"):
                try:
                    with st.spinner("Generating scene images..."):
                        for i,scene in enumerate(story["scenes"],1):
                            out=ep/"scene_images"/f"scene_{i:02d}.png"
                            refs=char_refs[:4]
                            gemini_image(scene_prompt(scene,chars,"16:9"),out,refs)
                    st.success("Scene keyframes generated.")
                except Exception as e: st.error(str(e))
        with right:
            provider_video=st.selectbox("Video engine",["kenburns","veo"],index=0)
            st.caption("Veo requires Vertex AI project, billing and ADC. Ken Burns is local/free.")
        st.divider()
        v1,v2,v3=st.columns(3)
        with v1:
            tts_voice=st.selectbox("TTS voice",["mr-IN-AarohiNeural","mr-IN-ManoharNeural","hi-IN-SwaraNeural","hi-IN-MadhurNeural","en-US-JennyNeural","en-US-GuyNeural"])
            if st.button("2. Generate narration TTS"):
                try:
                    voice_dir=ep/"voice"; voice_dir.mkdir(exist_ok=True)
                    for i,s in enumerate(story["scenes"],1):
                        text=(s.get("narration","")+" "+s.get("dialogue","")).strip()
                        if text: tts(text,voice_dir/f"scene_{i:02d}.mp3",tts_voice)
                    st.success("Voice tracks generated.")
                except Exception as e: st.error(str(e))
        with v2:
            upload=st.file_uploader("Or upload your recorded voice (MP3/WAV/M4A)",type=["mp3","wav","m4a"],key="voiceupload")
            if upload and st.button("Save recorded voice"):
                dest=ep/("recorded_voice"+Path(upload.name).suffix)
                dest.write_bytes(upload.getvalue())
                st.success(f"Saved: {dest.name}")
        with v3:
            if st.button("3. Generate original ambient music"):
                try:
                    create_ambient_music(ep/"background_music.wav",duration=360)
                    st.success("Music generated.")
                except Exception as e: st.error(str(e))
        st.divider()
        if st.button("4. Generate subtitles (SRT)"):
            try:
                create_srt(story["scenes"],ep/"subtitles.srt")
                st.success("SRT created.")
            except Exception as e: st.error(str(e))
        if st.button("5. Render YouTube + Reel videos",type="primary"):
            try:
                images=[ep/"scene_images"/f"scene_{i:02d}.png" for i in range(1,len(story["scenes"])+1)]
                missing=[p for p in images if not p.exists()]
                if missing: raise RuntimeError("Generate all scene keyframes first.")
                voice=next(iter(ep.glob("recorded_voice.*")),None)
                tts_paths=sorted((ep/"voice").glob("scene_*.mp3")) if (ep/"voice").exists() else []
                music=ep/"background_music.wav"
                music=music if music.exists() else None
                srt=ep/"subtitles.srt"
                for fmt in ("youtube","reels"):
                    result=render_episode(story["scenes"],images,ep,fmt,voice,tts_paths,music,provider_video,srt)
                    st.success(f"Created {result}")
            except Exception as e: st.error(str(e))
        thumb_bg=next(iter((ep/"scene_images").glob("scene_*.png")),None)
        if thumb_bg:
            if st.button("6. Generate YouTube thumbnail + social copy"):
                try:
                    make_thumbnail(thumb_bg,story.get("title",ep.name),ep/"thumbnail.jpg")
                    meta={k:story.get(k) for k in ("youtube_title","description","youtube_tags","instagram_caption","hashtags","shorts_hook","reel_script")}
                    json_write(ep/"social_metadata.json",meta)
                    st.image(str(ep/"thumbnail.jpg"),width=500)
                    st.success("Thumbnail and social metadata created.")
                except Exception as e: st.error(str(e))
    else:
        st.info("Generate a story first.")

with tabs[3]:
    st.subheader("Trend and keyword research")
    q=st.text_input("Keyword / niche",value="Marathi kids stories")
    region=st.selectbox("Region",["IN","US","GB","AE"],index=0)
    n=st.slider("Results",5,30,15)
    x,y=st.columns(2)
    with x:
        if st.button("Search YouTube videos"):
            try:
                rows=youtube_search(q,region,n)
                st.session_state["yt_trends"]=rows
            except Exception as e: st.error(str(e))
    with y:
        if st.button("Show regional trending videos"):
            try: st.session_state["yt_trends"]=youtube_most_popular(region,n)
            except Exception as e: st.error(str(e))
    if st.session_state.get("yt_trends"):
        df=pd.DataFrame(st.session_state["yt_trends"])
        st.dataframe(df,use_container_width=True)
        if st.button("Generate keyword/content ideas from results"):
            try:
                prompt="Analyse these YouTube trend titles. Suggest 20 original keywords, 10 video ideas, 5 Reel hooks and title patterns. Do not claim views predict future success. Data:\n"+df.to_json(orient="records",force_ascii=False)
                st.markdown(get_llm(provider).generate_text(prompt))
            except Exception as e: st.error(str(e))
    st.caption("Google Trends note: pytrends is an unofficial interface and can break. Google's official Trends API is currently an alpha with access by application.")
    gt=st.text_input("Google Trends keyword",value="kids stories")
    if st.button("Fetch Google Trends interest (unofficial pytrends)"):
        try:
            data=google_trends_unofficial(gt,geo=region)
            st.dataframe(pd.DataFrame(data),use_container_width=True)
        except Exception as e: st.error(f"Google Trends request failed: {e}")

with tabs[4]:
    st.subheader("AI news and innovation desk")
    nq=st.text_input("News topic",value="generative AI video models and creator tools")
    nl=st.selectbox("News language",["English","Marathi"])
    if st.button("Fetch latest headlines + create digest"):
        try:
            items=rss_news(nq,"mr" if nl=="Marathi" else "en",15)
            st.session_state["news_items"]=items
            prompt=("Summarise these recent headlines into a concise creator-focused innovation digest. "
                    "Separate confirmed facts from implications. Include headline source URLs inline. "
                    "Do not invent facts or claim an article says more than its headline. "
                    +json.dumps(items,ensure_ascii=False))
            digest=get_llm(provider).generate_text(prompt)
            st.session_state["news_digest"]=digest
        except Exception as e: st.error(str(e))
    if st.session_state.get("news_digest"):
        st.markdown(st.session_state["news_digest"])
        with st.expander("Source headlines"):
            for item in st.session_state.get("news_items",[]):
                st.markdown(f"- [{item['title']}]({item['link']}) — {item['published']}")

with tabs[5]:
    st.subheader("Publishing centre")
    eps=episode_dirs()
    if eps:
        ep=st.selectbox("Episode to publish",eps,format_func=lambda p:p.name,key="publish_ep")
        story=load_json(ep/"story.json",{})
        st.write("**Review title and description before publishing.**")
        yt_title=st.text_input("YouTube title",value=story.get("youtube_title",story.get("title",""))[:100])
        desc=st.text_area("Description",value=story.get("description",""))
        tags=st.text_input("Tags, comma separated",value=",".join(story.get("youtube_tags",[])))
        privacy=st.selectbox("YouTube visibility",["private","unlisted","public"],index=0)
        ytfile=ep/f"{ep.name}_youtube.mp4"
        thumb=ep/"thumbnail.jpg"
        if st.button("Upload to YouTube"):
            try:
                if not ytfile.exists(): raise RuntimeError("YouTube video file not found. Render it first.")
                url=upload_youtube(ytfile,yt_title,desc,[x.strip() for x in tags.split(",") if x.strip()],privacy,thumb if thumb.exists() else None)
                st.success(f"Uploaded: {url}")
            except Exception as e: st.error(str(e))
        st.divider()
        st.markdown("**Instagram publishing**")
        st.warning("Requires an Instagram professional account, publishing permissions and a publicly accessible media URL. Do not publish until you have reviewed the content.")
        media_url=st.text_input("Public HTTPS URL of your Reel/video (e.g. hosted on your own CDN)")
        caption=st.text_area("Instagram caption",value=story.get("instagram_caption","")+"\n\n"+" ".join(story.get("hashtags",[])))
        if st.button("Publish Instagram Reel"):
            try:
                if not media_url.startswith("https://"): raise RuntimeError("Provide a public HTTPS media URL.")
                result=publish_instagram(media_url,caption,media_type="REELS")
                st.success(f"Instagram media published. ID: {result}")
            except Exception as e: st.error(str(e))
    else: st.info("Create and render an episode first.")

with tabs[6]:
    st.subheader("Project folders")
    st.markdown(f"**Character library:** `{CHARACTERS}`")
    st.markdown(f"**Episodes:** `{EPISODES}`")
    st.markdown("Each character directory stores profile.json, prompts.txt and reference.png. Each episode stores story.json, scene images, voice tracks, music, SRT, thumbnail, social metadata and rendered MP4s.")
    for ep in episode_dirs():
        with st.expander(ep.name):
            for p in sorted(ep.rglob("*")):
                if p.is_file(): st.write(str(p.relative_to(ep)))
