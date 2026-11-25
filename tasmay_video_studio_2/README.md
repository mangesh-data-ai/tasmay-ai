# Tasmay Stories — Decoupled AI Video Studio

A modular Windows-first production studio with a Streamlit dashboard.

## Capabilities

- **Character library:** create character profiles from prompts; each character gets a dedicated folder, reusable design bible, prompt and reference image.
- **Story studio:** generate original Hindi, Marathi or English stories, scenes, dialogue, narration, visual prompts, moral, YouTube metadata, Reel hook and short-form script.
- **Production:** generate scene keyframes using Gemini image generation with saved character reference images; generate Marathi/Hindi/English TTS; upload your own narration; create original procedural ambient music; generate SRT subtitles; render landscape and vertical MP4s.
- **Thumbnail and social copy:** branded 1280x720 thumbnail, title, description, captions, hashtags and Shorts/Reels hooks.
- **Trend research:** YouTube search by keyword, regional most-popular videos, views and keyword ideation; optional Google Trends interest via `pytrends`.
- **AI news desk:** fetch Google News RSS headlines for a query and create an AI digest with source links.
- **Publishing:** optional YouTube OAuth upload and thumbnail; optional Instagram Graph API Reel publishing from a publicly accessible HTTPS media URL.

## Architecture: providers are decoupled

- `studio/llm.py`: Gemini or any OpenAI-compatible LLM.
- `studio/images.py`: Gemini image generation; takes optional character reference images.
- `studio/video.py`: provider interface with local Ken Burns renderer and Google Veo adapter. Add Kling/Runway/Replicate adapters here without changing story, voice, or publishing code.
- `studio/audio.py`: Edge TTS and procedural music.
- `studio/trends.py`: YouTube Data API, pytrends, Google News RSS.
- `studio/publishing.py`: YouTube Data API and Instagram Graph API.
- `app.py`: Streamlit dashboard and workflow orchestration.

## Setup on Windows

1. Install Python 3.11 or newer.
2. Install FFmpeg and add its `bin` directory to PATH. Test `ffmpeg -version`.
   - Windows builds: https://www.gyan.dev/ffmpeg/builds/
3. Extract the ZIP and open PowerShell in the project directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

4. Add your Gemini API key to `.env`:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=YOUR_KEY
GEMINI_TEXT_MODEL=gemini-2.5-flash
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
```

5. Launch:

```powershell
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal (usually http://localhost:8501).

## First test

- Generate one character profile in Character Library.
- Generate its reference image.
- Create a 4-scene story.
- Generate scene keyframes.
- Generate TTS and music.
- Generate subtitles.
- Render both YouTube and Reel formats.

Image and video generation are metered services and may require paid API access. The Ken Burns renderer is local and does not require a video-generation API.

## LLM alternatives

In `.env`:

```env
LLM_PROVIDER=openai-compatible
LLM_API_KEY=...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
```

This interface is compatible with providers that expose the OpenAI chat-completions API (for example OpenAI, OpenRouter, Groq or local Ollama). Use the provider's own endpoint/model names.

## Character directories

Example:
```
data/
  characters/
    dhagu/
      profile.json
      prompts.txt
      reference.png
    chamki/
      profile.json
      prompts.txt
      reference.png
  episodes/
    little-cloud/
      story.json
      scene_images/
      voice/
      background_music.wav
      subtitles.srt
      thumbnail.jpg
      social_metadata.json
      *_youtube.mp4
      *_reels.mp4
```

The character image is supplied as a reference input when scene images are generated. Visual consistency still needs human review; generative models can change small details between images.

## Video provider setup

### Local / free fallback
`VIDEO_PROVIDER=kenburns` or choose Ken Burns in the UI. This creates a camera-motion video from generated keyframes. It is not full 3D animation.

### Google Veo
Requires Google Cloud project, Vertex AI API enabled, billing, model access and ADC. A Gemini API key alone is not enough.

```powershell
gcloud auth application-default login
```

Set:
```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
VEO_MODEL=veo-3.1-generate-001
```
Select Veo in Production. Check current pricing, quotas, region/model availability first.

### Add another video provider
Implement `VideoProvider.animate(image_path, prompt, output_path, aspect)` in `studio/video.py`. Keep the method contract and the rest of the pipeline remains unchanged. Provider APIs (Kling, Runway, etc.) have separate credentials, request schemas and billing.

## YouTube trends and publishing

- Enable YouTube Data API v3 in Google Cloud and create an API key for public search/trending research. Add `YOUTUBE_API_KEY`.
- YouTube search consumes API quota; check your current quota in Google Cloud.
- For upload, create an OAuth 2.0 Desktop client and save the downloaded JSON as `client_secrets.json` in project root. First upload opens browser consent and stores `youtube_token.json`.
- First test with visibility `private`. Review metadata and child-audience designation before publishing.

## Google Trends caveat

Google's official Trends API is currently an alpha with limited access by application. The included `pytrends` connector is unofficial and can be rate-limited or break. It is optional; YouTube Data API trend research still works independently.

## Instagram publishing caveat

- Publishing requires an eligible Instagram professional account and Meta app permissions/token.
- For Reels, the Graph API fetches a publicly accessible HTTPS media URL. A local file path is not sufficient.
- Set `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_ACCOUNT_ID` and `META_GRAPH_VERSION`.
- This app publishes only after you press the publish button. Review the final caption and media first.
- Personal accounts and unsupported permissions cannot use this publishing flow.

## Voice, subtitles and music

- TTS uses Edge TTS voices; voice IDs are configurable in `.env` or the UI. Confirm the provider's current usage/licensing terms for commercial publishing.
- You can upload your own narration MP3/WAV/M4A.
- SRT subtitles are generated from the story script. For exact word-level subtitles from your own voice, install `faster-whisper` and add an ASR workflow (not required for scene-level subtitles).
- Ambient music is generated procedurally and is intentionally simple. For a commercial release, use music you composed or properly licensed music.

## Safety and publishing checklist

- Review every story and frame, especially children's content.
- Use original characters and properly licensed music, voices and assets.
- Do not clone another person's voice without permission.
- Set YouTube "Made for Kids" accurately for content directed to children.
- Do not expose a child's private information, location or routine.
- AI news summaries include links to source headlines. Verify the source article before presenting a claim as fact.
- Keep `.env`, OAuth secrets and access tokens private.
