import asyncio
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import soundfile as sf

# Try importing Kokoro
try:
    from kokoro_onnx import Kokoro
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False

VOICE_PRESETS = {
    "Christopher (Bacon / Male)": "en-US-ChristopherNeural",
    "Jenny (Girl / Cheerful)": "en-US-JennyNeural",
    "Guy (Epic Narrator)": "en-US-GuyNeural",
    "Ana (Energetic Kid)": "en-US-AnaNeural",
    "Eric (Teen / Chill)": "en-US-EricNeural",
    "Aria (Expressive Female)": "en-US-AriaNeural",
    "Ryan (British Pro)": "en-GB-RyanNeural",
    "Sonia (British Girl)": "en-GB-SoniaNeural",
    "Steffan (US Storyteller)": "en-US-SteffanNeural"
}

KOKORO_VOICE_MAP = {
    "en-US-ChristopherNeural": "am_adam",
    "en-US-JennyNeural": "af_bella",
    "en-US-GuyNeural": "am_michael",
    "en-US-AnaNeural": "af_nicole",
    "en-US-EricNeural": "am_fenrir",
    "en-US-AriaNeural": "af_sarah",
    "en-GB-RyanNeural": "am_puck",
    "en-GB-SoniaNeural": "bf_emma",
    "en-US-SteffanNeural": "am_echo",
}

_kokoro_instance = None
def get_kokoro():
    global _kokoro_instance
    if _kokoro_instance is None:
        model_path = "C:/Users/Krishna/Downloads/kokoro/kokoro-v0_19.onnx"
        voices_path = "C:/Users/Krishna/Downloads/kokoro/voices.bin"
        _kokoro_instance = Kokoro(model_path, voices_path)
    return _kokoro_instance

