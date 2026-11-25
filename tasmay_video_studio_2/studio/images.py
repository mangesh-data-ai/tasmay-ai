from pathlib import Path
from io import BytesIO
from PIL import Image
from studio.config import env

def gemini_image(prompt: str, output: Path, references=None):
    """Generate one image. Reference images are passed as multimodal inputs when supplied."""
    from google import genai
    from google.genai import types
    key = env("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY missing")
    client = genai.Client(api_key=key)
    model = env("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    contents = [prompt]
    for ref in references or []:
        if ref and Path(ref).exists():
            contents.append(Image.open(ref).convert("RGB"))
    response = client.models.generate_content(
        model=model, contents=contents,
        config=types.GenerateContentConfig(response_modalities=["TEXT","IMAGE"])
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    for part in response.candidates[0].content.parts:
        if getattr(part, "inline_data", None):
            img = Image.open(BytesIO(part.inline_data.data)).convert("RGB")
            img.save(output, quality=95)
            return output
    raise RuntimeError("No image returned by the configured Gemini image model.")

def character_prompt(profile):
    return profile.get("character_prompt") or (
        "Premium 3D animated family film character reference sheet. "
        + profile["visual_description"]
        + " Show front, side and three-quarter views plus happy, sad and surprised expressions. "
          "One consistent character, clean studio background, no text or watermark."
    )

def scene_prompt(scene, characters, aspect="16:9"):
    bible = "\n".join(
        f"{c['name']}: {c.get('visual_description','')}" for c in characters
    )
    return f"""Create a polished {aspect} keyframe for a premium 3D animated children's film.
CHARACTER BIBLE (must follow exactly):
{bible}
ACTION: {scene['visual_prompt']}
CAMERA: {scene.get('camera','cinematic medium shot')}
High-end 3D rendering, expressive faces, rich detailed environment, global illumination,
soft cinematic lighting, physically plausible materials. Preserve character designs.
No captions, written text, logos or watermark."""
