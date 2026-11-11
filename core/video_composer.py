"""
Video Composer Engine
GPU-accelerated video synthesis pipeline with authentic Roblox chat overlays,
animated word-highlight subtitles, audio ducking, and sound effect synchronization.
"""

import os
import sys
import subprocess
import shutil
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from core.roblox_api import fetch_roblox_avatar
from core.tts_engine import generate_dialogue_tts, get_audio_duration
from core.whatsapp_renderer import render_dynamic_whatsapp_video
from core.chat_renderer import (
    render_roblox_chat_bubble, 
    render_story_header_banner,
    render_whatsapp_chat_bubble,
    generate_whatsapp_background
)
from core.caption_engine import generate_animated_ass_subtitles
from core.asset_manager import (
    ASSETS_DIR, BG_DIR, MUSIC_DIR, SFX_DIR,
    list_background_videos, list_bgm_tracks, list_sfx,
    generate_fallback_background_video, init_default_assets
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def detect_best_video_encoder() -> Tuple[str, List[str]]:
    """
    Detects the best available hardware/software encoder on Windows.
    Checks: NVENC -> Windows MediaFoundation (GPU) -> libx264 (CPU).
    """
    # 1. Test NVENC
    cmd_nvenc = [
        "ffmpeg", "-f", "lavfi", "-i", "nullsrc=s=64x64:d=0.1",
        "-c:v", "h264_nvenc", "-f", "null", "-"
    ]
    try:
        if subprocess.run(cmd_nvenc, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
            return "NVENC (NVIDIA GPU)", ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "21", "-rc", "vbr", "-pix_fmt", "yuv420p"]
    except Exception:
        pass

    # 2. Test MediaFoundation GPU
    cmd_mf = [
        "ffmpeg", "-f", "lavfi", "-i", "nullsrc=s=64x64:d=0.1",
        "-c:v", "h264_mf", "-f", "null", "-"
    ]
    try:
        if subprocess.run(cmd_mf, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
            return "MediaFoundation (GPU)", ["-c:v", "h264_mf", "-b:v", "6000k", "-pix_fmt", "yuv420p"]
    except Exception:
        pass

    # 3. Fallback to CPU libx264
    return "libx264 (CPU Ultrafast)", ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p"]


def check_nvenc_support() -> bool:
    """Returns True if any GPU hardware encoder (NVENC or MediaFoundation) is available."""
    enc_name, _ = detect_best_video_encoder()
    return "GPU" in enc_name


def format_ffmpeg_path(path: str) -> str:
    """Formats a Windows path for FFmpeg filter arguments (escapes colons and backslashes)."""
    p = Path(path).resolve().as_posix()
    p = p.replace(":", "\\:")
    return p


def render_roblox_video(
    dialogue_or_script: Any,
    video_format: str = "chat",  # "chat" or "storytime"
    title: str = "Roblox Story",
    bg_video_path: Optional[str] = None,
    bgm_path: Optional[str] = None,
    output_filename: str = "roblox_short.mp4",
    width: int = 1080,
    height: int = 1920,
    fps: int = 60,
    use_gpu: bool = True,
    theme: str = "roblox"
) -> str:
    """
    Renders complete Roblox YouTube video / Short.
    """
    init_default_assets()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = OUTPUT_DIR / f"temp_{random.randint(10000, 99999)}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Parse dialogue lines
        if isinstance(dialogue_or_script, str):
            from core.script_generator import parse_raw_dialogue_text
            dialogue_lines = parse_raw_dialogue_text(dialogue_or_script)
        else:
            dialogue_lines = dialogue_or_script

        if not dialogue_lines:
            dialogue_lines = [
                {"speaker": "Bacon", "voice": "en-US-ChristopherNeural", "text": "Welcome to Roblox!"}
            ]

        # 2. Fetch avatars for all speakers
        for line in dialogue_lines:
            spk = line.get("speaker", "Bacon")
            line["avatar"] = fetch_roblox_avatar(spk)

        # 3. Generate Speech Audio & Word Timeline
        print("[Video Composer] Generating neural voiceovers...")
        speech_audio, timeline, total_duration = generate_dialogue_tts(
            dialogue_lines,
            str(temp_dir),
            pause_between_speakers=0.35 if video_format == "chat" else 0.2
        )
        print(f"[Video Composer] Speech generated: {total_duration:.2f}s")

        # 4. Prepare Background Video
        if theme == "whatsapp":
            bg_video_path = str(temp_dir / "whatsapp_visuals.mp4")
            render_dynamic_whatsapp_video(timeline, total_duration, str(temp_dir), bg_video_path, width, height, fps)
        else:
            if not bg_video_path or not Path(bg_video_path).exists():
                bgs = list_background_videos()
                if bgs:
                    bg_video_path = bgs[0]
                else:
                    bg_video_path = str(temp_dir / "fallback_bg.mp4")
                    generate_fallback_background_video(bg_video_path, duration=int(total_duration + 4), width=width, height=height)

        # 5. Prepare SFX & BGM paths
        sfx_pop = str(SFX_DIR / "message_pop.wav")
        sfx_triggers = []
        if video_format == "chat":
            for turn in timeline:
                sfx_triggers.append((sfx_pop, turn["start"]))

        if not bgm_path or not Path(bgm_path).exists():
            bgms = list_bgm_tracks()
            if bgms:
                bgm_path = bgms[0]
            else:
                bgm_path = str(MUSIC_DIR / "roblox_chill_lofi.wav")

        # 6. Build Input Stream List and Accurate Indices
        # Input 0: Background Video
        if bg_video_path.endswith(".png"):
            inputs = ["-loop", "1", "-framerate", str(fps), "-i", bg_video_path]
        elif theme == "whatsapp":
            # The whatsapp visuals are exactly the right length, no looping needed
            inputs = ["-i", bg_video_path]
        else:
            inputs = ["-stream_loop", "-1", "-i", bg_video_path]
        next_input_idx = 1

        # Input 1: Speech Audio
        inputs.extend(["-i", speech_audio])
        speech_input_idx = next_input_idx
        next_input_idx += 1

        # Input 2: Background Music (if present)
        bgm_input_idx = None
        if bgm_path and Path(bgm_path).exists():
            inputs.extend(["-stream_loop", "-1", "-i", bgm_path])
            bgm_input_idx = next_input_idx
            next_input_idx += 1

        # Inputs 3..N: SFX files
        sfx_input_indices = []
        for sfx_p, trigger_t in sfx_triggers:
            if Path(sfx_p).exists():
                inputs.extend(["-i", sfx_p])
                sfx_input_indices.append((next_input_idx, trigger_t))
                next_input_idx += 1

        # 7. Build Video Filters
        video_filters = []
        # Background crop to 9:16
        video_filters.append(f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1[bg]")
        last_v_stream = "[bg]"

        if video_format == "chat":
            if theme == "whatsapp":
                # For whatsapp, bubbles are pre-rendered into the background video.
                final_video_stream = last_v_stream
            else:
                current_y = int(height * 0.1)
                # Overlay chat bubbles
                for idx, turn in enumerate(timeline):
                    bubble_png = str(temp_dir / f"bubble_{idx:03d}.png")
                    spk = turn.get("speaker", "Player")
                    txt = turn.get("text", "")
                    av = turn.get("avatar", "")
                    
                    render_roblox_chat_bubble(
                        speaker_name=spk,
                        message_text=txt,
                        avatar_path=av,
                        output_path=bubble_png,
                        canvas_width=width - 120
                    )
                    y_pos = int(height * 0.42)
                        
                    inputs.extend(["-i", bubble_png])
                    bubble_input_idx = next_input_idx
                    next_input_idx += 1

                    start_t = turn["start"]
                    end_t = total_duration + 1.0 if idx == len(timeline) - 1 else timeline[idx + 1]["start"] + 0.1
                    out_stream = f"[v_over_{idx}]"
                    overlay_cmd = f"{last_v_stream}[{bubble_input_idx}:v]overlay=x=(W-w)/2:y={y_pos}:enable='between(t,{start_t:.3f},{end_t:.3f})'{out_stream}"
                    
                    video_filters.append(overlay_cmd)
                    last_v_stream = out_stream

                final_video_stream = last_v_stream

        else: # Storytime mode
            # Render top banner
            banner_png = str(temp_dir / "story_banner.png")
            main_avatar = timeline[0]["avatar"] if timeline else fetch_roblox_avatar("Roblox")
            render_story_header_banner(title, main_avatar, banner_png, width=width - 80)
            inputs.extend(["-i", banner_png])
            banner_input_idx = next_input_idx
            next_input_idx += 1

            # Render ASS subtitles
            ass_path = str(temp_dir / "subtitles.ass")
            generate_animated_ass_subtitles(
                timeline,
                ass_path,
                res_x=width,
                res_y=height,
                font_name="Arial Black",
                font_size=74,
                margin_v=int(height * 0.38)
            )

            # Banner overlay + Subtitle burning
            video_filters.append(f"{last_v_stream}[{banner_input_idx}:v]overlay=x=(W-w)/2:y=120[v_banner]")
            escaped_ass = format_ffmpeg_path(ass_path)
            video_filters.append(f"[v_banner]ass='{escaped_ass}'[v_final]")
            final_video_stream = "[v_final]"

        # 8. Build Audio Mix Filters
        audio_filters = []
        mix_streams = []
        audio_filters.append(f"[{speech_input_idx}:a]volume=1.5[speech_loud]")
        mix_streams.append("[speech_loud]")
        if bgm_input_idx is not None:
            audio_filters.append(f"[{bgm_input_idx}:a]volume=0.14,atrim=0:{total_duration+0.5},asetpts=PTS-STARTPTS[bgm_ducked]")
            mix_streams.append("[bgm_ducked]")

        for sfx_idx, trigger_t in sfx_input_indices:
            delay_ms = int(trigger_t * 1000)
            audio_filters.append(f"[{sfx_idx}:a]volume=0.8,adelay={delay_ms}|{delay_ms},asetpts=PTS-STARTPTS[sfx_{sfx_idx}]")
            mix_streams.append(f"[sfx_{sfx_idx}]")

        if len(mix_streams) > 1:
            audio_filters.append(f"{''.join(mix_streams)}amix=inputs={len(mix_streams)}:duration=first:dropout_transition=2[master_audio]")
            final_audio_stream = "[master_audio]"
        else:
            final_audio_stream = f"[{speech_input_idx}:a]"

        # Apply final volume boost to overall audio
        audio_filters.append(f"{final_audio_stream}volume=1.5[master_loud]")
        final_audio_stream = "[master_loud]"

        # 9. Combine Filters
        full_filter_complex = f"{';'.join(video_filters)};{';'.join(audio_filters)}" if audio_filters else ";".join(video_filters)

        # 10. Select Best Encoder
        enc_name, v_codec_args = detect_best_video_encoder()
        print(f"[Video Composer] Encoder: {enc_name}")

        target_output = OUTPUT_DIR / output_filename

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", full_filter_complex,
            "-map", final_video_stream,
            "-map", final_audio_stream,
            *v_codec_args,
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(total_duration + 0.5),
            "-r", str(fps),
            str(target_output)
        ]

        print(f"[Video Composer] Rendering video to {target_output}...")
        subprocess.run(cmd, check=True)
        print(f"[Video Composer] Video render complete: {target_output}")
        return str(target_output)

    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass


if __name__ == "__main__":
    from core.script_generator import get_template
    tpl = get_template("fake_chat_rich_vs_poor")
    out = render_roblox_video(
        dialogue_or_script=tpl["dialogue"],
        video_format="chat",
        title=tpl["title"],
        output_filename="test_roblox_chat.mp4"
    )
    print(f"Success! Output: {out}")
