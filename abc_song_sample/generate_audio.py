#!/usr/bin/env python3
"""
generate_audio.py
Synthesizes nursery rhyme vocals via Edge TTS, generates a cheerful synthesized
music box / marimba backing track with numpy, extracts exact word/letter timestamps,
and mixes the final broadcast-quality audio track using FFmpeg.
"""

import asyncio
import json
import math
import subprocess
from pathlib import Path
import edge_tts
import numpy as np

SAMPLE_RATE = 44100
OUT_DIR = Path("export")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 6 Verses of the ABC Song
VERSES = [
    {
        "id": "v1",
        "text": "A, B, C, D, E, F, G.",
        "letters": ["A", "B", "C", "D", "E", "F", "G"],
        "subtitle": "A  B  C  D  E  F  G"
    },
    {
        "id": "v2",
        "text": "H, I, J, K, L, M, N, O, P.",
        "letters": ["H", "I", "J", "K", "L", "M", "N", "O", "P"],
        "subtitle": "H  I  J  K  L  M  N  O  P"
    },
    {
        "id": "v3",
        "text": "Q, R, S, T, U, V.",
        "letters": ["Q", "R", "S", "T", "U", "V"],
        "subtitle": "Q  R  S  T  U  V"
    },
    {
        "id": "v4",
        "text": "W, X, Y, and Z.",
        "letters": ["W", "X", "Y", "Z"],
        "subtitle": "W  X  Y  and  Z"
    },
    {
        "id": "v5",
        "text": "Now I know my ABCs.",
        "letters": [],
        "subtitle": "Now I know my ABCs!"
    },
    {
        "id": "v6",
        "text": "Next time won't you sing with me!",
        "letters": [],
        "subtitle": "Next time won't you sing with me!"
    }
]

PAUSE_BETWEEN_VERSES = 0.45  # seconds of natural musical pause between verses
INTRO_PAD = 0.8              # seconds before vocals start
OUTRO_PAD = 1.8              # seconds after vocals end

async def synthesize_vocals():
    print("[1/4] Synthesizing vocals and extracting millisecond timestamps...")
    all_timings = []
    global_letter_times = {}
    verse_ranges = []
    
    current_time = INTRO_PAD
    verse_files = []
    
    for v in VERSES:
        vid = v["id"]
        text = v["text"]
        mp3_file = OUT_DIR / f"{vid}.mp3"
        
        comm = edge_tts.Communicate(
            text, 
            voice="en-US-AnaNeural", 
            rate="+4%", 
            pitch="+6Hz", 
            boundary="WordBoundary"
        )
        
        words = []
        with open(mp3_file, "wb") as f:
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    sec = chunk["offset"] / 1e7
                    w = chunk["text"].strip(",.?! ")
                    if w:
                        words.append((sec, w))
        
        # Get actual audio duration from ffprobe
        probe = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_file)
        ])
        v_dur = float(probe.strip())
        
        v_start = current_time
        v_end = current_time + v_dur
        verse_ranges.append({
            "id": vid,
            "subtitle": v["subtitle"],
            "start": round(v_start, 3),
            "end": round(v_end, 3),
            "letters": v["letters"]
        })
        
        # Map letter timestamps
        for sec, word in words:
            letter_upper = word.upper()
            if letter_upper in v["letters"]:
                global_letter_times[letter_upper] = round(current_time + sec, 3)
                print(f"  Letter '{letter_upper}' pops at t={global_letter_times[letter_upper]}s")
        
        verse_files.append((mp3_file, v_dur))
        current_time += v_dur + PAUSE_BETWEEN_VERSES

    total_duration = current_time + OUTRO_PAD
    print(f"Total Song Duration: {total_duration:.2f} seconds")
    
    # Concatenate vocals with exact pad delays
    print("[2/4] Assembling seamless vocal master track with FFmpeg...")
    inputs = []
    chains = []
    curr_offset = INTRO_PAD
    
    for i, (fpath, dur) in enumerate(verse_files):
        inputs.extend(["-i", str(fpath)])
        chains.append(f"[{i}:a]adelay={int(curr_offset * 1000)}|{int(curr_offset * 1000)}[a{i}]")
        curr_offset += dur + PAUSE_BETWEEN_VERSES
        
    amix_in = "".join(f"[a{i}]" for i in range(len(verse_files)))
    mix_filter = ";".join(chains) + f";{amix_in}amix=inputs={len(verse_files)}:normalize=0[voxout]"
    
    vox_wav = OUT_DIR / "vocals_master.wav"
    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        *inputs,
        "-filter_complex", mix_filter,
        "-map", "[voxout]",
        str(vox_wav)
    ], check=True)
    
    return total_duration, global_letter_times, verse_ranges

