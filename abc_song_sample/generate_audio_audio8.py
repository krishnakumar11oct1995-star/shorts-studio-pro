#!/usr/bin/env python3
"""
generate_audio_audio8.py
Generates the complete audio track for 'ABC Song' using Audio8_TTS (Falcon-H1 ONNX)
with the cloned 'bella_child' natural child voice. Synthesizes nursery glockenspiel
and marimba backing music, train whistle sound effects ('Choo Choo!'), extracts
precise letter onsets for 3D train letter pops, and produces broadcast-ready master audio.
"""

import json
import math
import subprocess
import sys
import wave
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
        "id": "v1",
        "title": "A through G",
        "text": "A, B, C, D, E, F, G.",
        "letters": ["A", "B", "C", "D", "E", "F", "G"],
        "subtitle": "A  B  C  D  E  F  G"
    },
    {
        "id": "v2",
        "title": "H through P",
        "text": "H, I, J, K, L, M, N, O, P.",
        "letters": ["H", "I", "J", "K", "L", "M", "N", "O", "P"],
        "subtitle": "H  I  J  K  L  M  N  O  P"
    },
    {
        "id": "v3",
        "title": "Q through V",
        "text": "Q, R, S, T, U, V.",
        "letters": ["Q", "R", "S", "T", "U", "V"],
        "subtitle": "Q  R  S  T  U  V"
    },
    {
        "id": "v4",
        "title": "W through Z",
        "text": "W, X, Y, and Z.",
        "letters": ["W", "X", "Y", "Z"],
        "subtitle": "W  X  Y  and  Z"
    },
    {
        "id": "v5",
        "title": "Now I know my ABCs",
        "text": "Now I know my ABCs.",
        "letters": [],
        "subtitle": "Now I know my ABCs!"
    },
    {
        "id": "v6",
        "title": "Next time won't you sing with me",
        "text": "Next time won't you sing with me!",
        "letters": [],
        "subtitle": "Next time won't you sing with me!"
    }
]

INTRO_PAD = 1.2
PAUSE_BETWEEN_VERSES = 0.6
OUTRO_PAD = 2.5

def detect_letter_onsets(wav_path, expected_letters):
    """Detects peak energy onsets for each letter spoken in the verse."""
    n_expected = len(expected_letters)
    if n_expected == 0:
        return []
    
    data, sr = sf.read(str(wav_path))
    if len(data.shape) > 1:
        data = data.mean(axis=1)
    
    frame_len = int(sr * 0.03)  # 30ms
    hop = int(sr * 0.01)        # 10ms
    energy = np.array([np.sum(data[i:i+frame_len]**2) for i in range(0, len(data)-frame_len, hop)])
    energy = energy / (np.max(energy) + 1e-9)
    
    best_onsets = []
    # Search for an energy threshold that gives exactly n_expected peaks
    for th in np.linspace(0.015, 0.20, 40):
        onsets = []
        in_peak = False
        for idx, e in enumerate(energy):
            t = idx * hop / sr
            if e > th and not in_peak:
                onsets.append(round(t, 3))
                in_peak = True
            elif e < th * 0.35:
                in_peak = False
        if len(onsets) == n_expected:
            best_onsets = onsets
            break
        if not best_onsets or abs(len(onsets) - n_expected) < abs(len(best_onsets) - n_expected):
            best_onsets = onsets
            
    # Fallback to smart interpolation across active speech if count differs
    if len(best_onsets) != n_expected:
        dur = len(data) / sr
        start_speech = 0.08
        end_speech = max(dur - 0.15, start_speech + 0.5)
        step = (end_speech - start_speech) / n_expected
        best_onsets = [round(start_speech + i * step, 3) for i in range(n_expected)]
        
    return best_onsets

