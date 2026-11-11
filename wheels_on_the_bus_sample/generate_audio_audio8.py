#!/usr/bin/env python3
"""
generate_audio_audio8.py
Generates the complete audio track for 'Wheels on the Bus' using Audio8_TTS (Falcon-H1 ONNX)
with the cloned 'bella_child' natural voice, creates bouncy nursery music with sound effects
(horn beeps, wiper swishes, door clicks), and outputs master audio + timings.
"""

import json
import math
import subprocess
import sys
from pathlib import Path
import numpy as np
import soundfile as sf

AUDIO8_ROOT = Path(r"C:\Users\Krishna\Downloads\Youtube\Audio8_TTS\onnx_runtime_0_1b_int8")
sys.path.append(str(AUDIO8_ROOT))
from arktts_runtime.runtime import ArkTtsRuntime

SAMPLE_RATE = 44100
OUT_DIR = Path("export")
OUT_DIR.mkdir(parents=True, exist_ok=True)

VERSES = [
    {
        "id": "v1_wheels",
        "title": "Wheels",
        "action": "wheels",
        "text": "The wheels on the bus go round and round, round and round, round and round. The wheels on the bus go round and round, all through the town!",
        "subtitle": "The wheels on the bus go round and round!"
    },
    {
        "id": "v2_wipers",
        "title": "Wipers",
        "action": "wipers",
        "text": "The wipers on the bus go swish, swish, swish, swish, swish, swish, swish, swish, swish. The wipers on the bus go swish, swish, swish, all through the town!",
        "subtitle": "The wipers on the bus go swish, swish, swish!"
    },
    {
        "id": "v3_horn",
        "title": "Horn",
        "action": "horn",
        "text": "The horn on the bus goes beep, beep, beep, beep, beep, beep, beep, beep, beep. The horn on the bus goes beep, beep, beep, all through the town!",
        "subtitle": "The horn on the bus goes beep, beep, beep!"
    },
    {
        "id": "v4_doors",
        "title": "Doors",
        "action": "doors",
        "text": "The doors on the bus go open and shut, open and shut, open and shut. The doors on the bus go open and shut, all through the town!",
        "subtitle": "The doors on the bus go open and shut!"
    },
    {
        "id": "v5_people",
        "title": "People",
        "action": "people",
        "text": "The people on the bus go up and down, up and down, up and down. The people on the bus go up and down, all through the town!",
        "subtitle": "The people on the bus go up and down!"
    }
]

INTRO_PAD = 1.0
PAUSE = 0.5
OUTRO_PAD = 2.0

def synthesize_vocals():
    print("[1/4] Initializing Audio8_TTS ONNX engine...")
    model_dir = AUDIO8_ROOT / "model"
    voices_dir = AUDIO8_ROOT / "voices"
    rt = ArkTtsRuntime(model_dir, voices_dir, "int8", "fp16", 6)
    sr = int(rt.manifest["sample_rate"])

    verse_ranges = []
    verse_files = []
    current_time = INTRO_PAD

    print(f"[2/4] Synthesizing {len(VERSES)} verses with Audio8 'bella_child' voice...")
    for v in VERSES:
        vid = v["id"]
        text = v["text"]
        out_wav = OUT_DIR / f"{vid}.wav"
        
        print(f"  Synthesizing verse: '{v['title']}'...")
        audio, _ = rt.synthesize(text=text, voice="bella_child", max_new_tokens=320, temperature=0.7)
        sf.write(str(out_wav), audio, sr)
        
        dur = len(audio) / sr
        v_start = current_time
        v_end = current_time + dur
        
        verse_ranges.append({
            "id": vid,
            "title": v["title"],
            "action": v["action"],
            "subtitle": v["subtitle"],
            "start": round(v_start, 3),
            "end": round(v_end, 3)
        })
        
        verse_files.append((out_wav, dur))
        current_time += dur + PAUSE

    total_dur = current_time + OUTRO_PAD
    print(f"Total Song Duration: {total_dur:.2f}s")

    # Combine vocals using FFmpeg
    inputs = []
    chains = []
    offset = INTRO_PAD
    for i, (fpath, dur) in enumerate(verse_files):
        inputs.extend(["-i", str(fpath)])
        chains.append(f"[{i}:a]adelay={int(offset * 1000)}|{int(offset * 1000)}[a{i}]")
        offset += dur + PAUSE

    mix_in = "".join(f"[a{i}]" for i in range(len(verse_files)))
    mix_filter = ";".join(chains) + f";{mix_in}amix=inputs={len(verse_files)}:normalize=0[voxout]"
    vox_wav = OUT_DIR / "vocals_master.wav"

    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        *inputs,
        "-filter_complex", mix_filter,
        "-map", "[voxout]",
        str(vox_wav)
    ], check=True)

    return total_dur, verse_ranges, vox_wav

