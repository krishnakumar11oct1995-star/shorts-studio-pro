"""
Asset Manager
Manages fonts, sound effects, background music, avatars, and gameplay footage.
Generates built-in procedural sound effects and starter assets so the studio works immediately offline.
"""

import os
import wave
import struct
import math
import random
import requests
import subprocess
from pathlib import Path
from typing import List, Optional

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
BG_DIR = ASSETS_DIR / "backgrounds"
MUSIC_DIR = ASSETS_DIR / "music"
SFX_DIR = ASSETS_DIR / "sfx"
FONTS_DIR = ASSETS_DIR / "fonts"
AVATARS_DIR = ASSETS_DIR / "avatars"


def ensure_all_dirs():
    """Create all asset directories."""
    for d in [BG_DIR, MUSIC_DIR, SFX_DIR, FONTS_DIR, AVATARS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def generate_beep_sfx(output_path: str, freq: float = 600, duration: float = 0.15, sfx_type: str = "pop"):
    """Generates procedural sound effects using math and wave without external dependencies."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    with wave.open(output_path, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        for i in range(n_samples):
            t = i / sample_rate
            # Decay envelope
            env = math.exp(-t * (25 if sfx_type == "pop" else 12))

            if sfx_type == "pop":
                # Pitch drops rapidly
                current_freq = freq * (1.0 + 2.0 * math.exp(-t * 40))
                value = math.sin(2 * math.pi * current_freq * t) * env
            elif sfx_type == "ding":
                # High harmonic chime
                value = (math.sin(2 * math.pi * freq * t) * 0.7 + math.sin(2 * math.pi * freq * 2 * t) * 0.3) * env
            elif sfx_type == "oof":
                # Deep cartoon thump
                current_freq = max(80, freq * (1.0 - t * 3.0))
                value = math.sin(2 * math.pi * current_freq * t) * env
            else: # click/typing
                value = (random.random() * 2 - 1) * env * 0.5

            sample = int(value * 32767 * 0.8)
            # Clamp sample
            sample = max(-32768, min(32767, sample))
            wav_file.writeframes(struct.pack("<h", sample))


def generate_chill_bgm(output_path: str, duration: float = 30.0):
    """Generates a pleasant procedural lo-fi synth chord progression loop."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)

    # Chords (Cmaj7 -> Am7 -> Dm7 -> G7) frequencies
    chords = [
        [261.63, 329.63, 392.00, 493.88],  # Cmaj7
        [220.00, 261.63, 329.63, 392.00],  # Am7
        [146.83, 220.00, 261.63, 349.23],  # Dm7
        [196.00, 246.94, 293.66, 349.23],  # G7
    ]
    chord_len = 3.75  # seconds per chord

    with wave.open(output_path, "w") as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        for i in range(n_samples):
            t = i / sample_rate
            chord_idx = int((t % (chord_len * len(chords))) / chord_len)
            current_chord = chords[chord_idx]

            # Soft vibrato
            vibrato = math.sin(2 * math.pi * 4.5 * t) * 1.5

            sample_l = 0.0
            sample_r = 0.0
            for note_idx, freq in enumerate(current_chord):
                pan = 0.3 + (note_idx * 0.15)
                tone = math.sin(2 * math.pi * (freq + vibrato) * t) * 0.12
                # Warm sub harmonic
                tone += math.sin(2 * math.pi * (freq * 0.5) * t) * 0.06
                sample_l += tone * (1.0 - pan)
                sample_r += tone * pan

            # Gentle pulse
            beat_pulse = (math.sin(2 * math.pi * 1.5 * t) + 1) * 0.1 + 0.8
            val_l = int(sample_l * beat_pulse * 32767 * 0.4)
            val_r = int(sample_r * beat_pulse * 32767 * 0.4)

            val_l = max(-32768, min(32767, val_l))
            val_r = max(-32768, min(32767, val_r))

            wav_file.writeframes(struct.pack("<hh", val_l, val_r))


def generate_fallback_background_video(output_path: str, duration: int = 15, width: int = 1080, height: int = 1920):
    """
    Generates a sleek 60 FPS animated gradient background video using FFmpeg.
    Runs instantaneously without needing external downloads.
    """
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"gradients=s={width}x{height}:r=60:c0=0x0b132b:c1=0x1c2541:c2=0x3a86ff:x0=W/2:y0=H/2:x1=W:y1=H:type=radial",
        "-vf", "hue=s=1.5:h=t*30",
        "-t", str(duration),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        output_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except Exception as e:
        # Fallback to solid color
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=0x111625:s={width}x{height}:r=60",
            "-t", str(duration),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
            output_path
        ], check=True)