def synthesize_vocals():
    print("[1/5] Initializing Audio8_TTS ONNX engine...")
    model_dir = AUDIO8_ROOT / "model"
    voices_dir = AUDIO8_ROOT / "voices"
    rt = ArkTtsRuntime(model_dir, voices_dir, "int8", "fp16", 6)
    sr = int(rt.manifest["sample_rate"])

    verse_ranges = []
    global_letter_times = {}
    verse_files = []
    current_time = INTRO_PAD

    print(f"[2/5] Synthesizing {len(VERSES)} verses with Audio8 'bella_child' natural child voice...")
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
        
        # Detect onsets for letter blocks
        onsets = detect_letter_onsets(out_wav, v["letters"])
        for char, onset in zip(v["letters"], onsets):
            abs_time = round(v_start + onset, 3)
            global_letter_times[char] = abs_time
            print(f"    Letter '{char}': onset at {abs_time:.3f}s")
        
        verse_ranges.append({
            "id": vid,
            "title": v["title"],
            "subtitle": v["subtitle"],
            "start": round(v_start, 3),
            "end": round(v_end, 3),
            "letters": v["letters"]
        })
        
        verse_files.append((out_wav, dur))
        current_time += dur + PAUSE_BETWEEN_VERSES

    total_duration = round(current_time - PAUSE_BETWEEN_VERSES + OUTRO_PAD, 3)
    print(f"  Total vocal duration: {total_duration:.2f}s across {len(VERSES)} verses.")

    # Mix vocals into one synchronized master vocal stem
    inputs = []
    chains = []
    curr_offset = INTRO_PAD
    for i, (fpath, dur) in enumerate(verse_files):
        inputs.extend(["-i", str(fpath)])
        chains.append(f"[{i}:a]adelay={int(curr_offset * 1000)}|{int(curr_offset * 1000)}[a{i}]")
        curr_offset += dur + PAUSE_BETWEEN_VERSES

    amix_in = "".join(f"[a{i}]" for i in range(len(verse_files)))
    mix_filter = ";".join(chains) + f";{amix_in}amix=inputs={len(verse_files)}:normalize=0[voxout]"
    
    vox_master = OUT_DIR / "vocals_master.wav"
    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        *inputs,
        "-filter_complex", mix_filter,
        "-map", "[voxout]",
        str(vox_master)
    ], check=True)

    return total_duration, global_letter_times, verse_ranges

def synthesize_backing_music(total_dur, verse_ranges):
    print("[3/5] Synthesizing nursery glockenspiel, marimba & chime music...")
    sr = SAMPLE_RATE
    total_samples = int(total_dur * sr)
    music = np.zeros(total_samples, dtype=np.float32)

    # Note frequencies in C Major
    P = {
        "C3": 130.81, "G3": 196.00, "A3": 220.00, "B3": 246.94,
        "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
        "G4": 392.00, "A4": 440.00, "B4": 493.88, "C5": 523.25,
        "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99,
        "A5": 880.00, "C6": 1046.50, "R": 0
    }

    def add_tone(freq, start_sec, dur_sec, vol=0.3):
        if freq <= 0:
            return
        start_idx = int(start_sec * sr)
        n_samples = int(dur_sec * sr)
        if start_idx >= total_samples:
            return
        end_idx = min(start_idx + n_samples, total_samples)
        length = end_idx - start_idx
        t = np.linspace(0, length / sr, length, False)
        
        # Glockenspiel bell envelope: bright initial strike with clean decay
        env = np.exp(-4.2 * t)
        bell = (
            np.sin(2 * np.pi * freq * t) * 0.70 +
            np.sin(2 * np.pi * freq * 2.001 * t) * 0.28 +
            np.sin(2 * np.pi * freq * 3.014 * t) * 0.12
        ) * env
        
        # Soft acoustic bass support
        bass_env = np.exp(-2.2 * t)
        bass = np.sin(2 * np.pi * (freq / 2.0) * t) * bass_env * 0.35
        
        music[start_idx:end_idx] += (bell * vol + bass * (vol * 0.5)).astype(np.float32)

    def add_chime(start_sec):
        start_idx = int(start_sec * sr)
        length = int(0.35 * sr)
        if start_idx + length < total_samples:
            t = np.linspace(0, 0.35, length, False)
            chime = (
                np.sin(2 * np.pi * 1567.98 * t) * 0.5 +
                np.sin(2 * np.pi * 2093.00 * t) * 0.4
            ) * np.exp(-7.5 * t) * 0.15
            music[start_idx:start_idx+length] += chime.astype(np.float32)

    def add_train_whistle(start_sec):
        """Cute steam train whistle: two-tone chord with cheerful vibrato."""
        start_idx = int(start_sec * sr)
        length = int(0.85 * sr)
        if start_idx + length < total_samples:
            t = np.linspace(0, 0.85, length, False)
            # Breath envelope (rise, sustain, soft fade)
            env = np.sin(np.pi * np.clip(t / 0.85, 0, 1)) ** 1.4
            vib = np.sin(2 * np.pi * 5.5 * t) * 7.0  # 5.5Hz vibrato
            whistle1 = np.sin(2 * np.pi * (440.0 + vib) * t) * 0.45
            whistle2 = np.sin(2 * np.pi * (587.33 + vib * 1.3) * t) * 0.38
            whistle3 = np.sin(2 * np.pi * (880.0 + vib * 2) * t) * 0.15
            sig = (whistle1 + whistle2 + whistle3) * env * 0.42
            music[start_idx:start_idx+length] += sig.astype(np.float32)

    # Add train whistle at the very beginning when the train enters
    add_train_whistle(0.2)
    # Add second toot right before vocals
    add_train_whistle(0.65)

    # Follow the verses with synchronized Twinkle/ABC melody notes
    verse_melodies = [
        # V1: A B C D E F G (C C G G A A G)
        ["C4", "C4", "G4", "G4", "A4", "A4", "G4"],
        # V2: H I J K L M N O P (F F E E D D D D C)
        ["F4", "F4", "E4", "E4", "D4", "D4", "D4", "D4", "C4"],
        # V3: Q R S T U V (G G F F E E D)
        ["G4", "G4", "F4", "F4", "E4", "D4"],
        # V4: W X Y and Z (G G F F E D)
        ["G4", "F4", "E4", "D4"],
        # V5: Now I know my ABCs (C C G G A A G)
        ["C4", "C4", "G4", "G4", "A4", "A4", "G4"],
        # V6: Next time won't you sing with me (F F E E D D C)
        ["F4", "F4", "E4", "E4", "D4", "D4", "C4"]
    ]

    for v_info, notes in zip(verse_ranges, verse_melodies):
        v_start = v_info["start"]
        v_end = v_info["end"]
        v_dur = v_end - v_start
        note_dur = v_dur / len(notes)
        for i, n in enumerate(notes):
            t_note = v_start + i * note_dur
            add_tone(P[n], t_note, note_dur * 0.90, vol=0.28)
            if i % 2 == 0:
                add_chime(t_note)

    # Add train whistle at outro celebration
    add_train_whistle(total_dur - OUTRO_PAD + 0.3)
    add_train_whistle(total_dur - OUTRO_PAD + 0.85)

    # Rhythmic bouncing marimba arpeggios throughout the song
    beat = 0.52  # ~115 BPM
    arp_notes = [P["C4"], P["E4"], P["G4"], P["C5"], P["G4"], P["E4"]]
    for i in range(int(total_dur / (beat / 2))):
        t_arp = i * (beat / 2)
        n = arp_notes[i % len(arp_notes)]
        add_tone(n, t_arp, (beat / 2) * 0.75, vol=0.07)

    # Gentle kick and shaker pulse for cheerful nursery groove
    for i in range(int(total_dur / beat)):
        t_beat = i * beat
        idx = int(t_beat * sr)
        l_kick = int(0.12 * sr)
        if idx + l_kick < total_samples:
            t_k = np.linspace(0, 0.12, l_kick, False)
            kick = np.sin(2 * np.pi * 95 * np.exp(-18 * t_k) * t_k) * np.exp(-12 * t_k) * 0.22
            music[idx:idx+l_kick] += kick.astype(np.float32)

    # Normalize
    max_val = np.max(np.abs(music))
    if max_val > 0:
        music = music / max_val * 0.75

    music_wav = OUT_DIR / "music_backing.wav"
    sf.write(str(music_wav), music, sr)
    print(f"  Backing track synthesized: {music_wav} ({total_dur:.2f}s)")
    return music_wav