def synthesize_backing_track(total_dur):
    print("[3/4] Synthesizing nursery glockenspiel & marimba backing music...")
    sr = SAMPLE_RATE
    total_samples = int(total_dur * sr)
    music = np.zeros(total_samples, dtype=np.float32)
    
    # Classic ABC melody frequencies (C major)
    # C4, D4, E4, F4, G4, A4, B4, C5
    P = {
        "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
        "G4": 392.00, "A4": 440.00, "B4": 493.88, "C5": 523.25,
        "E5": 659.25, "G5": 783.99, "R": 0
    }
    
    def add_note(note_freq, start_sec, dur_sec, vol=0.35):
        if note_freq <= 0:
            return
        n_samples = int(dur_sec * sr)
        start_idx = int(start_sec * sr)
        if start_idx >= total_samples:
            return
        end_idx = min(start_idx + n_samples, total_samples)
        length = end_idx - start_idx
        
        t = np.linspace(0, length / sr, length, False)
        # Glockenspiel bell tone: fundamental + bright overtone + warm body
        env = np.exp(-4.5 * t)
        tone = (
            np.sin(2 * np.pi * note_freq * t) * 0.7 +
            np.sin(2 * np.pi * note_freq * 2.0 * t) * 0.3 +
            np.sin(2 * np.pi * note_freq * 3.01 * t) * 0.15
        ) * env
        
        # Soft acoustic bass beneath lower notes
        bass_env = np.exp(-2.5 * t)
        bass = np.sin(2 * np.pi * (note_freq / 2.0) * t) * bass_env * 0.4
        
        music[start_idx:end_idx] += (tone * vol + bass * (vol * 0.6)).astype(np.float32)
        
    def add_chime(start_sec):
        # Sweet sparkle chime
        start_idx = int(start_sec * sr)
        length = int(0.3 * sr)
        if start_idx + length < total_samples:
            t = np.linspace(0, 0.3, length, False)
            chime = np.sin(2 * np.pi * 1567.98 * t) * np.exp(-8 * t) * 0.15
            music[start_idx:start_idx+length] += chime.astype(np.float32)
    
    # 4-measure looping chord progression synchronized with nursery tempo
    # 105 BPM -> ~0.571s per beat
    beat = 0.571
    cur_t = INTRO_PAD - 0.2
    
    # The ABC Song melody note sequence
    melody = [
        # A B C D E F G
        ("C4", 1), ("C4", 1), ("G4", 1), ("G4", 1), ("A4", 1), ("A4", 1), ("G4", 2),
        # H I J K L M N O P
        ("F4", 1), ("F4", 1), ("E4", 1), ("E4", 1), ("D4", 0.5), ("D4", 0.5), ("D4", 0.5), ("D4", 0.5), ("C4", 2),
        # Q R S T U V
        ("G4", 1), ("G4", 1), ("F4", 1), ("F4", 1), ("E4", 1), ("E4", 1), ("D4", 2),
        # W X Y and Z
        ("G4", 1), ("G4", 1), ("F4", 1), ("F4", 1), ("E4", 1), ("E4", 1), ("D4", 2),
        # Now I know my ABCs
        ("C4", 1), ("C4", 1), ("G4", 1), ("G4", 1), ("A4", 1), ("A4", 1), ("G4", 2),
        # Next time won't you sing with me
        ("F4", 1), ("F4", 1), ("E4", 1), ("E4", 1), ("D4", 1), ("D4", 1), ("C4", 3),
    ]
    
    m_time = cur_t
    for note, beats in melody:
        dur = beats * beat
        freq = P.get(note, 261.63)
        add_note(freq, m_time, dur * 0.95, vol=0.35)
        if beats >= 2:
            add_chime(m_time)
        m_time += dur
        
    # Soft background marimba arpeggio pulses throughout
    arp_notes = [P["C4"], P["E4"], P["G4"], P["C5"]]
    step = beat / 2.0
    for i in range(int(total_dur / step)):
        t_arp = i * step
        n = arp_notes[i % len(arp_notes)]
        add_note(n, t_arp, step * 0.8, vol=0.08)

    # Normalize music
    max_val = np.max(np.abs(music))
    if max_val > 0:
        music = music / max_val * 0.7
        
    # Write WAV
    music_wav = OUT_DIR / "music_backing.wav"
    int_samples = (music * 32767).astype(np.int16)
    
    import wave
    with wave.open(str(music_wav), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(int_samples.tobytes())
        
    return music_wav

def mix_master(total_dur, vox_wav, music_wav):
    print("[4/4] Mixing final studio stereo master audio...")
    final_mp3 = OUT_DIR / "abc_song_master.mp3"
    
    # Combine Vocals + Music (Music lowered slightly to 0.40 for voice clarity)
    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        "-i", str(vox_wav),
        "-i", str(music_wav),
        "-filter_complex",
        "[0:a]volume=1.35,aformat=channel_layouts=stereo[vox];"
        "[1:a]volume=0.38,aformat=channel_layouts=stereo[bgm];"
        "[vox][bgm]amix=inputs=2:duration=longest:dropout_transition=2[out]",
        "-map", "[out]",
        "-c:a", "libmp3lame",
        "-q:a", "2",
        str(final_mp3)
    ], check=True)
    
    print(f"Master Audio Ready: {final_mp3}")
    return final_mp3

async def main():
    total_dur, letter_times, verse_ranges = await synthesize_vocals()
    music_wav = synthesize_backing_track(total_dur)
    final_mp3 = mix_master(total_dur, OUT_DIR / "vocals_master.wav", music_wav)
    
    # Save timings metadata for Three.js engine and video renderer
    timings = {
        "total_duration": round(total_dur, 3),
        "letters": letter_times,
        "verses": verse_ranges
    }
    
    timings_json = OUT_DIR / "timings.json"
    with open(timings_json, "w", encoding="utf-8") as f:
        json.dump(timings, f, indent=2)
    print(f"Timings JSON saved: {timings_json}")
    
    # Also write a JS file so scene.html can load it directly without CORS issues
    timings_js = OUT_DIR / "timings.js"
    with open(timings_js, "w", encoding="utf-8") as f:
        f.write(f"window.ABC_TIMINGS = {json.dumps(timings, indent=2)};\n")
    print(f"Timings JS saved: {timings_js}")

if __name__ == "__main__":
    asyncio.run(main())
