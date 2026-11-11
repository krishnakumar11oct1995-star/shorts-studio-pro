import os
import math
import subprocess
import numpy as np
import scipy.io.wavfile as wavfile
from PIL import Image, ImageDraw
import cv2

def generate_lullaby(wav_path="output_lullaby.wav", duration=30.0):
    sample_rate = 44100
    notes = {
        'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
        'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'G5': 783.99, 'R': 0.0
    }

    melody = [
        ('C4', 1), ('C4', 1), ('G4', 1), ('G4', 1),
        ('A4', 1), ('A4', 1), ('G4', 2),
        ('F4', 1), ('F4', 1), ('E4', 1), ('E4', 1),
        ('D4', 1), ('D4', 1), ('C4', 2),
        ('G4', 1), ('G4', 1), ('F4', 1), ('F4', 1),
        ('E4', 1), ('E4', 1), ('D4', 2),
        ('G4', 1), ('G4', 1), ('F4', 1), ('F4', 1),
        ('E4', 1), ('E4', 1), ('D4', 2),
        ('C4', 1), ('C4', 1), ('G4', 1), ('G4', 1),
        ('A4', 1), ('A4', 1), ('G4', 2),
        ('F4', 1), ('F4', 1), ('E4', 1), ('E4', 1),
        ('D4', 1), ('D4', 1), ('C4', 2),
    ]

    beat_len = 0.72
    audio = np.zeros(int(sample_rate * (duration + 2.0)))

    def synth_bell(freq, note_dur):
        t = np.linspace(0, note_dur, int(sample_rate * note_dur), endpoint=False)
        if freq == 0:
            return np.zeros_like(t)
        env = np.exp(-t / 1.15)
        sig = (
            1.00 * np.sin(2 * np.pi * freq * t) +
            0.45 * np.sin(2 * np.pi * freq * 2.0 * t) * np.exp(-t / 0.7) +
            0.20 * np.sin(2 * np.pi * freq * 3.0 * t) * np.exp(-t / 0.4) +
            0.10 * np.sin(2 * np.pi * freq * 4.0 * t) * np.exp(-t / 0.25)
        ) * env
        att = int(sample_rate * 0.008)
        sig[:att] *= np.linspace(0, 1, att)
        return sig

    cur_t = 0.5
    for note, bts in melody:
        f = notes.get(note, 0.0)
        d = bts * beat_len
        if cur_t >= duration - 0.8:
            break
        bell = synth_bell(f, min(d * 1.8, 3.5))
        idx = int(cur_t * sample_rate)
        if idx + len(bell) <= len(audio):
            audio[idx:idx+len(bell)] += bell * 0.42
        if bts >= 1.0 and f > 0:
            bass = synth_bell(f / 2.0, 2.5)
            if idx + len(bass) <= len(audio):
                audio[idx:idx+len(bass)] += bass * 0.22
        cur_t += d

    audio = audio[:int(sample_rate * duration)]
    fin, fout = int(sample_rate * 1.0), int(sample_rate * 2.0)
    audio[:fin] *= np.linspace(0, 1, fin)
    audio[-fout:] *= np.linspace(1, 0, fout)
    audio = audio / (np.max(np.abs(audio)) + 1e-6) * 0.85

    stereo = np.column_stack([audio, audio])
    delay = int(sample_rate * 0.025)
    stereo[:, 1] = np.roll(stereo[:, 1], delay)
    stereo[:delay, 1] = 0

    wavfile.write(wav_path, sample_rate, (stereo * 32767).astype(np.int16))
    print(f"Generated lullaby: {wav_path}")
    return wav_path

