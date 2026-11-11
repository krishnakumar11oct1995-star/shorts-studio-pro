import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Optional, Tuple, List, Dict, Any

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
AVATARS_DIR = ASSETS_DIR / "avatars"

SPEAKER_COLORS = {
    "Bacon": (255, 180, 50),
    "Noob": (255, 230, 0),
    "Girl": (255, 120, 190),
    "Pro": (0, 230, 120),
    "Hacker": (255, 60, 60),
    "Roblox": (0, 162, 255),
    "Narrator": (200, 200, 255),
    "Guest": (220, 50, 50),
    "Rich": (50, 220, 120),
}

def get_font(size: int = 32, bold: bool = False) -> ImageFont.FreeTypeFont:
    nirmala_path = Path("C:/Windows/Fonts/Nirmala.ttc")
    if nirmala_path.exists():
        try:
            return ImageFont.truetype(str(nirmala_path), size, index=1 if bold else 0)
        except Exception:
            pass

    font_candidates = [
        FONTS_DIR / "Montserrat-ExtraBold.ttf",
        FONTS_DIR / "GothamBold.ttf",
        FONTS_DIR / "Roboto-Bold.ttf",
        Path("C:/Windows/Fonts/segoeuib.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
    ]
    for p in font_candidates:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default()

def get_regular_font(size: int = 28) -> ImageFont.FreeTypeFont:
    nirmala_path = Path("C:/Windows/Fonts/Nirmala.ttc")
    if nirmala_path.exists():
        try:
            return ImageFont.truetype(str(nirmala_path), size, index=0)
        except Exception:
            pass

    font_candidates = [
        Path("C:/Windows/Fonts/segoeui.ttf"),
        FONTS_DIR / "Montserrat-Medium.ttf",
        FONTS_DIR / "Montserrat-Bold.ttf",
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for p in font_candidates:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return get_font(size)

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    words = text.split()
    if not words: return [""]
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def crop_circular_avatar(avatar_path: str, size: int = 90) -> Image.Image:
    if not Path(avatar_path).exists():
        base = Image.new("RGBA", (size, size), (0, 162, 255, 255))
    else:
        try:
            base = Image.open(avatar_path).convert("RGBA")
            base = base.resize((size, size), Image.Resampling.LANCZOS)
        except Exception:
            base = Image.new("RGBA", (size, size), (0, 162, 255, 255))
    mask = Image.new("L", (size * 4, size * 4), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    mask = mask.resize((size, size), Image.Resampling.LANCZOS)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(base, (0, 0), mask=mask)
    return output

def render_roblox_chat_bubble(
    speaker_name: str,
    message_text: str,
    avatar_path: str,
    output_path: str,
    canvas_width: int = 960,
    theme: str = "dark",
    is_verified: bool = True
) -> Tuple[int, int]:
    if theme == "dark":
        bg_color = (25, 28, 34, 235)
        border_color = (60, 65, 75, 255)
        text_color = (255, 255, 255, 255)
        handle_color = (170, 175, 185, 255)
    else:
        bg_color = (255, 255, 255, 245)
        border_color = (210, 215, 225, 255)
        text_color = (20, 20, 25, 255)
        handle_color = (100, 105, 115, 255)

    accent_color = (0, 162, 255, 255)
    for k, col in SPEAKER_COLORS.items():
        if k.lower() in speaker_name.lower():
            accent_color = (*col, 255)
            break

    name_font = get_font(size=34, bold=True)
    text_font = get_regular_font(size=30)
    handle_font = get_regular_font(size=22)

    avatar_size = 96
    padding = 24
    inner_spacing = 20
    text_max_width = canvas_width - (padding * 2 + avatar_size + inner_spacing + 30)

    lines = wrap_text(message_text, text_font, text_max_width)
    line_height = 38
    text_block_height = max(len(lines) * line_height, 40)

    header_height = 42

    content_height = max(avatar_size, header_height + text_block_height + 8)
    bubble_height = content_height + (padding * 2)
    bubble_width = canvas_width

    shadow_margin = 12
    img_w = bubble_width + (shadow_margin * 2)
    img_h = bubble_height + (shadow_margin * 2)
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))

    shadow = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_rect = [
        shadow_margin,
        shadow_margin + 6,
        shadow_margin + bubble_width,
        shadow_margin + bubble_height + 6
    ]
    s_draw.rounded_rectangle(s_rect, radius=24, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=8))
    img.paste(shadow, (0, 0), mask=shadow)

    draw = ImageDraw.Draw(img)
    bubble_rect = [
        shadow_margin,
        shadow_margin,
        shadow_margin + bubble_width,
        shadow_margin + bubble_height
    ]
    draw.rounded_rectangle(bubble_rect, radius=24, fill=bg_color, outline=border_color, width=3)

    avatar_img = crop_circular_avatar(avatar_path, size=avatar_size)
    avatar_x = shadow_margin + padding
    avatar_y = shadow_margin + padding + (content_height - avatar_size) // 2

    draw.ellipse(
        [avatar_x - 3, avatar_y - 3, avatar_x + avatar_size + 3, avatar_y + avatar_size + 3],
        outline=accent_color,
        width=3
    )
    img.paste(avatar_img, (avatar_x, avatar_y), mask=avatar_img)

    content_x = avatar_x + avatar_size + inner_spacing
    content_y = shadow_margin + padding + 4

    draw.text((content_x, content_y), speaker_name, font=name_font, fill=accent_color)
    name_bbox = name_font.getbbox(speaker_name)
    name_w = name_bbox[2] - name_bbox[0]

    if is_verified:
        badge_x = content_x + name_w + 10
        badge_y = content_y + 6
        badge_size = 22
        draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], fill=(0, 162, 255))
        draw.line([badge_x + 5, badge_y + 11, badge_x + 9, badge_y + 15], fill=(255, 255, 255), width=2)
        draw.line([badge_x + 9, badge_y + 15, badge_x + 16, badge_y + 7], fill=(255, 255, 255), width=2)

    handle_text = f"@{speaker_name.lower().replace(' ', '_')}"
    draw.text((content_x + name_w + 42 if is_verified else content_x + name_w + 12, content_y + 8), handle_text, font=handle_font, fill=handle_color)

    text_start_y = content_y + header_height
    for idx, line in enumerate(lines):
        draw.text(
            (content_x, text_start_y + (idx * line_height)),
            line,
            font=text_font,
            fill=text_color
        )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return img_w, img_h

