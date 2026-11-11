"""
Caption Engine
Generates high-energy, animated ASS subtitles with dynamic word-by-word highlighting (MrBeast/Roblox style).
"""

import math
from pathlib import Path
from typing import List, Dict, Any, Optional

ASS_HEADER = """[Script Info]
Title: Roblox Shorts Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},{secondary_color},{outline_color},{back_color},-1,0,0,0,100,100,1,0,1,{outline_size},{shadow_size},{alignment},{margin_l},{margin_r},{margin_v},1
Style: Highlight,{font_name},{font_size},{highlight_color},{secondary_color},{outline_color},{back_color},-1,0,0,0,108,108,1,0,1,{outline_size},{shadow_size},{alignment},{margin_l},{margin_r},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def format_ass_time(seconds: float) -> str:
    """Converts seconds into ASS timestamp format H:MM:SS.cc"""
    if seconds < 0:
        seconds = 0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hrs:d}:{mins:02d}:{secs:02d}.{centis:02d}"


def hex_to_ass_color(hex_color: str, alpha: str = "00") -> str:
    """
    Converts #RRGGBB to ASS &HAABBGGRR color format.
    Example: #FFD700 (Gold) -> &H0000D7FF
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        r = hex_color[0:2]
        g = hex_color[2:4]
        b = hex_color[4:6]
        return f"&H{alpha}{b}{g}{r}&".upper()
    return f"&H{alpha}FFFFFF&"


def group_words_into_phrases(
    words: List[Dict[str, Any]],
    max_words_per_phrase: int = 3,
    max_duration_per_phrase: float = 1.6
) -> List[List[Dict[str, Any]]]:
    """
    Groups a stream of timestamped words into short, energetic visual chunks (1-3 words).
    """
    if not words:
        return []

    phrases = []
    current_phrase = []

    for w in words:
        if not current_phrase:
            current_phrase.append(w)
            continue

        phrase_duration = w["end"] - current_phrase[0]["start"]
        gap = w["start"] - current_phrase[-1]["end"]

        # Check if punctuation suggests a split or limit reached
        ends_sentence = any(current_phrase[-1]["word"].endswith(p) for p in [".", "!", "?", ","])

        if len(current_phrase) >= max_words_per_phrase or phrase_duration > max_duration_per_phrase or gap > 0.4 or ends_sentence:
            phrases.append(current_phrase)
            current_phrase = [w]
        else:
            current_phrase.append(w)

    if current_phrase:
        phrases.append(current_phrase)

    return phrases


def generate_animated_ass_subtitles(
    timeline_or_words: List[Any],
    output_ass_path: str,
    res_x: int = 1080,
    res_y: int = 1920,
    font_name: str = "Arial Black",
    font_size: int = 72,
    highlight_color_hex: str = "#FFD700",  # Bright Yellow/Gold
    base_color_hex: str = "#FFFFFF",       # Pure White
    outline_color_hex: str = "#000000",    # Deep Black border
    margin_v: int = 680,                  # Vertical position (centered-bottom)
    alignment: int = 2,                    # Bottom-center
    max_words_per_chunk: int = 3
) -> str:
    """
    Generates word-highlighted ASS subtitle script.
    Accepts either a list of words or dialogue timeline objects.
    """
    # Extract flat list of words with timestamps
    all_words = []
    if timeline_or_words and isinstance(timeline_or_words[0], dict) and "words" in timeline_or_words[0]:
        for turn in timeline_or_words:
            all_words.extend(turn.get("words", []))
    else:
        all_words = timeline_or_words

    if not all_words:
        # Generate minimal empty ASS
        content = ASS_HEADER.format(
            res_x=res_x, res_y=res_y,
            font_name=font_name, font_size=font_size,
            primary_color=hex_to_ass_color(base_color_hex),
            highlight_color=hex_to_ass_color(highlight_color_hex),
            secondary_color="&H000000FF&",
            outline_color=hex_to_ass_color(outline_color_hex),
            back_color="&H80000000&",
            outline_size=8, shadow_size=4,
            alignment=alignment, margin_l=40, margin_r=40, margin_v=margin_v
        )
        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_ass_path

    primary_color = hex_to_ass_color(base_color_hex)
    highlight_color = hex_to_ass_color(highlight_color_hex)
    outline_color = hex_to_ass_color(outline_color_hex)
    back_color = "&H80000000&"

    header = ASS_HEADER.format(
        res_x=res_x,
        res_y=res_y,
        font_name=font_name,
        font_size=font_size,
        primary_color=primary_color,
        highlight_color=highlight_color,
        secondary_color="&H000000FF&",
        outline_color=outline_color,
        back_color=back_color,
        outline_size=7,
        shadow_size=4,
        alignment=alignment,
        margin_l=40,
        margin_r=40,
        margin_v=margin_v
    )

    phrases = group_words_into_phrases(all_words, max_words_per_phrase=max_words_per_chunk)
    dialogue_events = []

    for phrase in phrases:
        if not phrase:
            continue
        phrase_start = phrase[0]["start"]
        phrase_end = phrase[-1]["end"]

        # For each active word in the phrase, create a slice where that word is highlighted
        for active_idx, target_word in enumerate(phrase):
            w_start = target_word["start"]
            w_end = target_word["end"]

            # If there's a next word, end at next word start to avoid gaps
            if active_idx < len(phrase) - 1:
                w_end = phrase[active_idx + 1]["start"]

            # Build line text with the active word in uppercase + highlight color tag
            line_parts = []
            for idx, w in enumerate(phrase):
                clean_w = w["word"].strip().upper()
                if idx == active_idx:
                    # Active word: pop effect and highlight color
                    line_parts.append(r"{\c" + highlight_color + r"\fscx112\fscy112}" + clean_w + r"{\r}")
                else:
                    line_parts.append(r"{\c" + primary_color + r"\fscx100\fscy100}" + clean_w + r"{\r}")

            formatted_text = " ".join(line_parts)
            dialogue_events.append(
                f"Dialogue: 0,{format_ass_time(w_start)},{format_ass_time(w_end)},Default,,0,0,0,,{formatted_text}"
            )

    full_ass_content = header + "\n".join(dialogue_events) + "\n"

    Path(output_ass_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(full_ass_content)

    return output_ass_path


if __name__ == "__main__":
    test_words = [
        {"word": "Welcome", "start": 0.0, "end": 0.4},
        {"word": "to", "start": 0.4, "end": 0.6},
        {"word": "the", "start": 0.6, "end": 0.8},
        {"word": "most", "start": 0.8, "end": 1.2},
        {"word": "intense", "start": 1.2, "end": 1.6},
        {"word": "Roblox", "start": 1.6, "end": 2.0},
        {"word": "obby!", "start": 2.0, "end": 2.5},
    ]
    out = generate_animated_ass_subtitles(test_words, "test_subs.ass")
    print(f"Generated animated ASS subtitles at {out}")
