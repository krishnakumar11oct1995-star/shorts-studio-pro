#!/usr/bin/env python3
"""
run_pipeline.py
The Zero-Intervention Master Runner for 3D Kids Music Videos.
Runs the complete autonomous pipeline from song generation to final 1080p MP4 video.
"""

import subprocess
import sys
import time

def main():
    print("=================================================================")
    print(" 🚀 STARTING FULLY AUTONOMOUS 3D KIDS VIDEO GENERATION PIPELINE")
    print(" Topic: 'ABC Song' (CoComelon Style 3D Alphabet Train)")
    print(" Zero user intervention required.")
    print("=================================================================\n")
    
    t0 = time.time()
    
    # Stage 1: Audio Generation
    print(">>> STAGE 1: Vocal Synthesis, Backing Music & Timings Extraction")
    subprocess.run([sys.executable, "generate_audio.py"], check=True)
    print("Stage 1 completed successfully!\n")
    
    # Stage 2: 3D Video Rendering
    print(">>> STAGE 2: Headless 3D WebGL Rendering to 1080p MP4 Video")
    subprocess.run([sys.executable, "render_video.py"], check=True)
    print("Stage 2 completed successfully!\n")
    
    total_sec = time.time() - t0
    print("=================================================================")
    print(f" ✅ ALL STAGES COMPLETE in {total_sec:.1f} seconds!")
    print(" Final 1080p MP4 Video: export/abc_song_1080p.mp4")
    print(" High-Res YouTube Thumbnail: export/thumbnail_abc_song.jpg")
    print(" Interactive Web 3D Player: scene.html")
    print("=================================================================")

if __name__ == "__main__":
    main()
