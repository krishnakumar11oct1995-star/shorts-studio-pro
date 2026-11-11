import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright

from core.chat_renderer import render_whatsapp_chat_bubble, get_font, get_regular_font, crop_circular_avatar

def generate_ui_assets(contact_name: str, avatar_path: str):
    html_content = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=1080, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Telugu:wght@400;500;600&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Roboto', 'Noto Sans Telugu', sans-serif;
                background-color: transparent;
                color: #e9edef;
                margin: 0;
                padding: 0;
                width: 1080px;
            }}
            .status-bar {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                height: 70px;
                background-color: #0b141a;
                padding: 0 40px;
                font-size: 32px;
                font-weight: 500;
                color: rgba(255, 255, 255, 0.9);
            }}
            .status-right {{
                display: flex;
                align-items: center;
                gap: 16px;
            }}
            .status-right svg {{
                width: 38px;
                height: 38px;
                fill: currentColor;
            }}
            .header {{
                display: flex;
                align-items: center;
                background-color: #0b141a;
                height: 140px;
                padding: 0 16px;
                box-sizing: border-box;
            }}
            .back-btn {{
                display: flex;
                align-items: center;
                margin-right: 8px;
            }}
            .avatar {{
                width: 90px;
                height: 90px;
                border-radius: 50%;
                background-color: #6c757d;
                margin-right: 24px;
                object-fit: cover;
            }}
            .contact-info {{
                flex-grow: 1;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }}
            .contact-name {{
                font-size: 44px;
                font-weight: 500;
                line-height: 1.2;
                color: #e9edef;
                overflow: hidden;
                white-space: nowrap;
                text-overflow: ellipsis;
                max-width: 500px;
            }}
            .status {{
                font-size: 28px;
                color: #8696a0;
                line-height: 1.2;
            }}
            .header-icons {{
                display: flex;
                align-items: center;
                gap: 48px;
                color: #e9edef;
                margin-right: 16px;
            }}
            
            .footer {{
                display: flex;
                align-items: flex-end;
                background-color: transparent;
                padding: 16px;
                box-sizing: border-box;
                width: 1080px;
            }}
            .input-pill {{
                flex-grow: 1;
                background-color: #1f2c34;
                border-radius: 48px;
                display: flex;
                align-items: center;
                padding: 16px 24px;
                margin-right: 16px;
                min-height: 100px;
            }}
            .pill-icons {{
                display: flex;
                align-items: center;
                gap: 40px;
                color: #8696a0;
            }}
            .message-text {{
                flex-grow: 1;
                font-size: 38px;
                color: #8696a0;
                margin-left: 24px;
                margin-right: 24px;
            }}
            .mic-btn {{
                width: 100px;
                height: 100px;
                border-radius: 50%;
                background-color: #00a884;
                display: flex;
                justify-content: center;
                align-items: center;
                color: #111b21;
                flex-shrink: 0;
            }}
            
            svg {{
                width: 52px;
                height: 52px;
                fill: currentColor;
            }}
        </style>
    </head>
    <body>
        <!-- HEADER ID for screenshot -->
        <div id="wa-header-container">
            <div class="status-bar">
                <div class="time">11:42</div>
                <div class="status-right">
                    <!-- Wifi -->
                    <svg viewBox="0 0 24 24"><path d="M12.01 21.49L23.64 7c-.45-.34-4.93-4-11.64-4C5.28 3 .81 6.66.36 7l11.63 14.49.01.01.01-.01z"/></svg>
                    <!-- Signal -->
                    <svg viewBox="0 0 24 24"><path d="M2 22h20V2z"/></svg>
                    <!-- Battery -->
                    <svg viewBox="0 0 24 24"><path d="M15.67 4H14V2h-4v2H8.33C7.6 4 7 4.6 7 5.33v15.33C7 21.4 7.6 22 8.33 22h7.33c.74 0 1.34-.6 1.34-1.33V5.33C17 4.6 16.4 4 15.67 4z"/></svg>
                </div>
            </div>
            <div class="header">
                <div class="back-btn">
                    <svg viewBox="0 0 24 24"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
                </div>
            <!-- The avatar will be rendered by PIL, so we just put a placeholder that matches bg -->
            <div class="avatar" style="background-color: transparent;"></div>
            <div class="contact-info">
                <div class="contact-name" id="contact-name">{contact_name}</div>
                <div class="status" id="contact-status">online</div>
            </div>
            <div class="header-icons">
                <svg viewBox="0 0 24 24"><path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4zM15 16H5V8h10v8z"/></svg>
                <svg viewBox="0 0 24 24"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
                <svg viewBox="0 0 24 24"><path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/></svg>
            </div>
        </div>
        </div>
        
        <!-- FOOTER ID for screenshot -->
        <div id="wa-footer" class="footer">
            <div class="input-pill">
                <div class="pill-icons">
                    <svg viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S8.33 8 7.5 8 6 8.67 6 9.5 6.67 11 7.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H7.89c.8 2.04 2.78 3.5 5.11 3.5z"/></svg>
                </div>
                <div class="message-text">Message</div>
                <div class="pill-icons">
                    <svg viewBox="0 0 24 24" style="transform: rotate(45deg);"><path d="M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5c0-1.38 1.12-2.5 2.5-2.5s2.5 1.12 2.5 2.5v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5c0 1.38 1.12 2.5 2.5 2.5s2.5-1.12 2.5-2.5V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.04 2.46 5.5 5.5 5.5s5.5-2.46 5.5-5.5V6h-1.5z"/></svg>
                    <svg viewBox="0 0 24 24"><path d="M9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.65 0-3 1.35-3 3s1.35 3 3 3 3-1.35 3-3-1.35-3-3-3z"/></svg>
                </div>
            </div>
            <div class="mic-btn">
                <svg style="width: 48px; height: 48px; fill: white;" viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.91-3c-.49 0-.9.36-.98.85C16.52 14.2 14.47 16 12 16s-4.52-1.8-4.93-4.15c-.08-.49-.49-.85-.98-.85-.61 0-1.09.54-1 1.14.49 3 2.89 5.35 5.91 5.78V20c0 .55.45 1 1 1s1-.45 1-1v-2.08c3.02-.43 5.42-2.78 5.91-5.78.1-.6-.39-1.14-1-1.14z"/></svg>
            </div>
        </div>
    </body>
    </html>
    '''
    
    html_path = 'C:/Users/Krishna/Downloads/Youtube/assets/temp_ui.html'
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("[WhatsApp Renderer] Generating UI assets via Playwright...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1080, "height": 1920})
            page.goto(f"file:///{html_path}")
            
            header = page.locator("#wa-header-container")
            
            for m in [42, 43, 44]:
                page.evaluate(f'document.querySelector(".time").innerText = "11:{m}"')
                page.evaluate('document.getElementById("contact-status").innerText = "online"')
                header.screenshot(path=f"C:/Users/Krishna/Downloads/Youtube/assets/header_online_11_{m}.png")
                page.evaluate('document.getElementById("contact-status").innerText = "typing..."')
                header.screenshot(path=f"C:/Users/Krishna/Downloads/Youtube/assets/header_typing_11_{m}.png")
                
            footer = page.locator("#wa-footer")
            page.evaluate('document.getElementById("wa-footer").style.backgroundColor = "transparent"')
            page.evaluate('document.body.style.backgroundColor = "transparent"')
            footer.screenshot(path="C:/Users/Krishna/Downloads/Youtube/assets/footer.png", omit_background=True)
            
            browser.close()
    except Exception as e:
        print(f"[WhatsApp Renderer] Playwright failed: {e}")
        
    assets = {}
    try:
        for m in [42, 43, 44]:
            assets[f'header_online_11_{m}'] = Image.open(f'C:/Users/Krishna/Downloads/Youtube/assets/header_online_11_{m}.png').convert("RGBA")
            assets[f'header_typing_11_{m}'] = Image.open(f'C:/Users/Krishna/Downloads/Youtube/assets/header_typing_11_{m}.png').convert("RGBA")
        assets['footer'] = Image.open('C:/Users/Krishna/Downloads/Youtube/assets/footer.png').convert("RGBA")
    except Exception as e:
        print(f"Error loading UI assets: {e}")
        assets['footer'] = None
    return assets

def render_dynamic_whatsapp_video(
    timeline: List[Dict[str, Any]],
    total_duration: float,
    temp_dir: str,
    output_video_path: str,
    width: int = 1080,
    height: int = 1920,
    fps: int = 60
):
    print("[WhatsApp Renderer] Preparing dynamic frames...")
    bubbles = []
    current_y = 0
    padding_between = 20
    
    self_speaker = timeline[0].get("speaker", "Player") if timeline else "Player"
    other_speaker = next((t.get("speaker") for t in timeline if t.get("speaker") != self_speaker), "Contact")
    other_avatar = next((t.get("avatar") for t in timeline if t.get("speaker") != self_speaker), "")
    
    # Generate UI Assets dynamically
    ui_assets = generate_ui_assets(other_speaker, other_avatar)
    
    for idx, turn in enumerate(timeline):
        bubble_png = str(Path(temp_dir) / f"bubble_{idx:03d}.png")
        spk = turn.get("speaker", "Player")
        txt = turn.get("text", "")
        
        is_self = (spk == self_speaker)
        
        # dynamic time
        # Let's say 1 minute in real time = 1 minute in video time
        # start at 11:42
        m = 42 + int(turn["start"] / 60.0)
        m = min(m, 44)
        time_text = f"11:{m} PM"
        
        _, bh = render_whatsapp_chat_bubble(
            speaker_name=spk,
            message_text=txt,
            output_path=bubble_png,
            is_self=is_self,
            canvas_width=width,
            timestamp=time_text
        )
        
        img = Image.open(bubble_png).convert("RGBA")
        
        bubbles.append({
            "img": img,
            "y": current_y,
            "h": bh,
            "start": turn["start"],
            "speaker": spk
        })
        current_y += bh + padding_between
        
    bg_img = None
    try:
        wallpaper_path = "C:/Users/Krishna/Downloads/Youtube/assets/backgrounds/wa_dark.jpg"
        if os.path.exists(wallpaper_path):
            bg_img = Image.open(wallpaper_path).convert("RGBA")
            bg_aspect = bg_img.width / bg_img.height
            canvas_aspect = width / height
            if bg_aspect > canvas_aspect:
                new_w = int(height * bg_aspect)
                bg_img = bg_img.resize((new_w, height), Image.Resampling.LANCZOS)
                offset = (new_w - width) // 2
                bg_img = bg_img.crop((offset, 0, offset + width, height))
            else:
                new_h = int(width / bg_aspect)
                bg_img = bg_img.resize((width, new_h), Image.Resampling.LANCZOS)
                offset = (new_h - height) // 2
                bg_img = bg_img.crop((0, offset, width, offset + height))
            
            dark_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 150))
            bg_img = Image.alpha_composite(bg_img, dark_overlay)
    except Exception as e:
        print("Failed to load background:", e)
        bg_img = Image.new("RGBA", (width, height), (11, 20, 26, 255))
        
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "rgba",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        output_video_path
    ]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    
    total_frames = int((total_duration + 1.0) * fps)
    
    current_scroll = 0.0
    target_scroll = 0.0
    header_h = ui_assets.get('header_online_11_42', None).height if ui_assets.get('header_online_11_42') else 200
    footer_h = ui_assets['footer'].height if ui_assets['footer'] else 140
    bottom_margin = footer_h + 30
    
    date_badge = Image.new("RGBA", (width, 80), (0, 0, 0, 0))
    db_draw = ImageDraw.Draw(date_badge)
    db_font = get_regular_font(24)
    db_text = "Today"
    db_w = db_font.getlength(db_text)
    db_x = (width - db_w) // 2
    db_draw.rounded_rectangle([db_x - 20, 20, db_x + db_w + 20, 60], radius=15, fill=(24, 34, 41, 255))
    db_draw.text((db_x, 26), db_text, font=db_font, fill=(134, 150, 160, 255))
    
    for frame_idx in range(total_frames):
        t = frame_idx / fps
        
        visible_bubbles = []
        max_y_visible = 0
        current_speaker_typing = None
        
        for idx, b in enumerate(bubbles):
            if t >= b["start"]:
                visible_bubbles.append(b)
                max_y_visible = b["y"] + b["h"]
            else:
                typing_lead_time = 1.5
                if b["start"] - typing_lead_time <= t < b["start"]:
                    current_speaker_typing = b["speaker"]
                break
                
        required_height = max_y_visible
        if required_height > (height - header_h - bottom_margin - 80):
            target_scroll = required_height - (height - header_h - bottom_margin - 80)
            
        current_scroll += (target_scroll - current_scroll) * 0.1
        
        frame = bg_img.copy()
        
        date_y = int(-current_scroll) + header_h + 10
        if date_y > header_h - 80 and date_y < height:
            frame.paste(date_badge, (0, date_y), mask=date_badge)
            
        for b in visible_bubbles:
            draw_y = int(b["y"] - current_scroll) + header_h + 90
            if draw_y + b["h"] > header_h and draw_y < height:
                frame.paste(b["img"], (0, draw_y), mask=b["img"])
                
        m = 42 + int(t / 60.0)
        m = min(m, 44)
        header_online_key = f'header_online_11_{m}'
        header_typing_key = f'header_typing_11_{m}'
        
        if header_online_key in ui_assets:
            if current_speaker_typing and current_speaker_typing != self_speaker:
                frame.paste(ui_assets[header_typing_key], (0, 0), mask=ui_assets[header_typing_key])
            else:
                frame.paste(ui_assets[header_online_key], (0, 0), mask=ui_assets[header_online_key])
                
            if other_avatar:
                try:
                    av = crop_circular_avatar(other_avatar, 90)
                    frame.paste(av, (76, 95), mask=av)
                except: pass
                
        if ui_assets['footer']:
            footer_y = height - ui_assets['footer'].height
            frame.paste(ui_assets['footer'], (0, footer_y), mask=ui_assets['footer'])
            
        process.stdin.write(frame.tobytes())
        
        if frame_idx % 60 == 0:
            print(f"[WhatsApp Renderer] Rendered {frame_idx}/{total_frames} frames ({(frame_idx/total_frames)*100:.1f}%)")
            
    process.stdin.close()
    process.wait()
    print("[WhatsApp Renderer] Dynamic video track complete.")
    return output_video_path
