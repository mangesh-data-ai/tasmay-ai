from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
DATA = ROOT / "data"
CHARACTERS = DATA / "characters"
EPISODES = DATA / "episodes"
ASSETS = ROOT / "assets"
for p in (DATA, CHARACTERS, EPISODES, ASSETS):
    p.mkdir(parents=True, exist_ok=True)

def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)
