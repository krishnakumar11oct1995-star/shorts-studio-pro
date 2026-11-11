import os
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw
import cv2

scale = 2
CARD_SIZE = 700
W, H = CARD_SIZE * scale, CARD_SIZE * scale
cx, cy = W // 2, H // 2

def draw_rot_el(target, ecx, ecy, rx, ry, deg, col):
    p = Image.new("RGBA", (int(rx * 2 + 40), int(ry * 2 + 40)), (0, 0, 0, 0))
    pd = ImageDraw.Draw(p)
    pd.ellipse([20, 20, 20 + rx*2, 20 + ry*2], fill=col)
    rot = p.rotate(deg, resample=Image.Resampling.BICUBIC, expand=True)
    rcx, rcy = rot.width // 2, rot.height // 2
    target.alpha_composite(rot, (int(ecx - rcx), int(ecy - rcy)))

# --- 1. PANDA ---
def render_panda(blink=False):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    r_c, r_l = 260 * scale, 85 * scale
    d.ellipse([cx - r_c, cy - r_c, cx + r_c, cy + r_c], fill=(255, 255, 255, 255))
    for i in range(14):
        ang = 2 * math.pi * i / 14
        lx = cx + int((r_c - 15 * scale) * math.cos(ang))
        ly = cy + int((r_c - 15 * scale) * math.sin(ang))
        d.ellipse([lx - r_l, ly - r_l, lx + r_l, ly + r_l], fill=(255, 255, 255, 255))
    body_cy = cy + 220 * scale
    d.ellipse([cx - 240*scale, body_cy - 120*scale, cx + 240*scale, body_cy + 260*scale], fill=(0, 0, 0, 255))
    d.ellipse([cx - 140*scale, body_cy - 60*scale, cx + 140*scale, body_cy + 220*scale], fill=(255, 255, 255, 255))
    h_cy = cy - 30 * scale
    h_rx, h_ry = 220 * scale, 190 * scale
    e_r = 75 * scale
    d.ellipse([cx - 180*scale - e_r, h_cy - 150*scale - e_r, cx - 180*scale + e_r, h_cy - 150*scale + e_r], fill=(0, 0, 0, 255))
    d.ellipse([cx + 180*scale - e_r, h_cy - 150*scale - e_r, cx + 180*scale + e_r, h_cy - 150*scale + e_r], fill=(0, 0, 0, 255))
    d.ellipse([cx - h_rx, h_cy - h_ry, cx + h_rx, h_cy + h_ry], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=14*scale)
    draw_rot_el(c, cx - 90*scale, h_cy - 10*scale, 55*scale, 75*scale, 25, (0, 0, 0, 255))
    draw_rot_el(c, cx + 90*scale, h_cy - 10*scale, 55*scale, 75*scale, -25, (0, 0, 0, 255))
    d = ImageDraw.Draw(c)
    if blink:
        d.line([(cx - 110*scale, h_cy - 10*scale), (cx - 70*scale, h_cy - 10*scale)], fill=(255, 255, 255, 255), width=10*scale)
        d.line([(cx + 70*scale, h_cy - 10*scale), (cx + 110*scale, h_cy - 10*scale)], fill=(255, 255, 255, 255), width=10*scale)
    else:
        d.arc([cx - 110*scale, h_cy - 25*scale, cx - 70*scale, h_cy + 15*scale], 180, 360, fill=(255, 255, 255, 255), width=10*scale)
        d.arc([cx + 70*scale, h_cy - 25*scale, cx + 110*scale, h_cy + 15*scale], 180, 360, fill=(255, 255, 255, 255), width=10*scale)
    d.ellipse([cx - 30*scale, h_cy + 25*scale, cx + 30*scale, h_cy + 75*scale], fill=(0, 0, 0, 255))
    d.arc([cx - 44*scale, h_cy + 45*scale, cx, h_cy + 95*scale], 0, 180, fill=(0, 0, 0, 255), width=10*scale)
    d.arc([cx, h_cy + 45*scale, cx + 44*scale, h_cy + 95*scale], 0, 180, fill=(0, 0, 0, 255), width=10*scale)
    return c.resize((CARD_SIZE, CARD_SIZE), Image.Resampling.LANCZOS)