async def _generate_voice_async(
    text: str,
    voice: str,
    output_audio_path: str,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    ref_audio: str = None
) -> List[Dict[str, Any]]:
    
    word_boundaries = []
    
    if voice == "indicf5" or voice.startswith("telugu"):
        from core.tts_indicf5 import generate_indicf5_audio
        try:
            clean_txt = text[:20].encode('ascii', 'replace').decode('ascii')
            print(f"[TTS] Using Neural Telugu TTS: {clean_txt}...")
        except Exception:
            print("[TTS] Using Neural Telugu TTS...")
            
        generate_indicf5_audio(text, ref_audio, "", output_audio_path, voice=voice if voice.startswith("telugu") else "telugu_male_1")
        
        dur = get_audio_duration(output_audio_path)
        words = text.strip().split()
        avg_word_dur = dur / max(1, len(words))
        current = 0.0
        for w in words:
            word_boundaries.append({
                "word": w,
                "start": current,
                "end": current + avg_word_dur
            })
            current += avg_word_dur
            
    elif KOKORO_AVAILABLE and os.path.exists("C:/Users/Krishna/Downloads/kokoro/kokoro-v0_19.onnx"):
        if voice.startswith("am_") or voice.startswith("af_"):
            kokoro_voice = voice
        else:
            kokoro_voice = KOKORO_VOICE_MAP.get(voice, "am_adam")
            
        try:
            print(f"[TTS] Using Kokoro ({kokoro_voice}) for text: {text[:20].encode('utf-8', 'ignore').decode('utf-8')}...")
        except Exception:
            print(f"[TTS] Using Kokoro ({kokoro_voice})")
        kokoro = get_kokoro()
        
        # parse rate
        speed = 1.0
        if rate != "+0%":
            try:
                percent = float(rate.replace('%','').replace('+',''))
                speed = 1.0 + (percent / 100.0)
            except: pass
            
        samples, sample_rate = kokoro.create(
            text, voice=kokoro_voice, speed=speed, lang="en-us"
        )
        sf.write(output_audio_path, samples, sample_rate)
        
        dur = len(samples) / sample_rate
        words = text.strip().split()
        avg_word_dur = dur / max(1, len(words))
        current = 0.0
        for w in words:
            word_boundaries.append({
                "word": w,
                "start": current,
                "end": current + avg_word_dur
            })
            current += avg_word_dur
            
    else:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        with open(output_audio_path, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    offset = chunk["offset"] / 10_000_000.0
                    duration = chunk["duration"] / 10_000_000.0
                    word = chunk["text"]
                    word_boundaries.append({
                        "word": word,
                        "start": offset,
                        "end": offset + duration
                    })
        if not word_boundaries and text.strip():
            words = text.strip().split()
            avg_word_dur = 0.35
            current = 0.0
            for w in words:
                word_boundaries.append({
                    "word": w,
                    "start": current,
                    "end": current + avg_word_dur
                })
                current += avg_word_dur
                
    return word_boundaries


def generate_single_tts(
    text: str,
    voice: str = "en-US-ChristopherNeural",
    output_audio_path: str = "temp_voice.mp3",
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> List[Dict[str, Any]]:
    return asyncio.run(_generate_voice_async(text, voice, output_audio_path, rate, pitch))


async def _generate_dialogue_async(
    dialogue_lines: List[Dict[str, Any]],
    output_dir: str,
    pause_between_speakers: float = 0.35
) -> Tuple[str, List[Dict[str, Any]], float]:

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    line_audio_files = []
    combined_timeline = []
    current_global_time = 0.0

    for idx, item in enumerate(dialogue_lines):
        speaker = item.get("speaker", f"Speaker {idx+1}")
        voice = item.get("voice", "en-US-ChristopherNeural")
        text = item.get("text", "").strip()
        avatar = item.get("avatar", "")
        rate = item.get("rate", "+0%")
        ref_audio = item.get("ref_audio", None)

        if not text:
            continue

        line_audio_file = str(out_path / f"line_{idx:03d}.wav") # Use wav for seamless concat
        
        try:
            word_boundaries = await _generate_voice_async(text, voice, line_audio_file, rate=rate, ref_audio=ref_audio)
        except Exception as e:
            print(f"[TTS] Error generating voice for {text}: {e}")
            continue

        if not Path(line_audio_file).exists() or Path(line_audio_file).stat().st_size == 0:
            print(f"[TTS] Warning: Failed to generate audio for '{text}'. Skipping.")
            continue

        dur = get_audio_duration(line_audio_file)
        if dur <= 0:
            dur = word_boundaries[-1]["end"] if word_boundaries else len(text.split()) * 0.35

        adjusted_words = []
        for wb in word_boundaries:
            adjusted_words.append({
                "word": wb["word"],
                "start": round(current_global_time + wb["start"], 3),
                "end": round(current_global_time + wb["end"], 3)
            })

        turn_info = {
            "index": idx,
            "speaker": speaker,
            "avatar": avatar,
            "text": text,
            "start": round(current_global_time, 3),
            "end": round(current_global_time + dur, 3),
            "duration": round(dur, 3),
            "words": adjusted_words,
            "audio_file": line_audio_file
        }
        combined_timeline.append(turn_info)
        line_audio_files.append((line_audio_file, dur))

        current_global_time += dur + pause_between_speakers

    stitched_audio_path = str(out_path / "combined_dialogue.wav")
    stitch_audio_clips_with_pauses(line_audio_files, pause_between_speakers, stitched_audio_path)

    total_duration = get_audio_duration(stitched_audio_path)
    if total_duration <= 0:
        total_duration = current_global_time

    return stitched_audio_path, combined_timeline, total_duration


def get_audio_duration(file_path: str) -> float:
    import subprocess
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        return 0.0


def stitch_audio_clips_with_pauses(
    clips: List[Tuple[str, float]],
    pause_sec: float,
    output_path: str
):
    import subprocess
    if not clips:
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "1", output_path], check=True)
        return

    filter_parts = []
    inputs = []
    for idx, (path, _) in enumerate(clips):
        inputs.extend(["-i", path])
    
    concat_streams = []
    for idx in range(len(clips)):
        concat_streams.append(f"[{idx}:a]")
        if idx < len(clips) - 1 and pause_sec > 0:
            filter_parts.append(f"aevalsrc=0:d={pause_sec}:s=44100[silence_{idx}]")
            concat_streams.append(f"[silence_{idx}]")
    
    concat_filter = f"{''.join(concat_streams)}concat=n={len(concat_streams)}:v=0:a=1[outa]"
    if filter_parts:
        full_filter = f"{';'.join(filter_parts)};{concat_filter}"
    else:
        full_filter = concat_filter

    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", full_filter, "-map", "[outa]", "-b:a", "192k", output_path]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[TTS Audio Stitch Error]: {e.stderr}")
        concat_txt = Path(output_path).parent / "concat_list.txt"
        with open(concat_txt, "w") as f:
            for p, _ in clips:
                f.write(f"file '{Path(p).resolve().as_posix()}'\\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", output_path], check=True)

def generate_dialogue_tts(
    dialogue_lines: List[Dict[str, Any]],
    output_dir: str,
    pause_between_speakers: float = 0.35
) -> Tuple[str, List[Dict[str, Any]], float]:
    return asyncio.run(_generate_dialogue_async(dialogue_lines, output_dir, pause_between_speakers))
