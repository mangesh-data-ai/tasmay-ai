import json, re
from studio.config import env

class LLM:
    """Replaceable text-generation adapter. Providers implement generate_text()."""
    def __init__(self, provider=None):
        self.provider = provider or env("LLM_PROVIDER", "gemini")
        if self.provider == "gemini":
            from google import genai
            key = env("GEMINI_API_KEY")
            if not key:
                raise RuntimeError("Add GEMINI_API_KEY to .env")
            self.client = genai.Client(api_key=key)
            self.model = env("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
        elif self.provider == "openai-compatible":
            from openai import OpenAI
            self.client = OpenAI(
                api_key=env("LLM_API_KEY", "ollama"),
                base_url=env("LLM_BASE_URL", "http://localhost:11434/v1"),
            )
            self.model = env("LLM_MODEL", "llama3.1")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate_text(self, prompt: str) -> str:
        if self.provider == "gemini":
            r = self.client.models.generate_content(model=self.model, contents=prompt)
            return r.text or ""
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role":"user","content":prompt}],
            temperature=0.7,
        )
        return r.choices[0].message.content or ""

    def generate_json(self, prompt: str) -> dict:
        if self.provider == "gemini":
            from google.genai import types
            r = self.client.models.generate_content(
                model=self.model, contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            raw = r.text or ""
        else:
            r = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role":"system","content":"Return valid JSON only."},
                          {"role":"user","content":prompt}],
                response_format={"type":"json_object"},
                temperature=0.7,
            )
            raw = r.choices[0].message.content or ""
        raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
        a, b = raw.find("{"), raw.rfind("}")
        if a < 0 or b < a:
            raise ValueError("Model did not return JSON: " + raw[:1200])
        return json.loads(raw[a:b+1])
