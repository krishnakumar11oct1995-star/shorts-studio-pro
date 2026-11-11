#!/usr/bin/env python3
"""
render_video.py
Headless automated video renderer for the 3D ABC Song video.
Uses Playwright (launching system Chrome with WebGL) to render 1080p frames
deterministically and pipes them straight into FFmpeg with the master audio track.
Outputs broadcast-ready 1080p MP4 video and an eye-catching YouTube thumbnail.
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
AUDIO_PATH = OUT_DIR / "abc_song_master.mp3"
TIMINGS_PATH = OUT_DIR / "timings.json"
OUTPUT_VIDEO = OUT_DIR / "abc_song_1080p.mp4"
THUMBNAIL_IMG = OUT_DIR / "thumbnail_abc_song.jpg"

FPS = 30
WIDTH = 1920
HEIGHT = 1080

async def render():
    if not SCENE_HTML.exists():
        sys.exit(f"Error: {SCENE_HTML} does not exist.")
    if not AUDIO_PATH.exists():
        sys.exit(f"Error: {AUDIO_PATH} does not exist. Run generate_audio.py first.")
        
    with open(TIMINGS_PATH, "r", encoding="utf-8") as f:
        timings = json.load(f)
        
    total_dur = timings["total_duration"]
    total_frames = int(total_dur * FPS)
    
    print(f"==================================================")
    print(f" Autonomous Video Rendering: 3D ABC Song (1080p)")
    print(f" Duration: {total_dur:.2f}s | FPS: {FPS} | Total Frames: {total_frames}")
    print(f" Target: {OUTPUT_VIDEO}")
    print(f"==================================================")
    
    # Initialize FFmpeg pipeline
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
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(OUTPUT_VIDEO)
    ]
    
    proc = subprocess.Popen(
        ffmpeg_cmd, 
        stdin=subprocess.PIPE, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )
    
    start_time = time.time()
    
    async with async_playwright() as p:
        # Launch system Google Chrome with GPU acceleration
        browser = await p.chromium.launch(
            channel="chrome",
            args=["--enable-webgl", "--ignore-gpu-blocklist", "--use-gl=angle"]
        )
        page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        
        # Load the 3D scene
        await page.goto(SCENE_HTML.as_uri())
        await page.add_style_tag(content="#play-btn { display: none !important; }")
        await page.wait_for_timeout(1000)
        
        # Render frame-by-frame
        print("[Rendering Frames]...")
        for frame_idx in range(total_frames):
            t = frame_idx / FPS
            
            # Deterministically seek the 3D scene to time t
            await page.evaluate(f"window.advanceClock({t})")
            
            # Capture frame as high-quality JPEG
            frame_bytes = await page.screenshot(type="jpeg", quality=95)
            proc.stdin.write(frame_bytes)
            
            # Print periodic progress
            if (frame_idx + 1) % 60 == 0 or frame_idx == total_frames - 1:
                pct = ((frame_idx + 1) / total_frames) * 100
                elapsed = time.time() - start_time
                fps_render = (frame_idx + 1) / elapsed
                print(f"  Frame {frame_idx + 1}/{total_frames} ({pct:.1f}%) | Speed: {fps_render:.1f} fps", flush=True)
                
        # Generate Celebratory Thumbnail (Wide shot with balloons and glowing letters)
        print("[Generating High-Resolution Thumbnail]...")
        thumb_t = max(2.5, total_dur - 3.0)
        await page.evaluate(f"window.advanceClock({thumb_t})")
        await page.screenshot(path=str(THUMBNAIL_IMG), type="jpeg", quality=98)
        print(f"Thumbnail saved: {THUMBNAIL_IMG} at t={thumb_t:.2f}s")
        
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