def init_default_assets():
    """Initializes and verifies all required starter assets (SFX, BGM, Avatars)."""
    ensure_all_dirs()

    # 1. Create Default SFX
    sfx_definitions = {
        "message_pop.wav": (900, 0.12, "pop"),
        "ding.wav": (1200, 0.35, "ding"),
        "oof.wav": (180, 0.25, "oof"),
        "click.wav": (400, 0.08, "click"),
    }
    for filename, (freq, dur, stype) in sfx_definitions.items():
        sfx_path = SFX_DIR / filename
        if not sfx_path.exists():
            generate_beep_sfx(str(sfx_path), freq=freq, duration=dur, sfx_type=stype)
            print(f"[Asset Manager] Generated SFX: {filename}")

    # 2. Create Default Lo-Fi BGM Loop
    bgm_path = MUSIC_DIR / "roblox_chill_lofi.wav"
    if not bgm_path.exists():
        generate_chill_bgm(str(bgm_path), duration=45.0)
        print(f"[Asset Manager] Generated Starter BGM: roblox_chill_lofi.wav")

    # 3. Download Google Font (Montserrat ExtraBold) for high-impact subtitles if missing
    font_path = FONTS_DIR / "Montserrat-ExtraBold.ttf"
    if not font_path.exists():
        try:
            url = "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-ExtraBold.ttf"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                with open(font_path, "wb") as f:
                    f.write(resp.content)
                print(f"[Asset Manager] Downloaded Montserrat-ExtraBold font.")
        except Exception as e:
            print(f"[Asset Manager] Font download skipped: {e}")

    # 4. Generate Starter Roblox Avatars
    from core.roblox_api import fetch_roblox_avatar, DEFAULT_PRESETS
    for name in DEFAULT_PRESETS.keys():
        fetch_roblox_avatar(name)

    print("[Asset Manager] Starter assets initialized successfully.")


def list_background_videos() -> List[str]:
    """Lists available gameplay video files in assets/backgrounds."""
    ensure_all_dirs()
    exts = (".mp4", ".mov", ".mkv", ".webm", ".avi")
    files = [str(f) for f in BG_DIR.iterdir() if f.suffix.lower() in exts]
    return files


def list_bgm_tracks() -> List[str]:
    """Lists available background music tracks."""
    ensure_all_dirs()
    exts = (".mp3", ".wav", ".aac", ".m4a", ".ogg")
    return [str(f) for f in MUSIC_DIR.iterdir() if f.suffix.lower() in exts]


def list_sfx() -> List[str]:
    """Lists available sound effects."""
    ensure_all_dirs()
    exts = (".wav", ".mp3", ".ogg")
    return [str(f) for f in SFX_DIR.iterdir() if f.suffix.lower() in exts]


def download_roblox_gameplay(url: str, output_name: str = "roblox_parkour.mp4") -> Optional[str]:
    """Downloads copyright-free Roblox gameplay footage via yt-dlp."""
    ensure_all_dirs()
    target_path = BG_DIR / output_name
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4][height<=1080]+bestaudio/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", str(target_path),
        url
    ]
    try:
        subprocess.run(cmd, check=True)
        return str(target_path)
    except Exception as e:
        print(f"[Asset Manager] Failed to download gameplay: {e}")
        return None


if __name__ == "__main__":
    init_default_assets()