def mix_master(total_dur):
    print("[4/5] Mixing master broadcast track with FFmpeg...")
    vox_wav = OUT_DIR / "vocals_master.wav"
    music_wav = OUT_DIR / "music_backing.wav"
    master_mp3 = OUT_DIR / "abc_song_master.mp3"

    # Vox volume 1.35, music volume 0.75, slight compressor for radio fullness
    filter_complex = (
        "[0:a]volume=1.35[v];"
        "[1:a]volume=0.75[m];"
        "[v][m]amix=inputs=2:duration=longest:dropout_transition=2[mixed];"
        "[mixed]acompressor=threshold=-16dB:ratio=3:attack=5:release=50[out]"
    )

    cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-i", str(vox_wav),
        "-i", str(music_wav),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(master_mp3)
    ]
    subprocess.run(cmd, check=True)
    print(f"  Master audio ready: {master_mp3}")
    return master_mp3

def export_timings(total_dur, letter_times, verse_ranges):
    print("[5/5] Exporting timings.json and timings.js for 3D Three.js scene...")
    data = {
        "total_duration": total_dur,
        "letters": letter_times,
        "verses": verse_ranges
    }
    
    with open(OUT_DIR / "timings.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    js_content = f"window.SONG_DATA = {json.dumps(data, indent=2)};\n"
    with open(OUT_DIR / "timings.js", "w", encoding="utf-8") as f:
        f.write(js_content)
        
    print(f"  Timings exported successfully ({len(letter_times)} letters, {len(verse_ranges)} verses).")

def main():
    print("=" * 60)
    print("Alphabet Adventure - ABC Song Audio Generation Pipeline")
    print("Using Audio8_TTS (Falcon-H1 INT8 ONNX) + 'bella_child' Voice")
    print("=" * 60)
    
    total_dur, letter_times, verse_ranges = synthesize_vocals()
    synthesize_backing_music(total_dur, verse_ranges)
    mix_master(total_dur)
    export_timings(total_dur, letter_times, verse_ranges)
    
    print("=" * 60)
    print(f"SUCCESS: Master ABC song generated! Duration = {total_dur:.2f}s")
    print("=" * 60)

if __name__ == "__main__":
    main()
