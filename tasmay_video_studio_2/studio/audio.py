from pathlib import Path
import asyncio, math, wave
import numpy as np
from studio.config import env

def tts(text, output: Path, voice=None):
    import edge_tts
    async def go():
        c=edge_tts.Communicate(
            text=text, voice=voice or env("TTS_VOICE","mr-IN-AarohiNeural"),
            rate=env("TTS_RATE","+0%"), volume=env("TTS_VOLUME","+0%")
        )
        await c.save(str(output))
    asyncio.run(go())
    return output

def available_voices():
    import asyncio, edge_tts
    return asyncio.run(edge_tts.list_voices())

def create_ambient_music(output: Path, duration=240, mood="gentle"):
    """Original procedural ambient pad. Use licensed music for a professional release."""
    sr=44100
    chords=[[261.63,329.63,392.0],[349.23,440.0,523.25],[220.0,261.63,329.63],[392.0,493.88,587.33]]
    n=int(duration*sr); t=np.arange(n,dtype=np.float32)/sr
    audio=np.zeros(n,dtype=np.float32)
    step=16.0
    for idx,start in enumerate(np.arange(0,duration,step)):
        mask=(t>=start)&(t<min(start+step,duration))
        local=t[mask]-start
        part=np.zeros_like(local)
        for j,f in enumerate(chords[idx%len(chords)]):
            part += np.sin(2*np.pi*f*local+j*.6)/(j+1)
            part += .15*np.sin(2*np.pi*(f/2)*local+j)
        fade=np.minimum(1,local/2)*np.minimum(1,(step-local)/2)
        audio[mask]=part*fade
    audio=np.clip(audio/(np.max(np.abs(audio))+.0001)*.12,-1,1)
    pcm=(np.stack([audio,audio],axis=1)*32767).astype(np.int16)
    output.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(output),"wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
    return output