def synthesize_music_and_sfx(total_dur, verse_ranges):
    print("[3/4] Synthesizing bouncy nursery music & synchronized sound effects...")
    sr = SAMPLE_RATE
    total_samples = int(total_dur * sr)
    music = np.zeros(total_samples, dtype=np.float32)

    # 116 BPM -> 0.517s per beat
    beat = 0.517

    # G Major scale: G3, A3, B3, C4, D4, E4, F#4, G4, B4, D5
    NOTES = {
        "G3": 196.00, "B3": 246.94, "C4": 261.63, "D4": 293.66,
        "E4": 329.63, "Fs4": 369.99, "G4": 392.00, "A4": 440.00,
        "B4": 493.88, "D5": 587.33
    }

    def add_tone(freq, start_sec, dur_sec, vol=0.3):
        if freq <= 0: return
        n_samples = int(dur_sec * sr)
        start_idx = int(start_sec * sr)
        if start_idx >= total_samples: return
        end_idx = min(start_idx + n_samples, total_samples)
        l = end_idx - start_idx
        t = np.linspace(0, l / sr, l, False)
        # Bright marimba / nursery bell
        tone = (np.sin(2 * np.pi * freq * t) * 0.7 +
                np.sin(2 * np.pi * freq * 2.0 * t) * 0.3) * np.exp(-4.0 * t)
        music[start_idx:end_idx] += (tone * vol).astype(np.float32)

    def add_bass(freq, start_sec, dur_sec, vol=0.35):
        n_samples = int(dur_sec * sr)
        start_idx = int(start_sec * sr)
        if start_idx >= total_samples: return
        end_idx = min(start_idx + n_samples, total_samples)
        l = end_idx - start_idx
        t = np.linspace(0, l / sr, l, False)
        bass = np.sin(2 * np.pi * freq * t) * np.exp(-2.2 * t)
        music[start_idx:end_idx] += (bass * vol).astype(np.float32)

    def add_horn_beep(start_sec):
        # Two-tone car horn (F4 + A4)
        for f in [349.23, 440.00]:
            n_samples = int(0.18 * sr)
            s_idx = int(start_sec * sr)
            if s_idx + n_samples < total_samples:
                t = np.linspace(0, 0.18, n_samples, False)
                tone = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t)) * (0.8 + 0.2 * np.sin(50 * t))
                music[s_idx:s_idx+n_samples] += (tone * 0.22).astype(np.float32)

    def add_wiper_swish(start_sec):
        # Filtered noise swish
        n_samples = int(0.25 * sr)
        s_idx = int(start_sec * sr)
        if s_idx + n_samples < total_samples:
            noise = np.random.uniform(-0.15, 0.15, n_samples)
            t = np.linspace(0, 1, n_samples, False)
            env = np.sin(np.pi * t)
            music[s_idx:s_idx+n_samples] += (noise * env).astype(np.float32)

    # 1. Bouncy bass and marimba rhythm throughout
    n_beats = int(total_dur / beat)
    chord_roots = [NOTES["G3"], NOTES["D4"], NOTES["G3"], NOTES["C4"]]
    for b in range(n_beats):
        t_b = b * beat
        r = chord_roots[(b // 4) % len(chord_roots)]
        add_bass(r / 2.0, t_b, beat * 0.8, vol=0.35)
        # Marimba syncopated pulse
        add_tone(r, t_b, beat * 0.5, vol=0.12)
        add_tone(NOTES["G4"], t_b + beat * 0.5, beat * 0.4, vol=0.10)

    # 2. Add synchronized sound effects based on verse actions!
    for v in verse_ranges:
        st = v["start"]
        dur = v["end"] - v["start"]
        action = v["action"]
        
        if action == "horn":
            # 3 horn beeps during "beep beep beep"
            add_horn_beep(st + 1.2)
            add_horn_beep(st + 1.6)
            add_horn_beep(st + 2.0)
            add_horn_beep(st + 3.2)
            add_horn_beep(st + 3.6)
            add_horn_beep(st + 4.0)
        elif action == "wipers":
            # Swish sounds during "swish swish swish"
            for k in range(6):
                add_wiper_swish(st + 1.0 + k * 0.45)

    # Normalize
    max_val = np.max(np.abs(music))
    if max_val > 0:
        music = (music / max_val * 0.65).astype(np.float32)

    music_wav = OUT_DIR / "music_backing.wav"
    int_samples = (music * 32767).astype(np.int16)
    import wave
    with wave.open(str(music_wav), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(int_samples.tobytes())

    return music_wav

def mix_master(vox_wav, music_wav):
    print("[4/4] Mixing final studio master track...")
    final_mp3 = OUT_DIR / "wheels_on_the_bus_master.mp3"
    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        "-i", str(vox_wav),
        "-i", str(music_wav),
        "-filter_complex",
        "[0:a]volume=1.4,aformat=channel_layouts=stereo[vox];"
        "[1:a]volume=0.45,aformat=channel_layouts=stereo[bgm];"
        "[vox][bgm]amix=inputs=2:duration=longest:dropout_transition=2[out]",
        "-map", "[out]",
        "-c:a", "libmp3lame",
        "-q:a", "2",
        str(final_mp3)
    ], check=True)
    return final_mp3

def main():
    total_dur, verse_ranges, vox_wav = synthesize_vocals()
    music_wav = synthesize_music_and_sfx(total_dur, verse_ranges)
    final_mp3 = mix_master(vox_wav, music_wav)

    timings = {
        "song": "Wheels on the Bus",
        "voice": "Audio8_TTS (bella_child)",
        "total_duration": round(total_dur, 3),
        "verses": verse_ranges
    }

    with open(OUT_DIR / "timings.json", "w", encoding="utf-8") as f:
        json.dump(timings, f, indent=2)

    with open(OUT_DIR / "timings.js", "w", encoding="utf-8") as f:
        f.write(f"window.BUS_TIMINGS = {json.dumps(timings, indent=2)};\n")

    print(f"Master Audio Track Ready: {final_mp3}")
    print(f"Timings Generated: {OUT_DIR / 'timings.json'}")

if __name__ == "__main__":
    main()
