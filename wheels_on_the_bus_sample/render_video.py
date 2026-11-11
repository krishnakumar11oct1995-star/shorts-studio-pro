#!/usr/bin/env python3
"""
render_video.py
Renders the 1080p 30fps MP4 video for 'Wheels on the Bus' using Playwright Chromium
(CodeVideoModel headless previs pipeline) + FFmpeg muxing with the Audio8_TTS master audio.
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

OUT_DIR = Path("export")
SCENE_HTML = Path("scene.html").resolve()
AUDIO_PATH = OUT_DIR / "wheels_on_the_bus_master.mp3"
TIMINGS_PATH = OUT_DIR / "timings.json"
OUTPUT_VIDEO = OUT_DIR / "wheels_on_the_bus_1080p.mp4"
THUMBNAIL_IMG = OUT_DIR / "thumbnail_wheels_on_the_bus.jpg"

FPS = 30
WIDTH = 1920
HEIGHT = 1080

async def render():
    if not SCENE_HTML.exists():
        sys.exit(f"Error: {SCENE_HTML} does not exist.")
    if not AUDIO_PATH.exists():
        sys.exit(f"Error: {AUDIO_PATH} does not exist. Run generate_audio_audio8.py first.")

    with open(TIMINGS_PATH, "r", encoding="utf-8") as f:
        timings = json.load(f)

    total_dur = timings["total_duration"]
    total_frames = int(total_dur * FPS)

    print(f"==================================================")
    print(f" Autonomous Video Rendering: Wheels on the Bus (1080p)")
    print(f" Audio Engine: Audio8_TTS (cloned bella_child voice)")
    print(f" Previs Engine: Three.js Code Video Model")
    print(f" Duration: {total_dur:.2f}s | FPS: {FPS} | Total Frames: {total_frames}")
    print(f" Target: {OUTPUT_VIDEO}")
    print(f"==================================================")

    ffmpeg_cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-f", "image2pipe",
        "-framerate", str(FPS),
        "-c:v", "mjpeg",
        "-i", "-",
        "-i", str(AUDIO_PATH),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(OUTPUT_VIDEO)
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    start_time = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",
            args=["--enable-webgl", "--ignore-gpu-blocklist", "--use-gl=angle"]
        )
        page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})

        await page.goto(SCENE_HTML.as_uri())
        await page.add_style_tag(content="#play-btn { display: none !important; }")
        await page.wait_for_timeout(1000)

        print("[Rendering 1080p Frames]...")
        for frame_idx in range(total_frames):
            t = frame_idx / FPS
            await page.evaluate(f"window.advanceClock({t})")

            frame_bytes = await page.screenshot(type="jpeg", quality=95)
            proc.stdin.write(frame_bytes)

            if (frame_idx + 1) % 90 == 0 or frame_idx == total_frames - 1:
                pct = ((frame_idx + 1) / total_frames) * 100
                elapsed = time.time() - start_time
                fps_render = (frame_idx + 1) / elapsed
                print(f"  Frame {frame_idx + 1}/{total_frames} ({pct:.1f}%) | Speed: {fps_render:.1f} fps", flush=True)

        # Generate High-Res Thumbnail at t=28.0s (Horn Beep Hero Angle)
        print("[Generating High-Resolution Thumbnail]...")
        await page.evaluate("window.advanceClock(28.0)")
        await page.screenshot(path=str(THUMBNAIL_IMG), type="jpeg", quality=98)
        print(f"Thumbnail saved: {THUMBNAIL_IMG}")

        await browser.close()

    proc.stdin.close()
    proc.wait()

    total_time = time.time() - start_time
    print(f"==================================================")
    print(f" Rendering Completed in {total_time:.1f}s!")
    print(f" Final Video: {OUTPUT_VIDEO.resolve()}")
    print(f" Size: {OUTPUT_VIDEO.stat().st_size / (1024*1024):.2f} MB")
    print(f"==================================================")

if __name__ == "__main__":
    asyncio.run(render())