def render_cards(size=720):
    scale = 2
    W, H = size * scale, size * scale

    def draw_rot_el(target, ecx, ecy, rx, ry, deg, col):
        p = Image.new("RGBA", (int(rx * 2 + 40), int(ry * 2 + 40)), (0, 0, 0, 0))
        pd = ImageDraw.Draw(p)
        pd.ellipse([20, 20, 20 + rx*2, 20 + ry*2], fill=col)
        rot = p.rotate(deg, resample=Image.Resampling.BICUBIC, expand=True)
        rcx, rcy = rot.width // 2, rot.height // 2
        target.alpha_composite(rot, (int(ecx - rcx), int(ecy - rcy)))

    # 1. Panda in Scalloped Cloud
    c1 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d1 = ImageDraw.Draw(c1)
    cx, cy = W // 2, H // 2
    r_c, r_l = 260 * scale, 85 * scale
    d1.ellipse([cx - r_c, cy - r_c, cx + r_c, cy + r_c], fill=(255, 255, 255, 255))
    for i in range(14):
        ang = 2 * math.pi * i / 14
        lx = cx + int((r_c - 15 * scale) * math.cos(ang))
        ly = cy + int((r_c - 15 * scale) * math.sin(ang))
        d1.ellipse([lx - r_l, ly - r_l, lx + r_l, ly + r_l], fill=(255, 255, 255, 255))
    body_cy = cy + 220 * scale
    d1.ellipse([cx - 240*scale, body_cy - 120*scale, cx + 240*scale, body_cy + 260*scale], fill=(0, 0, 0, 255))
    d1.ellipse([cx - 140*scale, body_cy - 60*scale, cx + 140*scale, body_cy + 220*scale], fill=(255, 255, 255, 255))
    h_cy = cy - 30 * scale
    h_rx, h_ry = 220 * scale, 190 * scale
    e_r = 75 * scale
    d1.ellipse([cx - 180*scale - e_r, h_cy - 150*scale - e_r, cx - 180*scale + e_r, h_cy - 150*scale + e_r], fill=(0, 0, 0, 255))
    d1.ellipse([cx + 180*scale - e_r, h_cy - 150*scale - e_r, cx + 180*scale + e_r, h_cy - 150*scale + e_r], fill=(0, 0, 0, 255))
    d1.ellipse([cx - h_rx, h_cy - h_ry, cx + h_rx, h_cy + h_ry], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=14*scale)
    draw_rot_el(c1, cx - 90*scale, h_cy - 10*scale, 55*scale, 75*scale, 25, (0, 0, 0, 255))
    draw_rot_el(c1, cx + 90*scale, h_cy - 10*scale, 55*scale, 75*scale, -25, (0, 0, 0, 255))
    d1 = ImageDraw.Draw(c1)
    d1.arc([cx - 110*scale, h_cy - 25*scale, cx - 70*scale, h_cy + 15*scale], 180, 360, fill=(255, 255, 255, 255), width=10*scale)
    d1.arc([cx + 70*scale, h_cy - 25*scale, cx + 110*scale, h_cy + 15*scale], 180, 360, fill=(255, 255, 255, 255), width=10*scale)
    d1.ellipse([cx - 30*scale, h_cy + 25*scale, cx + 30*scale, h_cy + 75*scale], fill=(0, 0, 0, 255))
    d1.arc([cx - 44*scale, h_cy + 45*scale, cx, h_cy + 95*scale], 0, 180, fill=(0, 0, 0, 255), width=10*scale)
    d1.arc([cx, h_cy + 45*scale, cx + 44*scale, h_cy + 95*scale], 0, 180, fill=(0, 0, 0, 255), width=10*scale)
    panda = c1.resize((size, size), Image.Resampling.LANCZOS)

    # 2. Lion in Sunburst Star
    c2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(c2)
    pts = []
    for i in range(32):
        ang = math.pi * i / 16
        r = 340 * scale if i % 2 == 0 else 260 * scale
        pts.append((cx + int(r * math.cos(ang)), cy + int(r * math.sin(ang))))
    d2.polygon(pts, fill=(255, 255, 255, 255))
    d2.ellipse([cx - 225*scale, cy - 225*scale, cx + 225*scale, cy + 225*scale], fill=(0, 0, 0, 255))
    d2.ellipse([cx - 175*scale, cy - 175*scale, cx + 175*scale, cy + 175*scale], fill=(255, 255, 255, 255))
    e_r = 50 * scale
    d2.ellipse([cx - 135*scale - e_r, cy - 135*scale - e_r, cx - 135*scale + e_r, cy - 135*scale + e_r], fill=(0, 0, 0, 255))
    d2.ellipse([cx + 135*scale - e_r, cy - 135*scale - e_r, cx + 135*scale + e_r, cy - 135*scale + e_r], fill=(0, 0, 0, 255))
    d2.ellipse([cx - 135*scale - 25*scale, cy - 135*scale - 25*scale, cx - 135*scale + 25*scale, cy - 135*scale + 25*scale], fill=(255, 255, 255, 255))
    d2.ellipse([cx + 135*scale - 25*scale, cy - 135*scale - 25*scale, cx + 135*scale + 25*scale, cy - 135*scale + 25*scale], fill=(255, 255, 255, 255))
    eye_r = 34 * scale
    d2.ellipse([cx - 75*scale - eye_r, cy - 30*scale - eye_r, cx - 75*scale + eye_r, cy - 30*scale + eye_r], fill=(0, 0, 0, 255))
    d2.ellipse([cx - 65*scale, cy - 44*scale, cx - 50*scale, cy - 29*scale], fill=(255, 255, 255, 255))
    d2.ellipse([cx - 90*scale, cy - 24*scale, cx - 80*scale, cy - 14*scale], fill=(255, 255, 255, 255))
    d2.ellipse([cx + 75*scale - eye_r, cy - 30*scale - eye_r, cx + 75*scale + eye_r, cy - 30*scale + eye_r], fill=(0, 0, 0, 255))
    d2.ellipse([cx + 85*scale, cy - 44*scale, cx + 100*scale, cy - 29*scale], fill=(255, 255, 255, 255))
    d2.ellipse([cx + 60*scale, cy - 24*scale, cx + 70*scale, cy - 14*scale], fill=(255, 255, 255, 255))
    d2.polygon([(cx - 28*scale, cy + 30*scale), (cx + 28*scale, cy + 30*scale), (cx, cy + 68*scale)], fill=(0, 0, 0, 255))
    d2.ellipse([cx - 30*scale, cy + 18*scale, cx + 2*scale, cy + 42*scale], fill=(0, 0, 0, 255))
    d2.ellipse([cx - 2*scale, cy + 18*scale, cx + 30*scale, cy + 42*scale], fill=(0, 0, 0, 255))
    d2.arc([cx - 38*scale, cy + 48*scale, cx, cy + 86*scale], 0, 180, fill=(0, 0, 0, 255), width=9*scale)
    d2.arc([cx, cy + 48*scale, cx + 38*scale, cy + 86*scale], 0, 180, fill=(0, 0, 0, 255), width=9*scale)
    for dy in [-15, 5, 25]:
        d2.line([(cx - 100*scale, cy + (50+dy)*scale), (cx - 160*scale, cy + (50+dy)*scale)], fill=(0, 0, 0, 255), width=6*scale)
        d2.line([(cx + 100*scale, cy + (50+dy)*scale), (cx + 160*scale, cy + (50+dy)*scale)], fill=(0, 0, 0, 255), width=6*scale)
    lion = c2.resize((size, size), Image.Resampling.LANCZOS)

    # 3. Bunny in Octagon Frame
    c3 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d3 = ImageDraw.Draw(c3)
    r, cut = 330 * scale, 100 * scale
    oct_pts = [
        (cx - r + cut, cy - r), (cx + r - cut, cy - r),
        (cx + r, cy - r + cut), (cx + r, cy + r - cut),
        (cx + r - cut, cy + r), (cx - r + cut, cy + r),
        (cx - r, cy + r - cut), (cx - r, cy - r + cut)
    ]
    d3.polygon(oct_pts, fill=(255, 255, 255, 255))
    d3.polygon(oct_pts, outline=(0, 0, 0, 255), width=12*scale)
    d3.ellipse([cx - 120*scale, cy - 300*scale, cx - 40*scale, cy - 75*scale], fill=(0, 0, 0, 255))
    d3.ellipse([cx - 105*scale, cy - 270*scale, cx - 55*scale, cy - 105*scale], fill=(255, 255, 255, 255))
    d3.ellipse([cx + 40*scale, cy - 300*scale, cx + 120*scale, cy - 75*scale], fill=(0, 0, 0, 255))
    d3.ellipse([cx + 55*scale, cy - 270*scale, cx + 105*scale, cy - 105*scale], fill=(255, 255, 255, 255))
    h_cy = cy + 20 * scale
    d3.ellipse([cx - 170*scale, h_cy - 130*scale, cx + 170*scale, h_cy + 140*scale], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=12*scale)
    eye_r = 30 * scale
    d3.ellipse([cx - 70*scale - eye_r, h_cy - 20*scale - eye_r, cx - 70*scale + eye_r, h_cy - 20*scale + eye_r], fill=(0, 0, 0, 255))
    d3.ellipse([cx - 60*scale, h_cy - 34*scale, cx - 46*scale, h_cy - 20*scale], fill=(255, 255, 255, 255))
    d3.ellipse([cx + 70*scale - eye_r, h_cy - 20*scale - eye_r, cx + 70*scale + eye_r, h_cy - 20*scale + eye_r], fill=(0, 0, 0, 255))
    d3.ellipse([cx + 80*scale, h_cy - 34*scale, cx + 94*scale, h_cy - 20*scale], fill=(255, 255, 255, 255))
    d3.polygon([(cx - 18*scale, h_cy + 24*scale), (cx + 18*scale, h_cy + 24*scale), (cx, h_cy + 42*scale)], fill=(0, 0, 0, 255))
    d3.arc([cx - 30*scale, h_cy + 34*scale, cx, h_cy + 65*scale], 0, 180, fill=(0, 0, 0, 255), width=9*scale)
    d3.arc([cx, h_cy + 34*scale, cx + 30*scale, h_cy + 65*scale], 0, 180, fill=(0, 0, 0, 255), width=9*scale)
    d3.line([(cx - 85*scale, h_cy + 35*scale), (cx - 145*scale, h_cy + 25*scale)], fill=(0, 0, 0, 255), width=6*scale)
    d3.line([(cx - 85*scale, h_cy + 45*scale), (cx - 145*scale, h_cy + 55*scale)], fill=(0, 0, 0, 255), width=6*scale)
    d3.line([(cx + 85*scale, h_cy + 35*scale), (cx + 145*scale, h_cy + 25*scale)], fill=(0, 0, 0, 255), width=6*scale)
    d3.line([(cx + 85*scale, h_cy + 45*scale), (cx + 145*scale, h_cy + 55*scale)], fill=(0, 0, 0, 255), width=6*scale)
    bunny = c3.resize((size, size), Image.Resampling.LANCZOS)

    # 4. Bear in Concentric Dotted Circle
    c4 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d4 = ImageDraw.Draw(c4)
    r_out = 330 * scale
    d4.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill=(255, 255, 255, 255))
    for i in range(24):
        ang = 2 * math.pi * i / 24
        dx = cx + int((r_out - 35*scale) * math.cos(ang))
        dy = cy + int((r_out - 35*scale) * math.sin(ang))
        d4.ellipse([dx - 13*scale, dy - 13*scale, dx + 13*scale, dy + 13*scale], fill=(0, 0, 0, 255))
    r_mid = 265 * scale
    d4.ellipse([cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid], outline=(0, 0, 0, 255), width=10*scale)
    e_r = 70 * scale
    d4.ellipse([cx - 150*scale - e_r, cy - 130*scale - e_r, cx - 150*scale + e_r, cy - 130*scale + e_r], fill=(0, 0, 0, 255))
    d4.ellipse([cx + 150*scale - e_r, cy - 130*scale - e_r, cx + 150*scale + e_r, cy - 130*scale + e_r], fill=(0, 0, 0, 255))
    d4.ellipse([cx - 150*scale - 32*scale, cy - 130*scale - 32*scale, cx - 150*scale + 32*scale, cy - 130*scale + 32*scale], fill=(255, 255, 255, 255))
    d4.ellipse([cx + 150*scale - 32*scale, cy - 130*scale - 32*scale, cx + 150*scale + 32*scale, cy - 130*scale + 32*scale], fill=(255, 255, 255, 255))
    h_r = 180 * scale
    d4.ellipse([cx - h_r, cy - 30*scale - h_r, cx + h_r, cy - 30*scale + h_r], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=11*scale)
    eye_r = 28 * scale
    d4.ellipse([cx - 70*scale - eye_r, cy - 48*scale - eye_r, cx - 70*scale + eye_r, cy - 48*scale + eye_r], fill=(0, 0, 0, 255))
    d4.ellipse([cx - 60*scale, cy - 60*scale, cx - 48*scale, cy - 48*scale], fill=(255, 255, 255, 255))
    d4.ellipse([cx + 70*scale - eye_r, cy - 48*scale - eye_r, cx + 70*scale + eye_r, cy - 48*scale + eye_r], fill=(0, 0, 0, 255))
    d4.ellipse([cx + 80*scale, cy - 60*scale, cx + 92*scale, cy - 48*scale], fill=(255, 255, 255, 255))
    d4.ellipse([cx - 80*scale, cy + 20*scale - 60*scale, cx + 80*scale, cy + 20*scale + 60*scale], fill=(0, 0, 0, 255))
    d4.ellipse([cx - 30*scale, cy + 5*scale - 18*scale, cx + 30*scale, cy + 5*scale + 18*scale], fill=(255, 255, 255, 255))
    d4.arc([cx - 28*scale, cy + 30*scale, cx, cy + 62*scale], 0, 180, fill=(255, 255, 255, 255), width=6*scale)
    d4.arc([cx, cy + 30*scale, cx + 28*scale, cy + 62*scale], 0, 180, fill=(255, 255, 255, 255), width=6*scale)
    bear = c4.resize((size, size), Image.Resampling.LANCZOS)

    return [panda, lion, bunny, bear]

