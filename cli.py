"""
Roblox Video Studio - Command Line Interface
Batch generate Roblox YouTube Shorts from text or template.
"""

import sys
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.script_generator import BUILTIN_TEMPLATES, parse_raw_dialogue_text
from core.video_composer import render_roblox_video


def main():
    parser = argparse.ArgumentParser(description="Roblox YouTube Short Generator (Local GPU)")
    parser.add_argument("--format", choices=["chat", "storytime"], default="chat", help="Video format (chat or storytime)")
    parser.add_argument("--preset", choices=list(BUILTIN_TEMPLATES.keys()), help="Built-in template to use")
    parser.add_argument("--script", required=True, help="Path to text script")
    parser.add_argument("--output", required=True, help="Output MP4 path")
    parser.add_argument("--title", default="Text Story")
    parser.add_argument("--theme", choices=['whatsapp', 'roblox'], default='roblox')
    parser.add_argument("--language", choices=['english', 'telugu'], default='english')
    parser.add_argument("--char1_ref", help="Reference audio for Character 1 (Self)")
    parser.add_argument("--char2_ref", help="Reference audio for Character 2 (Other)")
    parser.add_argument("--voice_map", help="JSON string mapping characters to voices or indicf5:path")
    parser.add_argument("--fps", type=int, default=60, help="Video frame rate (30 or 60)")
    parser.add_argument("--cpu", action="store_true", help="Force CPU rendering instead of NVENC GPU")

    args = parser.parse_args()

    if args.preset:
        tpl = BUILTIN_TEMPLATES[args.preset]
        dialogue = tpl.get("dialogue") or tpl.get("script")
        fmt = tpl.get("format", args.format)
        title = tpl.get("title", args.title)
    elif args.script:
        with open(args.script, "r", encoding="utf-8-sig") as f:
            script_text = f.read()
        dialogue = parse_raw_dialogue_text(script_text) if args.format == "chat" else script_text
        fmt = args.format
        title = args.title
    else:
        print("No script or preset provided. Using default preset: fake_chat_rich_vs_poor")
        tpl = BUILTIN_TEMPLATES["fake_chat_rich_vs_poor"]
        dialogue = tpl["dialogue"]
        fmt = "chat"
        title = tpl["title"]

    if args.format == "chat":
        import json
        voice_map = {}
        if args.voice_map:
            voice_map = json.loads(args.voice_map)
            
        # Extract unique speakers
        speakers = []
        for line in dialogue:
            if line["speaker"] not in speakers:
                speakers.append(line["speaker"])
                
        self_speaker = speakers[1] if len(speakers) > 1 else speakers[0]
        
        for item in dialogue:
            char = item["speaker"]
            
            if char in voice_map:
                v = voice_map[char]
                if v.startswith("indicf5:"):
                    item["voice"] = "indicf5"
                    item["ref_audio"] = v.split(":", 1)[1]
                else:
                    item["voice"] = v
            else:
                if args.language == "telugu":
                    item["voice"] = "indicf5"
                    item["ref_audio"] = args.char1_ref if char == self_speaker else args.char2_ref
                else:
                    item["voice"] = "en_default"
            
            # Map avatar based on self vs other
            item["avatar"] = "self.png" if item["speaker"] == self_speaker else "other.png"

    print(f"[*] Rendering {fmt} video: '{title}' -> {args.output}")
    out = render_roblox_video(
        dialogue_or_script=dialogue,
        video_format=fmt,
        title=title,
        output_filename=args.output,
        fps=args.fps,
        use_gpu=not args.cpu,
        theme=args.theme
    )
    print(f"[+] Done! Saved video to: {out}")


if __name__ == "__main__":
    main()