# --- 2. LION ---
def render_lion(blink=False):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    pts = []
    for i in range(32):
        ang = math.pi * i / 16
        r = 340 * scale if i % 2 == 0 else 260 * scale
        pts.append((cx + int(r * math.cos(ang)), cy + int(r * math.sin(ang))))
    d.polygon(pts, fill=(255, 255, 255, 255))
    d.ellipse([cx - 225*scale, cy - 225*scale, cx + 225*scale, cy + 225*scale], fill=(0, 0, 0, 255))
    d.ellipse([cx - 175*scale, cy - 175*scale, cx + 175*scale, cy + 175*scale], fill=(255, 255, 255, 255))
    e_r = 50 * scale
    d.ellipse([cx - 135*scale - e_r, cy - 135*scale - e_r, cx - 135*scale + e_r, cy - 135*scale + e_r], fill=(0, 0, 0, 255))
    d.ellipse([cx + 135*scale - e_r, cy - 135*scale - e_r, cx + 135*scale + e_r, cy - 135*scale + e_r], fill=(0, 0, 0, 255))
    d.ellipse([cx - 135*scale - 25*scale, cy - 135*scale - 25*scale, cx - 135*scale + 25*scale, cy - 135*scale + 25*scale], fill=(255, 255, 255, 255))
    d.ellipse([cx + 135*scale - 25*scale, cy - 135*scale - 25*scale, cx + 135*scale + 25*scale, cy - 135*scale + 25*scale], fill=(255, 255, 255, 255))
    if blink:
        d.arc([cx - 100*scale, cy - 40*scale, cx - 50*scale, cy], 180, 360, fill=(0, 0, 0, 255), width=9*scale)
        d.arc([cx + 50*scale, cy - 40*scale, cx + 100*scale, cy], 180, 360, fill=(0, 0, 0, 255), width=9*scale)
    else:
        eye_r = 34 * scale
        d.ellipse([cx - 75*scale - eye_r, cy - 30*scale - eye_r, cx - 75*scale + eye_r, cy - 30*scale + eye_r], fill=(0, 0, 0, 255))
        d.ellipse([cx - 65*scale, cy - 44*scale, cx - 50*scale, cy - 29*scale], fill=(255, 255, 255, 255))
        d.ellipse([cx - 90*scale, cy - 24*scale, cx - 80*scale, cy - 14*scale], fill=(255, 255, 255, 255))
        d.ellipse([cx + 75*scale - eye_r, cy - 30*scale - eye_r, cx + 75*scale + eye_r, cy - 30*scale + eye_r], fill=(0, 0, 0, 255))
        d.ellipse([cx + 85*scale, cy - 44*scale, cx + 100*scale, cy - 29*scale], fill=(255, 255, 255, 255))
        d.ellipse([cx + 60*scale, cy - 24*scale, cx + 70*scale, cy - 14*scale], fill=(255, 255, 255, 255))
    d.polygon([(cx - 28*scale, cy + 30*scale), (cx + 28*scale, cy + 30*scale), (cx, cy + 68*scale)], fill=(0, 0, 0, 255))
    d.ellipse([cx - 30*scale, cy + 18*scale, cx + 2*scale, cy + 42*scale], fill=(0, 0, 0, 255))
    d.ellipse([cx - 2*scale, cy + 18*scale, cx + 30*scale, cy + 42*scale], fill=(0, 0, 0, 255))
    d.arc([cx - 38*scale, cy + 48*scale, cx, cy + 86*scale], 0, 180, fill=(0, 0, 0, 255), width=9*scale)
    d.arc([cx, cy + 48*scale, cx + 38*scale, cy + 86*scale], 0, 180, fill=(0, 0, 0, 255), width=9*scale)
    for dy in [-15, 5, 25]:
        d.line([(cx - 100*scale, cy + (50+dy)*scale), (cx - 160*scale, cy + (50+dy)*scale)], fill=(0, 0, 0, 255), width=6*scale)
        d.line([(cx + 100*scale, cy + (50+dy)*scale), (cx + 160*scale, cy + (50+dy)*scale)], fill=(0, 0, 0, 255), width=6*scale)
    return c.resize((CARD_SIZE, CARD_SIZE), Image.Resampling.LANCZOS)

