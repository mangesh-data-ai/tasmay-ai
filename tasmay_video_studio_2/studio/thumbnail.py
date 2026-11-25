from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

def make_thumbnail(background: Path, title: str, output: Path, brand="TASMAy STORIES"):
    im=Image.open(background).convert("RGB").resize((1280,720))
    # dark translucent lower gradient panel for legible text
    overlay=Image.new("RGBA",im.size,(0,0,0,0)); d=ImageDraw.Draw(overlay)
    d.rectangle((0,470,1280,720),fill=(0,0,0,145))
    im=Image.alpha_composite(im.convert("RGBA"),overlay).convert("RGB")
    draw=ImageDraw.Draw(im)
    try:
        font=ImageFont.truetype("arialbd.ttf",66)
        small=ImageFont.truetype("arial.ttf",28)
    except Exception:
        font=ImageFont.load_default(); small=ImageFont.load_default()
    # wrap title
    words=title.split(); lines=[]; line=""
    for word in words:
        test=(line+" "+word).strip()
        if draw.textbbox((0,0),test,font=font)[2] > 1160 and line:
            lines.append(line); line=word
        else: line=test
    if line: lines.append(line)
    y=485
    for line in lines[:2]:
        draw.text((60,y),line,font=font,fill="white",stroke_width=2,stroke_fill="#26324a")
        y += 76
    draw.text((65,675),brand,font=small,fill=(255,225,140))
    output.parent.mkdir(parents=True,exist_ok=True); im.save(output,quality=94)
    return output
