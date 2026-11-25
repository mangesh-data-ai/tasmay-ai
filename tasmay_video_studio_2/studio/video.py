from pathlib import Path
import os, shutil, subprocess, time
from studio.config import env

def require_ffmpeg():
    if not shutil.which("ffmpeg"):
        raise RuntimeError("Install FFmpeg and add ffmpeg.exe to Windows PATH.")

def run(cmd):
    subprocess.run([str(x) for x in cmd], check=True)

class VideoProvider:
    """Provider interface: implement animate(image_path, prompt, output_path, aspect)."""
    name = "base"
    def animate(self, image_path: Path, prompt: str, output_path: Path, aspect="16:9"):
        raise NotImplementedError

class KenBurnsProvider(VideoProvider):
    name = "kenburns"
    def animate(self, image_path, prompt, output_path, aspect="16:9"):
        # Renderer handles duration/format. This provider is intentionally a no-op marker.
        return None

class VeoProvider(VideoProvider):
    name = "veo"
    def animate(self, image_path, prompt, output_path, aspect="16:9"):
        project = env("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise RuntimeError("Set GOOGLE_CLOUD_PROJECT and configure gcloud ADC.")
        from google import genai
        from google.genai import types
        client = genai.Client(vertexai=True, project=project, location=env("GOOGLE_CLOUD_LOCATION","global"))
        image = types.Image.from_file(location=str(image_path))
        op = client.models.generate_videos(
            model=env("VEO_MODEL","veo-3.1-generate-001"),
            source=types.GenerateVideosSource(prompt=prompt, image=image),
            config=types.GenerateVideosConfig(
                number_of_videos=1, duration_seconds=5, aspect_ratio=aspect,
                enhance_prompt=True
            )
        )
        while not op.done:
            time.sleep(15)
            op = client.operations.get(op)
        video = op.response.generated_videos[0].video
        output_path.parent.mkdir(parents=True, exist_ok=True)
        video.save(str(output_path))
        return output_path

def make_still_clip(image_path, out_path, duration, width, height, index, fps=30):
    frames = max(1, int(duration*fps))
    zoom = "min(zoom+0.0007,1.08)" if index % 2 else "max(zoom-0.0007,1.0)"
    vf = (f"scale={width}:{height}:force_original_aspect_ratio=increase,"
          f"crop={width}:{height},zoompan=z='{zoom}':d={frames}:s={width}x{height}:fps={fps},"
          "format=yuv420p")
    run(["ffmpeg","-y","-loop","1","-i",image_path,"-t",duration,"-vf",vf,
         "-r",fps,"-an","-c:v","libx264","-preset","medium","-crf","19",out_path])

def render_episode(scenes, image_paths, episode_dir, fmt, narration_path=None, tts_paths=None,
                   music_path=None, provider_name="kenburns", subtitle_path=None):
    require_ffmpeg()
    width,height = (1920,1080) if fmt=="youtube" else (1080,1920)
    aspect = "16:9" if fmt=="youtube" else "9:16"
    provider = VeoProvider() if provider_name=="veo" else KenBurnsProvider()
    clips=[]
    clip_dir=episode_dir/f"clips_{fmt}"
    clip_dir.mkdir(parents=True,exist_ok=True)
    for i,(scene,img) in enumerate(zip(scenes,image_paths),1):
        duration=float(scene.get("duration",7))
        out=clip_dir/f"scene_{i:03d}.mp4"
        if provider_name=="veo":
            try:
                generated=provider.animate(img,scene.get("visual_prompt",""),out,aspect)
                fitted=clip_dir/f"fit_{i:03d}.mp4"
                run(["ffmpeg","-y","-i",generated,"-t",duration,
                     "-vf",f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1",
                     "-an","-c:v","libx264","-preset","medium","-crf","19",fitted])
                out=fitted
            except Exception as e:
                print(f"Veo scene {i} failed; using animated still: {e}")
                make_still_clip(img,out,duration,width,height,i)
        else:
            make_still_clip(img,out,duration,width,height,i)
        clips.append(out)
    concat=clip_dir/"concat.txt"
    concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in clips),encoding="utf-8")
    silent=clip_dir/"silent.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat,"-c","copy",silent])

    # TTS segments are concatenated into a single track by ffmpeg.
    voice=narration_path
    if not voice and tts_paths:
        voice=episode_dir/"voiceover.mp3"
        listing=episode_dir/"voice_concat.txt"
        listing.write_text("".join(f"file '{Path(p).resolve().as_posix()}'\n" for p in tts_paths),encoding="utf-8")
        run(["ffmpeg","-y","-f","concat","-safe","0","-i",listing,"-c:a","libmp3lame","-q:a","3",voice])
    final=episode_dir/f"{episode_dir.name}_{fmt}.mp4"
    inputs=["-i",silent]
    if voice and Path(voice).exists(): inputs += ["-i",voice]
    if music_path and Path(music_path).exists(): inputs += ["-stream_loop","-1","-i",music_path]
    cmd=["ffmpeg","-y"]+inputs
    if voice and Path(voice).exists() and music_path and Path(music_path).exists():
        cmd += ["-filter_complex","[1:a]volume=1.0[v];[2:a]volume=0.12[m];[v][m]amix=inputs=2:duration=first:dropout_transition=2[a]","-map","0:v","-map","[a]"]
    elif voice and Path(voice).exists():
        cmd += ["-map","0:v","-map","1:a"]
    elif music_path and Path(music_path).exists():
        cmd += ["-map","0:v","-map","1:a"]
    else:
        cmd += ["-map","0:v"]
    cmd += ["-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",final]
    run(cmd)
    return final