# --- 3. BUNNY ---
def render_bunny(blink=False):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    r, cut = 330 * scale, 100 * scale
    oct_pts = [
        (cx - r + cut, cy - r), (cx + r - cut, cy - r),
        (cx + r, cy - r + cut), (cx + r, cy + r - cut),
        (cx + r - cut, cy + r), (cx - r + cut, cy + r),
        (cx - r, cy + r - cut), (cx - r, cy - r + cut)
    ]
    d.polygon(oct_pts, fill=(255, 255, 255, 255))
    d.polygon(oct_pts, outline=(0, 0, 0, 255), width=12*scale)
    d.ellipse([cx - 120*scale, cy - 300*scale, cx - 40*scale, cy - 75*scale], fill=(0, 0, 0, 255))
    d.ellipse([cx - 105*scale, cy - 270*scale, cx - 55*scale, cy - 105*scale], fill=(255, 255, 255, 255))
    d.ellipse([cx + 40*scale, cy - 300*scale, cx + 120*scale, cy - 75*scale], fill=(0, 0, 0, 255))
    d.ellipse([cx + 55*scale, cy - 270*scale, cx + 105*scale, cy - 105*scale], fill=(255, 255, 255, 255))
    h_cy = cy + 20 * scale
    d.ellipse([cx - 170*scale, h_cy - 130*scale, cx + 170*scale, h_cy + 140*scale], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=12*scale)
    if blink:
        d.arc([cx - 95*scale, h_cy - 30*scale, cx - 45*scale, h_cy + 10*scale], 180, 360, fill=(0, 0, 0, 255), width=8*scale)
        d.arc([cx + 45*scale, h_cy - 30*scale, cx + 95*scale, h_cy + 10*scale], 180, 360, fill=(0, 0, 0, 255), width=8*scale)
    else:
        eye_r = 30 * scale
        d.ellipse([cx - 70*scale - eye_r, h_cy - 20*scale - eye_r, cx - 70*scale + eye_r, h_cy - 20*scale + eye_r], fill=(0, 0, 0, 255))
        d.ellipse([cx - 60*scale, h_cy - 34*scale, cx - 46*scale, h_cy - 20*scale], fill=(255, 255, 255, 255))
        d.ellipse([cx + 70*scale - eye_r, h_cy - 20*scale - eye_r, cx + 70*scale + eye_r, h_cy - 20*scale + eye_r], fill=(0, 0, 0, 255))
        d.ellipse([cx + 80*scale, h_cy - 34*scale, cx + 94*scale, h_cy - 20*scale], fill=(255, 255, 255, 255))
    d.polygon([(cx - 18*scale, h_cy + 24*scale), (cx + 18*scale, h_cy + 24*scale), (cx, h_cy + 42*scale)], fill=(0, 0, 0, 255))
    d.arc([cx - 30*scale, h_cy + 34*scale, cx, h_cy + 65*scale], 0, 180, fill=(0, 0, 0, 255), width=9*scale)
    d.arc([cx, h_cy + 34*scale, cx + 30*scale, h_cy + 65*scale], 0, 180, fill=(0, 0, 0, 255), width=9*scale)
    d.line([(cx - 85*scale, h_cy + 35*scale), (cx - 145*scale, h_cy + 25*scale)], fill=(0, 0, 0, 255), width=6*scale)
    d.line([(cx - 85*scale, h_cy + 45*scale), (cx - 145*scale, h_cy + 55*scale)], fill=(0, 0, 0, 255), width=6*scale)
    d.line([(cx + 85*scale, h_cy + 35*scale), (cx + 145*scale, h_cy + 25*scale)], fill=(0, 0, 0, 255), width=6*scale)
    d.line([(cx + 85*scale, h_cy + 45*scale), (cx + 145*scale, h_cy + 55*scale)], fill=(0, 0, 0, 255), width=6*scale)
    return c.resize((CARD_SIZE, CARD_SIZE), Image.Resampling.LANCZOS)

# --- 4. BEAR ---
def render_bear(blink=False):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    r_out = 330 * scale
    d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill=(255, 255, 255, 255))
    for i in range(24):
        ang = 2 * math.pi * i / 24
        dx = cx + int((r_out - 35*scale) * math.cos(ang))
        dy = cy + int((r_out - 35*scale) * math.sin(ang))
        d.ellipse([dx - 13*scale, dy - 13*scale, dx + 13*scale, dy + 13*scale], fill=(0, 0, 0, 255))
    r_mid = 265 * scale
    d.ellipse([cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid], outline=(0, 0, 0, 255), width=10*scale)
    e_r = 70 * scale
    d.ellipse([cx - 150*scale - e_r, cy - 130*scale - e_r, cx - 150*scale + e_r, cy - 130*scale + e_r], fill=(0, 0, 0, 255))
    d.ellipse([cx + 150*scale - e_r, cy - 130*scale - e_r, cx + 150*scale + e_r, cy - 130*scale + e_r], fill=(0, 0, 0, 255))
    d.ellipse([cx - 150*scale - 32*scale, cy - 130*scale - 32*scale, cx - 150*scale + 32*scale, cy - 130*scale + 32*scale], fill=(255, 255, 255, 255))
    d.ellipse([cx + 150*scale - 32*scale, cy - 130*scale - 32*scale, cx + 150*scale + 32*scale, cy - 130*scale + 32*scale], fill=(255, 255, 255, 255))
    h_r = 180 * scale
    d.ellipse([cx - h_r, cy - 30*scale - h_r, cx + h_r, cy - 30*scale + h_r], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=11*scale)
    if blink:
        d.arc([cx - 95*scale, cy - 60*scale, cx - 45*scale, cy - 20*scale], 180, 360, fill=(0, 0, 0, 255), width=8*scale)
        d.arc([cx + 45*scale, cy - 60*scale, cx + 95*scale, cy - 20*scale], 180, 360, fill=(0, 0, 0, 255), width=8*scale)
    else:
        eye_r = 28 * scale
        d.ellipse([cx - 70*scale - eye_r, cy - 48*scale - eye_r, cx - 70*scale + eye_r, cy - 48*scale + eye_r], fill=(0, 0, 0, 255))
        d.ellipse([cx - 60*scale, cy - 60*scale, cx - 48*scale, cy - 48*scale], fill=(255, 255, 255, 255))
        d.ellipse([cx + 70*scale - eye_r, cy - 48*scale - eye_r, cx + 70*scale + eye_r, cy - 48*scale + eye_r], fill=(0, 0, 0, 255))
        d.ellipse([cx + 80*scale, cy - 60*scale, cx + 92*scale, cy - 48*scale], fill=(255, 255, 255, 255))
    d.ellipse([cx - 80*scale, cy + 20*scale - 60*scale, cx + 80*scale, cy + 20*scale + 60*scale], fill=(0, 0, 0, 255))
    d.ellipse([cx - 30*scale, cy + 5*scale - 18*scale, cx + 30*scale, cy + 5*scale + 18*scale], fill=(255, 255, 255, 255))
    d.arc([cx - 28*scale, cy + 30*scale, cx, cy + 62*scale], 0, 180, fill=(255, 255, 255, 255), width=6*scale)
    d.arc([cx, cy + 30*scale, cx + 28*scale, cy + 62*scale], 0, 180, fill=(255, 255, 255, 255), width=6*scale)
    return c.resize((CARD_SIZE, CARD_SIZE), Image.Resampling.LANCZOS)

