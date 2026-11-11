"""
Roblox API Integration
Fetches official Roblox user avatar headshots, usernames, and profile data with local caching.
"""

import os
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Dict, Tuple

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
AVATARS_DIR = ASSETS_DIR / "avatars"

DEFAULT_PRESETS = {
    "Bacon": {
        "username": "PalHair_Bacon",
        "color": (230, 160, 40),
        "desc": "Classic Bacon Hair"
    },
    "Noob": {
        "username": "Classic_Noob",
        "color": (255, 225, 50),
        "desc": "Yellow/Blue Classic Noob"
    },
    "Guest666": {
        "username": "Guest_666",
        "color": (220, 40, 40),
        "desc": "Creepy Roblox Guest"
    },
    "RichBacon": {
        "username": "Rich_Bacon",
        "color": (50, 205, 50),
        "desc": "Dominus Flexer"
    },
    "CoolGirl": {
        "username": "Roblox_Girl",
        "color": (255, 105, 180),
        "desc": "Stylish Roblox Girl"
    },
    "Roblox": {
        "username": "Roblox",
        "color": (0, 162, 255),
        "desc": "Official Roblox"
    },
    "Builderman": {
        "username": "Builderman",
        "color": (255, 140, 0),
        "desc": "Roblox Founder Builderman"
    }
}


def ensure_dirs():
    """Ensure asset directories exist."""
    AVATARS_DIR.mkdir(parents=True, exist_ok=True)


def get_user_id_by_username(username: str) -> Optional[int]:
    """Look up Roblox user ID via public Roblox API."""
    try:
        url = "https://users.roblox.com/v1/usernames/users"
        payload = {"usernames": [username], "excludeBannedUsers": False}
        resp = requests.post(url, json=payload, timeout=6)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            if data and len(data) > 0:
                return data[0].get("id")
    except Exception as e:
        print(f"[Roblox API] Error looking up user {username}: {e}")
    return None


def fetch_roblox_avatar(username: str, force_refresh: bool = False) -> str:
    """
    Fetches and caches the headshot thumbnail for a given Roblox username.
    Returns the absolute path to the cached PNG.
    Falls back to a styled procedural avatar if the user doesn't exist or if offline.
    """
    ensure_dirs()
    sanitized_name = "".join(c for c in username if c.isalnum() or c in ("_", "-")).strip()
    if not sanitized_name:
        sanitized_name = "Player"

    cache_path = AVATARS_DIR / f"{sanitized_name}.png"
    if cache_path.exists() and not force_refresh:
        return str(cache_path)

    # 1. Try Roblox API lookup
    user_id = get_user_id_by_username(username)
    if user_id:
        try:
            thumb_url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=false"
            thumb_resp = requests.get(thumb_url, timeout=6)
            if thumb_resp.status_code == 200:
                items = thumb_resp.json().get("data", [])
                if items and items[0].get("imageUrl"):
                    img_url = items[0]["imageUrl"]
                    img_data = requests.get(img_url, timeout=10).content
                    with open(cache_path, "wb") as f:
                        f.write(img_data)
                    print(f"[Roblox API] Cached real avatar for {username} -> {cache_path}")
                    return str(cache_path)
        except Exception as e:
            print(f"[Roblox API] Failed to fetch thumbnail for {username}: {e}")

    # 2. Fallback: generate high-res stylized Roblox avatar placeholder
    create_procedural_avatar(sanitized_name, str(cache_path))
    return str(cache_path)


def create_procedural_avatar(username: str, output_path: str, size: int = 420):
    """Creates a colorful, iconic Roblox-themed avatar icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Hash username for consistent color
    hash_val = sum(ord(c) for c in username)
    colors = [
        ((255, 205, 0), (0, 110, 220)),   # Noob yellow / blue
        ((230, 160, 40), (50, 50, 50)),   # Bacon hair brown / gray
        ((255, 105, 180), (147, 112, 219)),# Pink / Purple
        ((0, 200, 115), (30, 40, 60)),    # Green / Dark
        ((230, 50, 50), (20, 20, 20)),    # Red / Black
        ((0, 162, 255), (255, 255, 255)), # Roblox Blue / White
    ]
    bg_color, accent_color = colors[hash_val % len(colors)]

    # Draw rounded background circle/square
    draw.rounded_rectangle([10, 10, size - 10, size - 10], radius=80, fill=bg_color, outline=(255, 255, 255, 200), width=8)

    # Draw stylized blocky Roblox head
    head_w, head_h = 200, 200
    head_x = (size - head_w) // 2
    head_y = 70
    draw.rectangle([head_x, head_y, head_x + head_w, head_y + head_h], fill=(255, 225, 100), outline=(40, 40, 40), width=6)

    # Eyes (classic Roblox dots)
    eye_size = 18
    draw.ellipse([head_x + 45, head_y + 70, head_x + 45 + eye_size, head_y + 70 + eye_size], fill=(20, 20, 20))
    draw.ellipse([head_x + 135, head_y + 70, head_x + 135 + eye_size, head_y + 70 + eye_size], fill=(20, 20, 20))

    # Smile (classic Roblox smile)
    draw.arc([head_x + 55, head_y + 80, head_x + 145, head_y + 140], start=20, end=160, fill=(20, 20, 20), width=6)

    # Torso peak at bottom
    draw.rectangle([head_x - 30, head_y + head_h + 10, head_x + head_w + 30, size - 15], fill=accent_color, outline=(40, 40, 40), width=6)

    img.save(output_path, "PNG")
    return output_path


def get_available_presets() -> Dict[str, dict]:
    """Returns preset character configs."""
    return DEFAULT_PRESETS


if __name__ == "__main__":
    ensure_dirs()
    # Test fetch
    p = fetch_roblox_avatar("Roblox")
    print(f"Roblox avatar saved to: {p}")
    p2 = fetch_roblox_avatar("Builderman")
    print(f"Builderman avatar saved to: {p2}")