def main():
    wav_path = "output_lullaby.wav"
    if not os.path.exists(wav_path):
        generate_lullaby(wav_path, duration=30.0)

    CARD_SIZE = 720
    cards = render_cards(CARD_SIZE)

    WIDTH = 1920
    HEIGHT = 1080
    FPS = 30
    DURATION = 30.0
    TOTAL_FRAMES = int(DURATION * FPS)
    TEMP_VIDEO = "temp_raw_video.mp4"
    OUT_MP4 = "high_contrast_baby_sensory_30s.mp4"

    for f in [TEMP_VIDEO, OUT_MP4]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    # OpenCV VideoWriter for ultra-fast, zero-pipe deadlock encoding
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(TEMP_VIDEO, fourcc, FPS, (WIDTH, HEIGHT))

    # Pre-render a seamless looping starry background (width = 3840)
    bg_w = WIDTH * 2
    bg_img = Image.new("RGB", (bg_w, HEIGHT), (0, 0, 0))
    d_bg = ImageDraw.Draw(bg_img)
    np.random.seed(42)
    for _ in range(80):
        sx = int(np.random.uniform(0, bg_w))
        sy = int(np.random.uniform(0, HEIGHT))
        sz = int(np.random.uniform(6, 14))
        shape = np.random.choice(["circle", "plus", "diamond"])
        if shape == "circle":
            d_bg.ellipse([sx-sz, sy-sz, sx+sz, sy+sz], fill=(255, 255, 255))
        elif shape == "plus":
            d_bg.line([(sx-sz*1.4, sy), (sx+sz*1.4, sy)], fill=(255, 255, 255), width=3)
            d_bg.line([(sx, sy-sz*1.4), (sx, sy+sz*1.4)], fill=(255, 255, 255), width=3)
        elif shape == "diamond":
            d_bg.polygon([(sx-sz*1.3, sy), (sx, sy-sz*1.3), (sx+sz*1.3, sy), (sx, sy+sz*1.3)], fill=(255, 255, 255))

    scroll_speed = 130.0
    card_spacing = 1050

    print(f"Rendering {TOTAL_FRAMES} frames ({FPS} FPS, 1080p)...")
    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / float(FPS)

        # Starfield subtle parallax scroll
        bg_offset = int((t * 25.0) % WIDTH)
        frame_img = bg_img.crop((bg_offset, 0, bg_offset + WIDTH, HEIGHT))

        # Position characters
        base_scroll = 960 - (t * scroll_speed)
        for k in range(-2, 7):
            char_idx = k % len(cards)
            char_center_x = base_scroll + (k * card_spacing)
            if char_center_x < -CARD_SIZE or char_center_x > WIDTH + CARD_SIZE:
                continue

            y_bob = math.sin(t * 1.5 + k * 1.4) * 20
            char_center_y = (HEIGHT // 2) + y_bob

            top_left_x = int(char_center_x - CARD_SIZE // 2)
            top_left_y = int(char_center_y - CARD_SIZE // 2)

            frame_img.paste(cards[char_idx], (top_left_x, top_left_y), cards[char_idx])

        # Write to OpenCV
        frame_bgr = cv2.cvtColor(np.array(frame_img), cv2.COLOR_RGB2BGR)
        writer.write(frame_bgr)

        if (frame_idx + 1) % 150 == 0 or frame_idx == TOTAL_FRAMES - 1:
            print(f"Frame {frame_idx + 1}/{TOTAL_FRAMES} ({(frame_idx+1)/TOTAL_FRAMES*100:.0f}%)")

    writer.release()
    print("Video track encoded! Merging audio with FFmpeg...")

    # Mux audio and re-encode to clean H.264
    cmd = [
        "ffmpeg", "-y",
        "-i", TEMP_VIDEO,
        "-i", wav_path,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUT_MP4
    ]
    subprocess.run(cmd, check=True)

    if os.path.exists(TEMP_VIDEO):
        os.remove(TEMP_VIDEO)

    print(f"SUCCESS: Generated {OUT_MP4} ({os.path.getsize(OUT_MP4)} bytes)")

if __name__ == "__main__":
    main()