# --- 5. ELEPHANT ---
def render_elephant(blink=False):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    pts = []
    for deg in range(0, 360, 5):
        t = math.radians(deg)
        hx = 16 * (math.sin(t)**3)
        hy = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        pts.append((cx + int(hx * 18 * scale), cy - 30 * scale + int(hy * 18 * scale)))
    d.polygon(pts, fill=(255, 255, 255, 255))
    d.polygon(pts, outline=(0, 0, 0, 255), width=12*scale)
    ear_w, ear_h = 110 * scale, 140 * scale
    d.ellipse([cx - 240*scale, cy - 100*scale, cx - 240*scale + ear_w*2, cy - 100*scale + ear_h*2], fill=(0, 0, 0, 255))
    d.ellipse([cx - 220*scale, cy - 80*scale, cx - 220*scale + (ear_w-20)*2, cy - 80*scale + (ear_h-20)*2], fill=(255, 255, 255, 255))
    d.ellipse([cx + 240*scale - ear_w*2, cy - 100*scale, cx + 240*scale, cy - 100*scale + ear_h*2], fill=(0, 0, 0, 255))
    d.ellipse([cx + 220*scale - (ear_w-20)*2, cy - 80*scale, cx + 220*scale, cy - 80*scale + (ear_h-20)*2], fill=(255, 255, 255, 255))
    d.ellipse([cx - 150*scale, cy - 120*scale, cx + 150*scale, cy + 130*scale], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=12*scale)
    if blink:
        d.arc([cx - 95*scale, cy - 40*scale, cx - 45*scale, cy], 180, 360, fill=(0, 0, 0, 255), width=8*scale)
        d.arc([cx + 45*scale, cy - 40*scale, cx + 95*scale, cy], 180, 360, fill=(0, 0, 0, 255), width=8*scale)
    else:
        d.ellipse([cx - 95*scale, cy - 45*scale, cx - 45*scale, cy + 5*scale], fill=(0, 0, 0, 255))
        d.ellipse([cx - 85*scale, cy - 38*scale, cx - 65*scale, cy - 18*scale], fill=(255, 255, 255, 255))
        d.ellipse([cx + 45*scale, cy - 45*scale, cx + 95*scale, cy + 5*scale], fill=(0, 0, 0, 255))
        d.ellipse([cx + 55*scale, cy - 38*scale, cx + 75*scale, cy - 18*scale], fill=(255, 255, 255, 255))
    d.arc([cx - 40*scale, cy + 10*scale, cx + 40*scale, cy + 120*scale], 0, 180, fill=(0, 0, 0, 255), width=24*scale)
    d.arc([cx + 10*scale, cy + 50*scale, cx + 55*scale, cy + 95*scale], 180, 360, fill=(0, 0, 0, 255), width=16*scale)
    d.ellipse([cx - 130*scale, cy - 5*scale, cx - 105*scale, cy + 20*scale], fill=(0, 0, 0, 255))
    d.ellipse([cx + 105*scale, cy - 5*scale, cx + 130*scale, cy + 20*scale], fill=(0, 0, 0, 255))
    return c.resize((CARD_SIZE, CARD_SIZE), Image.Resampling.LANCZOS)

