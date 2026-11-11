"""
Script Generator & Parser
Provides viral Roblox story templates, multi-character dialogue parsing, and optional AI story generation.
"""

import re
import json
import random
import requests
from typing import List, Dict, Any, Optional

# Viral Roblox Short Templates
BUILTIN_TEMPLATES = {
    "fake_chat_rich_vs_poor": {
        "title": "Rich Bacon vs Noob",
        "format": "chat",
        "bgm": "roblox_chill_lofi.wav",
        "dialogue": [
            {"speaker": "RichBacon", "voice": "en-US-ChristopherNeural", "text": "Bro, why are you still wearing default noob clothes in 2026?"},
            {"speaker": "Noob", "voice": "en-US-JennyNeural", "text": "Because skill matters more than Robux, Bacon!"},
            {"speaker": "RichBacon", "voice": "en-US-ChristopherNeural", "text": "1v1 me on Tower of Hell right now then. Loser gives 10,000 Robux."},
            {"speaker": "Noob", "voice": "en-US-JennyNeural", "text": "Deal! You're gonna regret this."},
            {"speaker": "RichBacon", "voice": "en-US-ChristopherNeural", "text": "Wait... how did you just speedrun stage 50 in 10 seconds?!"},
            {"speaker": "Noob", "voice": "en-US-JennyNeural", "text": "I told you. Never underestimate the Noob!"}
        ]
    },
    "fake_chat_scammer_caught": {
        "title": "Scammer Caught in 4K",
        "format": "chat",
        "bgm": "roblox_chill_lofi.wav",
        "dialogue": [
            {"speaker": "Guest666", "voice": "en-US-EricNeural", "text": "Trust trade me your Mega Shadow Dragon, I will duplicate it for you!"},
            {"speaker": "CoolGirl", "voice": "en-US-AriaNeural", "text": "Are you sure? What if you scam me?"},
            {"speaker": "Guest666", "voice": "en-US-EricNeural", "text": "Bro I swear on my account, I am an admin in this game!"},
            {"speaker": "CoolGirl", "voice": "en-US-AriaNeural", "text": "Really? Because my dad is literally the creator of Roblox."},
            {"speaker": "Guest666", "voice": "en-US-EricNeural", "text": "Wait what... please don't ban my IP!"},
            {"speaker": "CoolGirl", "voice": "en-US-AriaNeural", "text": "Too late. Enjoy your permanent ban!"}
        ]
    },
    "storytime_scary_glitch": {
        "title": "The Scariest Roblox Glitch",
        "format": "storytime",
        "bgm": "roblox_chill_lofi.wav",
        "speaker": "Robloxian",
        "voice": "en-US-GuyNeural",
        "script": "At 3 AM last night, I joined an empty server in Brookhaven. Everything was pitch black, and all the streetlights were flickering. Suddenly, a player named Guest 666 joined my private house and typed in chat: Don't look behind you. When I turned my camera, my game crashed instantly! Has this glitch ever happened to you?"
    },
    "storytime_secret_badge": {
        "title": "The Impossible 0.01% Badge",
        "format": "storytime",
        "bgm": "roblox_chill_lofi.wav",
        "speaker": "Bacon",
        "voice": "en-US-ChristopherNeural",
        "script": "There is a secret Roblox obby where only 3 players in history have ever reached the top. The jumps are literally pixel-perfect, with invisible lava traps everywhere. After 48 hours of non-stop trying, I finally hit the final button and unlocked the rarest crown in Roblox history!"
    }
}


def parse_raw_dialogue_text(raw_text: str, default_voice: str = "en-US-ChristopherNeural") -> List[Dict[str, Any]]:
    """
    Parses user-entered script in formats like:
    Bacon: Hey what's up!
    Noob: Nothing much, just playing Blox Fruits.
    [Guy]: Narrator line here.
    """
    raw_text = raw_text.replace('\ufeff', '').strip()
    lines = raw_text.split("\n")
    dialogue = []

    # Voice assignment mapping
    speaker_voices = {}
    available_voices = [
        "en-US-ChristopherNeural",
        "en-US-JennyNeural",
        "en-US-EricNeural",
        "en-US-AriaNeural",
        "en-US-GuyNeural",
        "en-GB-RyanNeural",
        "en-US-AnaNeural"
    ]

    for line in lines:
        line = line.strip().replace('\ufeff', '')
        if not line:
            continue

        # Match "Speaker: Text" or "[Speaker]: Text"
        match = re.match(r"^\[?([^\:\]\n]{1,32})\]?\s*:\s*(.+)$", line)
        if match:
            speaker = match.group(1).strip()
            text = match.group(2).strip()
        else:
            speaker = "Narrator"
            text = line

        # Assign unique voice to speaker if not mapped
        if speaker not in speaker_voices:
            idx = len(speaker_voices) % len(available_voices)
            # Detect gender cues in name
            lower_s = speaker.lower()
            if any(w in lower_s for w in ["girl", "jenny", "princess", "queen", "mom", "sis"]):
                speaker_voices[speaker] = "en-US-JennyNeural"
            elif any(w in lower_s for w in ["narrator", "host", "god", "announcer"]):
                speaker_voices[speaker] = "en-US-GuyNeural"
            elif any(w in lower_s for w in ["kid", "baby", "boy", "noob"]):
                speaker_voices[speaker] = "en-US-AnaNeural"
            else:
                speaker_voices[speaker] = available_voices[idx]

        dialogue.append({
            "speaker": speaker,
            "voice": speaker_voices[speaker],
            "text": text
        })

    return dialogue


def generate_ai_script(
    topic: str,
    format_type: str = "chat",
    ollama_url: str = "http://localhost:11434/api/generate",
    model: str = "llama3.2:3b"
) -> Optional[str]:
    """
    Generates a viral Roblox script using a local Ollama LLM if running.
    """
    if format_type == "chat":
        system_prompt = (
            "Write a viral, high-energy 45-second Roblox fake chat dialogue between two players (e.g. Bacon and Noob). "
            "Format each line as 'Speaker: Dialogue'. Keep sentences short, funny, punchy, and engaging for YouTube Shorts. "
            f"Topic: {topic}"
        )
    else:
        system_prompt = (
            "Write a viral, dramatic 45-second Roblox storytime narration script for YouTube Shorts. "
            "Make it exciting, intense, with a hook in the first 3 seconds and a question at the end. "
            f"Topic: {topic}"
        )

    try:
        payload = {
            "model": model,
            "prompt": system_prompt,
            "stream": False
        }
        resp = requests.post(ollama_url, json=payload, timeout=20)
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[Script Generator] Ollama generation skipped: {e}")

    return None


def get_template_keys() -> List[str]:
    """Returns list of template IDs."""
    return list(BUILTIN_TEMPLATES.keys())


def get_template(key: str) -> Dict[str, Any]:
    """Retrieves a specific template."""
    return BUILTIN_TEMPLATES.get(key, BUILTIN_TEMPLATES["fake_chat_rich_vs_poor"])
