from studio.llm import LLM

LANGS = {"Hindi":"Hindi (Devanagari)", "Marathi":"Marathi (Devanagari)", "English":"English"}
def create_story(topic, language="Marathi", age="3-7 years", scenes=8, genre="moral adventure", llm=None):
    llm = llm or LLM()
    prompt = f"""
Act as an original children's animation showrunner. Write an original, age-safe story.
Seed/topic: {topic}
Spoken language: {LANGS.get(language, language)}
Age group: {age}; genre: {genre}; exactly {scenes} scenes.
Return valid JSON:
{{
"title": "title in spoken language",
"moral": "one-sentence moral",
"synopsis": "short synopsis",
"description": "YouTube description",
"characters": [
{{"name":"character name","role":"role","visual_description":"detailed stable visual appearance in English: species/body shape, colours, face, eyes, clothing, accessories, proportions","personality":"traits"}}
],
"scenes": [
{{"number":1,"title":"scene title","narration":"natural narration in requested language",
"dialogue":"dialogue in requested language or empty",
"visual_prompt":"English cinematic visual prompt; one clear action; include named characters and setting",
"camera":"camera instruction in English","duration":7,
"sound_effects":["sound idea"],"music_mood":"short mood"}}
],
"youtube_title":"SEO-friendly title in requested language",
"youtube_tags":["tag1","tag2"],
"instagram_caption":"short social caption in requested language",
"hashtags":["#tag1","#tag2"],
"shorts_hook":"first 2-second hook in requested language",
"reel_script":"30-45 second condensed story in requested language"
}}
Rules: fully original; no copyrighted franchise characters; no scary violence; positive resolution.
Use Devanagari for Hindi/Marathi. Visual prompts in English for image/video models.
Preserve identical character appearance across scenes. No words, signs, logos, subtitles in generated images.
Keep the narration coherent, speakable and suitable for voice-over.
"""
    data = llm.generate_json(prompt)
    if len(data.get("scenes", [])) != scenes:
        raise ValueError("Story generator returned an unexpected number of scenes. Try again.")
    return data

def create_character_profile(name, idea, art_style="premium cinematic 3D animation", llm=None):
    llm = llm or LLM()
    p = f"""
Design an original recurring children's animation character. Name: {name}. Concept: {idea}.
Return JSON with name, role, visual_description, personality, voice_personality,
character_prompt, negative_prompt, palette (array), consistency_rules (array).
The visual_description must be very specific and stable: body silhouette, height/proportions,
materials, exact colours, eye shape/colour, face, clothes/accessories, distinguishing features.
Art direction: {art_style}. Avoid resemblance to existing copyrighted characters.
character_prompt must request a single full-body character turnaround/reference sheet:
front, side, 3/4 views and 3 facial expressions; consistent design; clean neutral background;
no text, no watermark. Return JSON only.
"""
    return llm.generate_json(p)