# --- 6. OWL ---
def render_owl(blink=False):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    r_out = 320 * scale
    d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill=(255, 255, 255, 255))
    d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], outline=(0, 0, 0, 255), width=12*scale)
    d.polygon([(cx - 140*scale, cy - 170*scale), (cx - 80*scale, cy - 240*scale), (cx - 50*scale, cy - 160*scale)], fill=(0, 0, 0, 255))
    d.polygon([(cx + 140*scale, cy - 170*scale), (cx + 80*scale, cy - 240*scale), (cx + 50*scale, cy - 160*scale)], fill=(0, 0, 0, 255))
    d.ellipse([cx - 170*scale, cy - 160*scale, cx + 170*scale, cy + 190*scale], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=12*scale)
    for row in range(3):
        y_r = cy + 40*scale + row * 40*scale
        for col in [-60, 0, 60]:
            d.arc([cx + (col-25)*scale, y_r, cx + (col+25)*scale, y_r + 35*scale], 0, 180, fill=(0, 0, 0, 255), width=7*scale)
    eye_r = 75 * scale
    d.ellipse([cx - 80*scale - eye_r, cy - 40*scale - eye_r, cx - 80*scale + eye_r, cy - 40*scale + eye_r], fill=(0, 0, 0, 255))
    d.ellipse([cx - 80*scale - (eye_r-12*scale), cy - 40*scale - (eye_r-12*scale), cx - 80*scale + (eye_r-12*scale), cy - 40*scale + (eye_r-12*scale)], fill=(255, 255, 255, 255))
    d.ellipse([cx + 80*scale - eye_r, cy - 40*scale - eye_r, cx + 80*scale + eye_r, cy - 40*scale + eye_r], fill=(0, 0, 0, 255))
    d.ellipse([cx + 80*scale - (eye_r-12*scale), cy - 40*scale - (eye_r-12*scale), cx + 80*scale + (eye_r-12*scale), cy - 40*scale + (eye_r-12*scale)], fill=(255, 255, 255, 255))
    if blink:
        d.arc([cx - 120*scale, cy - 45*scale, cx - 40*scale, cy - 15*scale], 0, 180, fill=(0, 0, 0, 255), width=12*scale)
        d.arc([cx + 40*scale, cy - 45*scale, cx + 120*scale, cy - 15*scale], 0, 180, fill=(0, 0, 0, 255), width=12*scale)
    else:
        p_r = 40 * scale
        d.ellipse([cx - 80*scale - p_r, cy - 40*scale - p_r, cx - 80*scale + p_r, cy - 40*scale + p_r], fill=(0, 0, 0, 255))
        d.ellipse([cx - 70*scale, cy - 55*scale, cx - 50*scale, cy - 35*scale], fill=(255, 255, 255, 255))
        d.ellipse([cx + 80*scale - p_r, cy - 40*scale - p_r, cx + 80*scale + p_r, cy - 40*scale + p_r], fill=(0, 0, 0, 255))
        d.ellipse([cx + 90*scale, cy - 55*scale, cx + 110*scale, cy - 35*scale], fill=(255, 255, 255, 255))
    d.polygon([(cx - 20*scale, cy - 15*scale), (cx + 20*scale, cy - 15*scale), (cx, cy + 25*scale)], fill=(0, 0, 0, 255))
    return c.resize((CARD_SIZE, CARD_SIZE), Image.Resampling.LANCZOS)

# --- 7. CAT ---
def render_cat(blink=False):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    r = 340 * scale
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=(255, 255, 255, 255))
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], outline=(0, 0, 0, 255), width=12*scale)
    d.polygon([(cx - 150*scale, cy - 100*scale), (cx - 110*scale, cy - 240*scale), (cx - 40*scale, cy - 120*scale)], fill=(0, 0, 0, 255))
    d.polygon([(cx - 135*scale, cy - 105*scale), (cx - 110*scale, cy - 210*scale), (cx - 60*scale, cy - 120*scale)], fill=(255, 255, 255, 255))
    d.polygon([(cx + 150*scale, cy - 100*scale), (cx + 110*scale, cy - 240*scale), (cx + 40*scale, cy - 120*scale)], fill=(0, 0, 0, 255))
    d.polygon([(cx + 135*scale, cy - 105*scale), (cx + 110*scale, cy - 210*scale), (cx + 60*scale, cy - 120*scale)], fill=(255, 255, 255, 255))
    d.ellipse([cx - 170*scale, cy - 120*scale, cx + 170*scale, cy + 130*scale], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=12*scale)
    if blink:
        d.arc([cx - 105*scale, cy - 40*scale, cx - 45*scale, cy], 180, 360, fill=(0, 0, 0, 255), width=9*scale)
        d.arc([cx + 45*scale, cy - 40*scale, cx + 105*scale, cy], 180, 360, fill=(0, 0, 0, 255), width=9*scale)
    else:
        d.ellipse([cx - 105*scale, cy - 45*scale, cx - 45*scale, cy + 15*scale], fill=(0, 0, 0, 255))
        d.ellipse([cx - 95*scale, cy - 35*scale, cx - 75*scale, cy - 15*scale], fill=(255, 255, 255, 255))
        d.ellipse([cx + 45*scale, cy - 45*scale, cx + 105*scale, cy + 15*scale], fill=(0, 0, 0, 255))
        d.ellipse([cx + 75*scale, cy - 35*scale, cx + 95*scale, cy - 15*scale], fill=(255, 255, 255, 255))
    d.polygon([(cx - 16*scale, cy + 25*scale), (cx + 16*scale, cy + 25*scale), (cx, cy + 42*scale)], fill=(0, 0, 0, 255))
    d.arc([cx - 30*scale, cy + 35*scale, cx, cy + 65*scale], 0, 180, fill=(0, 0, 0, 255), width=8*scale)
    d.arc([cx, cy + 35*scale, cx + 30*scale, cy + 65*scale], 0, 180, fill=(0, 0, 0, 255), width=8*scale)
    for dy in [-15, 5, 25]:
        d.line([(cx - 85*scale, cy + (35+dy)*scale), (cx - 150*scale, cy + (35+dy)*scale)], fill=(0, 0, 0, 255), width=6*scale)
        d.line([(cx + 85*scale, cy + (35+dy)*scale), (cx + 150*scale, cy + (35+dy)*scale)], fill=(0, 0, 0, 255), width=6*scale)
    return c.resize((CARD_SIZE, CARD_SIZE), Image.Resampling.LANCZOS)