def render_story_header_banner(
    title: str,
    avatar_path: str,
    output_path: str,
    width: int = 1000
) -> Tuple[int, int]:
    banner_height = 140
    img = Image.new("RGBA", (width, banner_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([10, 10, width - 10, banner_height - 10], radius=35, fill=(18, 20, 26, 230), outline=(255, 215, 0, 200), width=4)

    av_size = 90
    avatar_img = crop_circular_avatar(avatar_path, size=av_size)
    img.paste(avatar_img, (30, 25), mask=avatar_img)

    font = get_font(size=36, bold=True)
    draw.text((145, 48), title, font=font, fill=(255, 255, 255))

    img.save(output_path, "PNG")
    return width, banner_height

def generate_whatsapp_background(output_path: str, width: int = 1080, height: int = 1920):
    img = Image.new("RGBA", (width, height), (229, 221, 213, 255))
    img.save(output_path, "PNG")

def render_whatsapp_chat_bubble(
    speaker_name: str,
    message_text: str,
    output_path: str,
    is_self: bool = False,
    canvas_width: int = 1080,
    timestamp: str = "11:42 PM"
) -> Tuple[int, int]:
    # Android WhatsApp Dark Mode Colors
    bg_color = (0, 92, 75, 255) if is_self else (32, 44, 51, 255)
    text_color = (233, 237, 239, 255)
    time_color = (134, 150, 160, 255)
    
    text_font = get_regular_font(size=32)
    time_font = get_regular_font(size=20)
    
    padding_x = 24
    padding_y = 16
    max_bubble_width = int(canvas_width * 0.75)
    text_max_width = max_bubble_width - (padding_x * 2)
    
    lines = wrap_text(message_text, text_font, text_max_width)
    line_height = 40
    text_block_height = len(lines) * line_height
    
    max_line_width = 0
    for line in lines:
        bbox = text_font.getbbox(line)
        max_line_width = max(max_line_width, bbox[2] - bbox[0])
        
    time_bbox = time_font.getbbox(timestamp)
    time_width = time_bbox[2] - time_bbox[0]
    
    # Add extra space for the time/ticks inline at the bottom right
    # To keep it simple, we always put time at the bottom right of the LAST line
    bubble_width = max(max_line_width, time_width * 2) + (padding_x * 2) + 40
    bubble_height = text_block_height + padding_y * 2 + 10
    
    img = Image.new("RGBA", (canvas_width, bubble_height + 15), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    margin = 35
    if is_self:
        x_offset = canvas_width - bubble_width - margin
    else:
        x_offset = margin
        
    y_offset = 0
    
    bubble_rect = [x_offset, y_offset, x_offset + bubble_width, y_offset + bubble_height]
    draw.rounded_rectangle(bubble_rect, radius=24, fill=bg_color)
    
    # Android tail comes from the TOP corner
    if is_self:
        draw.polygon([
            (x_offset + bubble_width - 15, y_offset),
            (x_offset + bubble_width + 15, y_offset),
            (x_offset + bubble_width - 15, y_offset + 25)
        ], fill=bg_color)
    else:
        draw.polygon([
            (x_offset + 15, y_offset),
            (x_offset - 15, y_offset),
            (x_offset + 15, y_offset + 25)
        ], fill=bg_color)
        
    text_y = y_offset + padding_y
    for idx, line in enumerate(lines):
        draw.text((x_offset + padding_x, text_y + (idx * line_height)), line, font=text_font, fill=text_color)
        
    time_x = x_offset + bubble_width - padding_x - time_width + 10
    time_y = y_offset + bubble_height - 28
    draw.text((time_x, time_y), timestamp, font=time_font, fill=time_color)
    
    if is_self:
        tick_x = time_x - 30
        tick_y = time_y + 5
        draw.line([tick_x, tick_y+5, tick_x+5, tick_y+10, tick_x+12, tick_y], fill=(83, 189, 235, 255), width=3)
        draw.line([tick_x+7, tick_y+5, tick_x+12, tick_y+10, tick_x+19, tick_y], fill=(83, 189, 235, 255), width=3)
        
    img.save(output_path, "PNG")
    return canvas_width, bubble_height + 15
