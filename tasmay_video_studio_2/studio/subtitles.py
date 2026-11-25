from pathlib import Path
import re

def _stamp(s):
    ms=int(max(0,s)*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); sec,ms=divmod(ms,1000)
    return f"{h:02}:{m:02}:{sec:02},{ms:03}"

def create_srt(scenes, output: Path):
    cursor=0.0; rows=[]
    for i,s in enumerate(scenes,1):
        duration=float(s.get("duration",7))
        text=(s.get("narration","")+" "+s.get("dialogue","")).strip()
        rows += [str(i),f"{_stamp(cursor)} --> {_stamp(cursor+duration)}",text,""]
        cursor += duration
    output.write_text("\n".join(rows),encoding="utf-8")
    return output

def transcribe_audio(audio_path, output_srt: Path, model_size="small"):
    """Optional local ASR. pip install faster-whisper. No audio uploaded to a cloud ASR."""
    from faster_whisper import WhisperModel
    model=WhisperModel(model_size,device="cpu",compute_type="int8")
    segments,_=model.transcribe(str(audio_path),vad_filter=True)
    rows=[]
    for i,s in enumerate(segments,1):
        rows += [str(i),f"{_stamp(s.start)} --> {_stamp(s.end)}",s.text.strip(),""]
    output_srt.write_text("\n".join(rows),encoding="utf-8")
    return output_srt