# --- 8. PENGUIN ---
def render_penguin(blink=False):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    rx_out, ry_out = 280 * scale, 340 * scale
    d.ellipse([cx - rx_out, cy - ry_out, cx + rx_out, cy + ry_out], fill=(255, 255, 255, 255))
    d.ellipse([cx - rx_out, cy - ry_out, cx + rx_out, cy + ry_out], outline=(0, 0, 0, 255), width=12*scale)
    d.ellipse([cx - 180*scale, cy - 220*scale, cx + 180*scale, cy + 240*scale], fill=(0, 0, 0, 255))
    d.ellipse([cx - 130*scale, cy - 140*scale, cx + 130*scale, cy + 220*scale], fill=(255, 255, 255, 255))
    d.ellipse([cx - 240*scale, cy - 60*scale, cx - 130*scale, cy + 140*scale], fill=(0, 0, 0, 255))
    d.ellipse([cx + 130*scale, cy - 60*scale, cx + 240*scale, cy + 140*scale], fill=(0, 0, 0, 255))
    if blink:
        d.arc([cx - 80*scale, cy - 70*scale, cx - 30*scale, cy - 30*scale], 180, 360, fill=(0, 0, 0, 255), width=8*scale)
        d.arc([cx + 30*scale, cy - 70*scale, cx + 80*scale, cy - 30*scale], 180, 360, fill=(0, 0, 0, 255), width=8*scale)
    else:
        d.ellipse([cx - 80*scale, cy - 80*scale, cx - 30*scale, cy - 25*scale], fill=(0, 0, 0, 255))
        d.ellipse([cx - 70*scale, cy - 72*scale, cx - 50*scale, cy - 52*scale], fill=(255, 255, 255, 255))
        d.ellipse([cx + 30*scale, cy - 80*scale, cx + 80*scale, cy - 25*scale], fill=(0, 0, 0, 255))
        d.ellipse([cx + 50*scale, cy - 72*scale, cx + 70*scale, cy - 52*scale], fill=(255, 255, 255, 255))
    d.polygon([(cx - 25*scale, cy - 30*scale), (cx + 25*scale, cy - 30*scale), (cx, cy + 15*scale)], fill=(0, 0, 0, 255))
    d.ellipse([cx - 90*scale, cy + 210*scale, cx - 20*scale, cy + 260*scale], fill=(0, 0, 0, 255))
    d.ellipse([cx + 20*scale, cy + 210*scale, cx + 90*scale, cy + 260*scale], fill=(0, 0, 0, 255))
    return c.resize((CARD_SIZE, CARD_SIZE), Image.Resampling.LANCZOS)

def generate_master_cycle():
    print("Pre-rendering all 8 animal characters (normal + blinking)...")
    anim_funcs = [render_panda, render_lion, render_bunny, render_bear, render_elephant, render_owl, render_cat, render_penguin]
    names = ["Panda", "Lion", "Bunny", "Bear", "Elephant", "Owl", "Cat", "Penguin"]
    
    animals = []
    for f, name in zip(anim_funcs, names):
        animals.append({
            "name": name,
            "open": f(blink=False),
            "blink": f(blink=True)
        })

    WIDTH = 1920
    HEIGHT = 1080
    FPS = 30
    CYCLE_DUR = 270.0 # 4.5 minutes
    TOTAL_FRAMES = int(CYCLE_DUR * FPS)
    TEMP_VIDEO = "temp_master_cycle.mp4"
    MASTER_MP4 = "master_cycle_270s.mp4"
    AUDIO_WAV = "master_cycle_lullaby.wav"

    for f in [TEMP_VIDEO, MASTER_MP4]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(TEMP_VIDEO, fourcc, FPS, (WIDTH, HEIGHT))

    # Seamless background
    bg_w = WIDTH * 2
    bg_img = Image.new("RGB", (bg_w, HEIGHT), (0, 0, 0))
    d_bg = ImageDraw.Draw(bg_img)
    np.random.seed(101)
    for _ in range(90):
        sx = int(np.random.uniform(0, bg_w))
        sy = int(np.random.uniform(0, HEIGHT))
        sz = int(np.random.uniform(5, 13))
        shape = np.random.choice(["circle", "plus", "diamond"])
        if shape == "circle":
            d_bg.ellipse([sx-sz, sy-sz, sx+sz, sy+sz], fill=(255, 255, 255))
        elif shape == "plus":
            d_bg.line([(sx-sz*1.4, sy), (sx+sz*1.4, sy)], fill=(255, 255, 255), width=3)
            d_bg.line([(sx, sy-sz*1.4), (sx, sy+sz*1.4)], fill=(255, 255, 255), width=3)
        elif shape == "diamond":
            d_bg.polygon([(sx-sz*1.3, sy), (sx, sy-sz*1.3), (sx+sz*1.3, sy), (sx, sy+sz*1.3)], fill=(255, 255, 255))

    print(f"Rendering 4.5-min master cycle ({TOTAL_FRAMES} frames)...")

    def paste_centered(frame, card, x, y, scale_factor=1.0, rot_deg=0.0):
        cur_card = card
        if abs(scale_factor - 1.0) > 0.02:
            nw = int(CARD_SIZE * scale_factor)
            nh = int(CARD_SIZE * scale_factor)
            cur_card = cur_card.resize((nw, nh), Image.Resampling.BILINEAR)
        if abs(rot_deg) > 0.5:
            cur_card = cur_card.rotate(rot_deg, resample=Image.Resampling.BICUBIC, expand=True)
        tx = int(x - cur_card.width // 2)
        ty = int(y - cur_card.height // 2)
        frame.paste(cur_card, (tx, ty), cur_card)

    def draw_ripples(draw, cx, cy, t, num_rings=3):
        for r_idx in range(num_rings):
            phase = (t * 0.4 + r_idx / float(num_rings)) % 1.0
            r = int(250 + phase * 400)
            alpha_width = int(6 * (1.0 - phase) + 2)
            if alpha_width > 0:
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255), width=alpha_width)

    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / float(FPS)
        scene_time = t % 45.0
        scene_idx = int(t / 45.0)

        # Starfield parallax
        bg_offset = int((t * 22.0) % WIDTH)
        frame_img = bg_img.crop((bg_offset, 0, bg_offset + WIDTH, HEIGHT))
        draw = ImageDraw.Draw(frame_img)

        # Blink state: blinks for 0.35s every 3.5s
        is_blink = (t % 3.5) < 0.35

        # --- SCENE 1 (0-45s): Calm Horizontal Tracking (Animals 0..3: Panda, Lion, Bunny, Bear) ---
        if scene_idx == 0:
            scroll_speed = 120.0
            card_spacing = 1050
            base_scroll = 960 - (scene_time * scroll_speed)
            for k in range(-2, 6):
                c_idx = k % 4
                char_x = base_scroll + k * card_spacing
                if char_x < -CARD_SIZE or char_x > WIDTH + CARD_SIZE:
                    continue
                y_bob = math.sin(t * 1.5 + k * 1.4) * 20
                char_y = (HEIGHT // 2) + y_bob
                c_data = animals[c_idx]
                card = c_data["blink"] if is_blink else c_data["open"]
                paste_centered(frame_img, card, char_x, char_y)

        # --- SCENE 2 (45-90s): Center Focus & Calm Breathing Sway (Elephant then Owl) ---
        elif scene_idx == 1:
            draw_ripples(draw, WIDTH // 2, HEIGHT // 2, scene_time)
            c_data = animals[4] if scene_time < 22.5 else animals[5] # Elephant or Owl
            card = c_data["blink"] if is_blink else c_data["open"]
            breath = 1.0 + 0.08 * math.sin(scene_time * 1.3)
            sway = math.sin(scene_time * 1.1) * 4.5
            paste_centered(frame_img, card, WIDTH // 2, HEIGHT // 2, breath, sway)

        # --- SCENE 3 (90-135s): Dual Floating Dance (Cat on left, Penguin on right) ---
        elif scene_idx == 2:
            # Cat
            y_cat = (HEIGHT // 2) + math.sin(scene_time * 1.4) * 75
            sway_cat = math.sin(scene_time * 1.2) * 5.0
            c_cat = animals[6]["blink"] if is_blink else animals[6]["open"]
            paste_centered(frame_img, c_cat, 550, y_cat, 0.98, sway_cat)
            # Penguin
            y_pen = (HEIGHT // 2) - math.sin(scene_time * 1.4) * 75
            sway_pen = -math.sin(scene_time * 1.2) * 5.0
            c_pen = animals[7]["blink"] if is_blink else animals[7]["open"]
            paste_centered(frame_img, c_pen, 1370, y_pen, 0.98, sway_pen)

        # --- SCENE 4 (135-180s): Horizontal Tracking 2 (Elephant, Owl, Cat, Penguin) ---
        elif scene_idx == 3:
            scroll_speed = 120.0
            card_spacing = 1050
            base_scroll = 960 - (scene_time * scroll_speed)
            for k in range(-2, 6):
                c_idx = 4 + (k % 4)
                char_x = base_scroll + k * card_spacing
                if char_x < -CARD_SIZE or char_x > WIDTH + CARD_SIZE:
                    continue
                y_bob = math.sin(t * 1.5 + k * 1.4) * 20
                char_y = (HEIGHT // 2) + y_bob
                c_data = animals[c_idx]
                card = c_data["blink"] if is_blink else c_data["open"]
                paste_centered(frame_img, card, char_x, char_y)

        # --- SCENE 5 (180-225s): Center Focus (Panda then Lion) ---
        elif scene_idx == 4:
            draw_ripples(draw, WIDTH // 2, HEIGHT // 2, scene_time)
            c_data = animals[0] if scene_time < 22.5 else animals[1] # Panda or Lion
            card = c_data["blink"] if is_blink else c_data["open"]
            breath = 1.0 + 0.08 * math.sin(scene_time * 1.3)
            sway = math.sin(scene_time * 1.1) * 4.5
            paste_centered(frame_img, card, WIDTH // 2, HEIGHT // 2, breath, sway)

        # --- SCENE 6 (225-270s): Dual Peek-a-boo (Bunny & Bear) ---
        else:
            y_b = (HEIGHT // 2) + math.sin(scene_time * 1.4) * 70
            sway_b = math.sin(scene_time * 1.1) * 4.5
            c_b = animals[2]["blink"] if is_blink else animals[2]["open"]
            paste_centered(frame_img, c_b, 550, y_b, 0.98, sway_b)

            y_be = (HEIGHT // 2) - math.sin(scene_time * 1.4) * 70
            sway_be = -math.sin(scene_time * 1.1) * 4.5
            c_be = animals[3]["blink"] if is_blink else animals[3]["open"]
            paste_centered(frame_img, c_be, 1370, y_be, 0.98, sway_be)

        frame_bgr = cv2.cvtColor(np.array(frame_img), cv2.COLOR_RGB2BGR)
        writer.write(frame_bgr)

        if (frame_idx + 1) % 450 == 0 or frame_idx == TOTAL_FRAMES - 1:
            print(f"Master progress: {frame_idx + 1}/{TOTAL_FRAMES} ({(frame_idx+1)/TOTAL_FRAMES*100:.0f}%)")

    writer.release()
    print("Master raw video encoded. Muxing audio...")

    cmd_mux = [
        "ffmpeg", "-y",
        "-i", TEMP_VIDEO,
        "-i", AUDIO_WAV,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        MASTER_MP4
    ]
    subprocess.run(cmd_mux, check=True)
    if os.path.exists(TEMP_VIDEO):
        os.remove(TEMP_VIDEO)
    print(f"Master cycle ready: {MASTER_MP4} ({os.path.getsize(MASTER_MP4)} bytes)")

    # === STEP 2: LOOP INTO FULL 1-HOUR (3600 SECONDS) VIDEO ===
    FINAL_1HR_MP4 = "high_contrast_baby_sensory_1hour.mp4"
    if os.path.exists(FINAL_1HR_MP4):
        try:
            os.remove(FINAL_1HR_MP4)
        except Exception:
            pass

    print(f"Expanding master cycle into 1-Hour video: {FINAL_1HR_MP4}...")
    # 270s * 14 loops = 3780s, trimmed to exact 3600s (1 hour 00 mins 00 secs)
    cmd_1hr = [
        "ffmpeg", "-y",
        "-stream_loop", "13",
        "-i", MASTER_MP4,
        "-t", "3600",
        "-c", "copy",
        FINAL_1HR_MP4
    ]
    subprocess.run(cmd_1hr, check=True)
    print(f"ALL DONE! Generated full 1-Hour video: {FINAL_1HR_MP4} ({os.path.getsize(FINAL_1HR_MP4)} bytes)")

if __name__ == "__main__":
    generate_master_cycle()
