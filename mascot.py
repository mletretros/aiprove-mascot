#!/usr/bin/env python3
"""AIProve mascot: 'The Prover'.

One character, four poses, drawn entirely from Pillow primitives in the
broadsheet-meets-terminal register the bounty asks for: newsprint ground,
engraved hatching, a terminal for a head, a wax seal in hand.

No image model, no stock art, no external assets.
"""
from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

PAPER = (236, 229, 212)
PAPER_DIM = (222, 214, 196)
INK = (26, 24, 21)
INK_SOFT = (74, 68, 58)
INK_FAINT = (150, 142, 126)
PHOSPHOR = (86, 138, 96)
PHOSPHOR_DIM = (58, 92, 66)
SEAL = (138, 46, 38)

FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]


def font(idx: int, size: int):
    path = FONTS[idx]
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ---------------------------------------------------------------- primitives


def paper(w: int, h: int, seed: int = 11) -> Image.Image:
    """Newsprint ground: warm base, per-pixel grain, soft vignette."""
    base = Image.new("RGB", (w, h), PAPER)
    grain = Image.effect_noise((w, h), 26).convert("L")
    grain = Image.merge("RGB", (grain, grain, grain))
    return Image.blend(base, Image.blend(base, grain, 0.10), 0.55)


def vignette(im: Image.Image, strength: float = 0.20) -> Image.Image:
    w, h = im.size
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    pad = int(min(w, h) * 0.06)
    d.ellipse([-pad, -pad, w + pad, h + pad], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(min(w, h) * 0.12))
    dark = Image.new("RGB", (w, h), (16, 12, 8))
    return Image.composite(im, Image.blend(im, dark, strength), m)


def hatch(d: ImageDraw.ImageDraw, poly, ink=INK, step: int = 7, angle: float = 45.0, width: int = 1):
    """Fill a polygon with parallel engraved lines clipped to its mask."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    mask = Image.new("L", (int(x1 - x0) + 2, int(y1 - y0) + 2), 0)
    md = ImageDraw.Draw(mask)
    md.polygon([(x - x0, y - y0) for x, y in poly], fill=255)

    layer = Image.new("RGB", mask.size, PAPER)
    ld = ImageDraw.Draw(layer)
    diag = int(math.hypot(*mask.size)) + 8
    rad = math.radians(angle)
    dx, dy = math.cos(rad), math.sin(rad)
    for i in range(-diag, diag, step):
        cx, cy = mask.size[0] / 2, mask.size[1] / 2
        px, py = cx - dy * i, cy + dx * i
        ld.line([(px - dx * diag, py - dy * diag), (px + dx * diag, py + dy * diag)], fill=ink, width=width)
    im_root = d._image if hasattr(d, "_image") else None
    if im_root is None:
        return
    im_root.paste(layer, (int(x0) - 1, int(y0) - 1), mask)


def hatch_on(im: Image.Image, poly, ink=INK, step: int = 7, angle: float = 45.0, width: int = 1):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, y0 = int(min(xs)), int(min(ys))
    w, h = int(max(xs)) - x0 + 2, int(max(ys)) - y0 + 2
    if w <= 0 or h <= 0:
        return
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon([(x - x0, y - y0) for x, y in poly], fill=255)
    layer = Image.new("RGB", (w, h), PAPER)
    ld = ImageDraw.Draw(layer)
    diag = int(math.hypot(w, h)) + 8
    rad = math.radians(angle)
    dx, dy = math.cos(rad), math.sin(rad)
    for i in range(-diag, diag, step):
        cx, cy = w / 2, h / 2
        px, py = cx - dy * i, cy + dx * i
        ld.line([(px - dx * diag, py - dy * diag), (px + dx * diag, py + dy * diag)], fill=ink, width=width)
    im.paste(layer, (x0, y0), mask)


def tracked(d: ImageDraw.ImageDraw, xy, s: str, fnt, fill=INK, tracking: float = 3.0, anchor_x: str = "left"):
    widths = [d.textlength(ch, font=fnt) for ch in s]
    total = sum(widths) + tracking * (len(s) - 1)
    x, y = xy
    if anchor_x == "center":
        x -= total / 2
    elif anchor_x == "right":
        x -= total
    for ch, w in zip(s, widths):
        d.text((x, y), ch, font=fnt, fill=fill)
        x += w + tracking
    return total


def rule(d: ImageDraw.ImageDraw, x0: float, x1: float, y: float, w: int = 2, fill=INK):
    d.line([(x0, y), (x1, y)], fill=fill, width=w)


def double_rule(d: ImageDraw.ImageDraw, x0: float, x1: float, y: float, thick=6, gap=6, thin=2, fill=INK):
    d.line([(x0, y), (x1, y)], fill=fill, width=thick)
    d.line([(x0, y + gap + thick // 2), (x1, y + gap + thick // 2)], fill=fill, width=thin)


def epicycloid(cx, cy, r, k=13, amp=5.0, phase=0.0, steps=720):
    pts = []
    for i in range(steps + 1):
        a = 2 * math.pi * i / steps
        rr = r + amp * math.sin(k * a + phase)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def arc_text(im: Image.Image, cx, cy, r, s: str, fnt, fill=INK, start_deg=-90, tracking=1.4, flip=False):
    d = ImageDraw.Draw(im)
    widths = [d.textlength(ch, font=fnt) for ch in s]
    total = sum(widths) + tracking * (len(s) - 1)
    angle_span = total / r
    a = math.radians(start_deg) - (0 if flip else angle_span / 2)
    for ch, w in zip(s, widths):
        da = (w + tracking) / 2 / r
        ang = a + da
        ch_im = Image.new("RGBA", (int(w) + 14, fnt.size * 2), (0, 0, 0, 0))
        ImageDraw.Draw(ch_im).text((7, 0), ch, font=fnt, fill=fill + (255,))
        rot = math.degrees(ang) + (270 if not flip else 90)
        ch_im = ch_im.rotate(-rot, expand=True, resample=Image.BICUBIC)
        px = cx + r * math.cos(ang) - ch_im.width / 2
        py = cy + r * math.sin(ang) - ch_im.height / 2
        im.paste(ch_im, (int(px), int(py)), ch_im)
        a = ang + da


# ---------------------------------------------------------------- the character

HEAD_W, HEAD_H = 420, 300


def terminal_head(im: Image.Image, cx: float, cy: float, scale: float = 1.0, gaze: float = 0.0, dirty: bool = True):
    """The head is a terminal window: bezel, phosphor screen, cursor, two status lines."""
    w, h = HEAD_W * scale, HEAD_H * scale
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    d = ImageDraw.Draw(im)

    # cast shadow on the paper
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0 + 10, y0 + 14, x1 + 10, y1 + 14], radius=18 * scale, fill=(30, 24, 16, 60))
    im.paste(Image.alpha_composite(im.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(9))).convert("RGB"), (0, 0))

    # bezel
    d.rounded_rectangle([x0, y0, x1, y1], radius=18 * scale, fill=(30, 27, 24), outline=INK, width=max(2, int(3 * scale)))
    # screen
    pad = 22 * scale
    sx0, sy0, sx1, sy1 = x0 + pad, y0 + pad * 0.85, x1 - pad, y1 - pad * 0.85
    d.rounded_rectangle([sx0, sy0, sx1, sy1], radius=8 * scale, fill=(18, 22, 19))
    # phosphor scanlines
    step = max(2, int(4 * scale))
    for yy in range(int(sy0) + 3, int(sy1) - 2, step):
        alpha = 0.16 if (yy // step) % 2 else 0.09
        d.line([(sx0 + 4, yy), (sx1 - 4, yy)], fill=(int(40 + 46 * alpha * 6), int(70 + 60 * alpha * 6), int(46 + 46 * alpha * 6)), width=1)
    # a line of code on the screen, plus a cursor
    fnt = font(2, int(34 * scale))
    tx = sx0 + 16 * scale
    ty = sy0 + 12 * scale
    d.text((tx, ty), "> grade --open", font=fnt, fill=(126, 196, 138))
    d.text((tx, ty + 44 * scale), "  metric: published", font=font(3, int(28 * scale)), fill=(96, 156, 108))
    cw = d.textlength("  metric: published", font=font(3, int(28 * scale)))
    d.rectangle([tx + cw + 6, ty + 50 * scale, tx + cw + 16 * scale, ty + 74 * scale], fill=(150, 220, 160))
    # status lamp
    d.ellipse([sx1 - 26 * scale, sy1 - 24 * scale, sx1 - 12 * scale, sy1 - 10 * scale], fill=(170, 226, 176))
    # bezel screws
    for (px, py) in [(x0 + 9 * scale, y0 + 9 * scale), (x1 - 9 * scale, y0 + 9 * scale),
                     (x0 + 9 * scale, y1 - 9 * scale), (x1 - 9 * scale, y1 - 9 * scale)]:
        d.ellipse([px - 3 * scale, py - 3 * scale, px + 3 * scale, py + 3 * scale], fill=(120, 112, 100))
    # the gaze: the screen's own glow leans where the head looks
    if gaze:
        from PIL import ImageChops

        glow = Image.new("RGB", im.size, (0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gx = cx + gaze * w * 0.16
        gd.ellipse([gx - 70 * scale, cy - 46 * scale, gx + 70 * scale, cy + 46 * scale], fill=(34, 74, 42))
        engulf = ImageChops.add(im, glow.filter(ImageFilter.GaussianBlur(30 * scale)))
        im.paste(engulf, (0, 0))


def coat(im: Image.Image, cx: float, cy: float, w: float, h: float):
    """A long coat, engraved: two lapels, hatched body, high collar."""
    d = ImageDraw.Draw(im)
    body = [
        (cx - w / 2, cy + h),
        (cx - w / 2 + w * 0.06, cy + h * 0.18),
        (cx - w * 0.30, cy),
        (cx + w * 0.30, cy),
        (cx + w / 2 - w * 0.06, cy + h * 0.18),
        (cx + w / 2, cy + h),
    ]
    d.polygon(body, fill=PAPER)
    hatch_on(im, body, ink=INK, step=6, angle=64, width=1)
    # outer contour
    d.line(body[1:] + [body[0]], fill=INK, width=4)
    # lapels
    lap_l = [(cx - w * 0.30, cy), (cx - w * 0.06, cy + h * 0.16), (cx - w * 0.10, cy + h * 0.5), (cx - w * 0.34, cy + h * 0.22)]
    lap_r = [(cx + w * 0.30, cy), (cx + w * 0.06, cy + h * 0.16), (cx + w * 0.10, cy + h * 0.5), (cx + w * 0.34, cy + h * 0.22)]
    for lp in (lap_l, lap_r):
        d.polygon(lp, fill=PAPER_DIM)
        d.line(lp + [lp[0]], fill=INK, width=3)
    # button line + buttons
    d.line([(cx, cy + h * 0.20), (cx, cy + h * 0.94)], fill=INK, width=3)
    for i in range(4):
        by = cy + h * (0.30 + i * 0.17)
        d.ellipse([cx - 8, by - 8, cx + 8, by + 8], fill=INK)


def seal_coin(im: Image.Image, cx: float, cy: float, r: float, label_ring: str = "GRADED IN THE OPEN"):
    """The wax seal from the poster, reused as the character's token of office."""
    d = ImageDraw.Draw(im)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(226, 214, 192), outline=INK, width=3)
    d.polygon(epicycloid(cx, cy, r * 0.92, k=15, amp=r * 0.05), outline=INK)
    d.ellipse([cx - r * 0.62, cy - r * 0.62, cx + r * 0.62, cy + r * 0.62], fill=SEAL)
    d.ellipse([cx - r * 0.48, cy - r * 0.48, cx + r * 0.48, cy + r * 0.48], outline=(246, 232, 214), width=2)
    tracked(d, (cx, cy - r * 0.16), "PROVE", font(0, int(r * 0.34)), fill=(246, 232, 214), tracking=2, anchor_x="center")
    arc_text(im, cx, cy, r * 0.80, label_ring, font(3, max(9, int(r * 0.14))), fill=INK, start_deg=-90)
    arc_text(im, cx, cy, r * 0.80, "ONE CHARACTER, FOUR POSES", font(3, max(9, int(r * 0.13))),
             fill=INK, start_deg=90, flip=True)


def arm(d: ImageDraw.ImageDraw, pts, width=26, cuff=True):
    d.line(pts, fill=INK, width=width + 6)
    d.line(pts, fill=PAPER, width=width)
    if cuff:
        for (px, py) in [pts[-1]]:
            d.ellipse([px - width * 0.6, py - width * 0.6, px + width * 0.6, py + width * 0.6], fill=PAPER, outline=INK, width=4)


def legs(im: Image.Image, cx: float, hip_y: float, bottom: float, spread: float = 1.0):
    d = ImageDraw.Draw(im)
    for s in (-1, 1):
        hipx = cx + s * 46 * spread
        footx = cx + s * 70 * spread
        poly = [(hipx - 30, hip_y), (hipx + 30, hip_y), (footx + 26, bottom), (footx - 30, bottom)]
        d.polygon(poly, fill=PAPER)
        hatch_on(im, poly, ink=INK, step=8, angle=100, width=1)
        d.line(poly + [poly[0]], fill=INK, width=4)
        # boot
        d.rectangle([footx - 34, bottom - 26, footx + 36, bottom], fill=INK)
    return


def ground_marks(d: ImageDraw.ImageDraw, cx: float, y: float, w: float):
    for i, frac in enumerate([1.0, 0.78, 0.58, 0.4]):
        gw = w * frac
        d.line([(cx - gw / 2, y + i * 9), (cx + gw / 2, y + i * 9)], fill=INK if i == 0 else INK_FAINT, width=3 if i == 0 else 2)


# ---------------------------------------------------------------- poses


def pose_idle(t: float = 0.0, W: int = 1400, H: int = 1800) -> Image.Image:
    im = paper(W, H, seed=11)
    d = ImageDraw.Draw(im)
    cx = W / 2
    head_cy = 470
    terminal_head(im, cx, head_cy, scale=1.0, gaze=math.sin(t * 3) * 0.3)
    coat(im, cx, 640, 470, 720)
    legs(im, cx, 1320, 1620, spread=1.0)
    # left arm down, right arm holding the seal up
    arm(d, [(cx - 230, 720), (cx - 300, 900), (cx - 320, 1030)], width=26)
    arm(d, [(cx + 230, 720), (cx + 320, 800), (cx + 360, 700)], width=26)
    seal_coin(im, cx + 372, 660, 96)
    # a floating rule of text, the way a broadsheet sets a caption
    d2 = ImageDraw.Draw(im)
    tracked(d2, (cx, 1690), "THE PROVER  ·  IT DOES NOT ASK PERMISSION", font(3, 22), fill=INK_SOFT, tracking=3, anchor_x="center")
    rule(d2, cx - 300, cx + 300, 1650, 3)
    return vignette(im)


def pose_stamp(t: float = 0.0, W: int = 1400, H: int = 1800) -> Image.Image:
    im = paper(W, H, seed=23)
    d = ImageDraw.Draw(im)
    cx = W / 2 + 30
    head_cy = 520
    terminal_head(im, cx, head_cy, scale=0.98, gaze=0.6)
    coat(im, cx, 690, 460, 700)
    legs(im, cx, 1350, 1630, spread=0.9)

    # a card on the paper being stamped
    card = [cx - 340, 1420, cx + 300, 1640]
    d.rectangle(card, fill=(244, 238, 224), outline=INK, width=4)
    for i in range(3):
        d.line([(card[0] + 26, card[1] + 40 + i * 34), (card[0] + 26 + 260 - i * 40, card[1] + 40 + i * 34)], fill=INK_FAINT, width=5)
    tracked(d, (card[0] + 26, card[1] + 8), "VERTICAL: SUBMISSION", font(3, 18), fill=INK_SOFT, tracking=2)

    # arm driving the seal down onto the card
    arm(d, [(cx + 210, 760), (cx + 320, 980), (cx + 150, 1330)], width=26)
    seal_coin(im, cx + 120, 1380, 88, label_ring="GRADED · IN · THE · OPEN")

    # impact marks
    for k in range(7):
        a = math.pi * (0.15 + 0.7 * k / 6)
        r0, r1 = 108, 150 + 16 * math.sin(k * 2.1)
        d.line([(cx + 120 + r0 * math.cos(a + 2.1), 1380 + r0 * math.sin(a + 2.1) * 0.5),
                (cx + 120 + r1 * math.cos(a + 2.1), 1380 + r1 * math.sin(a + 2.1) * 0.5)], fill=INK, width=4)

    tracked(d, (W / 2, 120), "POSE II  ·  STAMPING A VERDICT", font(3, 22), fill=INK_SOFT, tracking=4, anchor_x="center")
    return vignette(im)


def pose_ledger(t: float = 0.0, W: int = 1400, H: int = 1800) -> Image.Image:
    im = paper(W, H, seed=37)
    d = ImageDraw.Draw(im)
    cx = W / 2
    terminal_head(im, cx, 470, scale=0.94, gaze=-0.2)
    coat(im, cx, 620, 450, 690)
    legs(im, cx, 1290, 1600, spread=1.05)

    # the board: a small broadsheet held open
    bx0, by0, bx1, by1 = cx - 380, 820, cx + 380, 1260
    d.polygon([(bx0, by0), (bx1, by0 - 20), (bx1, by1), (bx0, by1 + 22)], fill=(244, 238, 224), outline=INK, width=4)
    rule(d, bx0 + 30, bx1 - 30, by0 + 56, 4)
    tracked(d, (bx0 + 30, by0 + 22), "THE BOARD · OPEN BOUNTIES", font(3, 20), fill=INK, tracking=3)
    rows = [("byte golf", "41,200"), ("latency", "41,200"), ("backtest", "82,400"), ("forecast", "150")]
    for i, (name, amt) in enumerate(rows):
        yy = by0 + 100 + i * 62
        d.text((bx0 + 34, yy), name, font=font(3, 26), fill=INK)
        d.text((bx1 - 40 - d.textlength(amt, font=font(3, 26)), yy), amt, font=font(3, 26), fill=INK)
        rule(d, bx0 + 30, bx1 - 30, yy + 44, 1, INK_FAINT)

    # both arms holding the page
    arm(d, [(cx - 220, 700), (cx - 350, 850), (bx0 + 40, 900)], width=24)
    arm(d, [(cx + 220, 700), (cx + 350, 850), (bx1 - 40, 880)], width=24)
    tracked(d, (W / 2, 120), "POSE III  ·  READING THE BOARD", font(3, 22), fill=INK_SOFT, tracking=4, anchor_x="center")
    return vignette(im)


def mark_square(size: int = 1200) -> Image.Image:
    """The badge: head only, on paper, ringed like a seal. Usable at 32 px."""
    im = paper(size, size, seed=53)
    d = ImageDraw.Draw(im)
    cx = cy = size / 2
    d.polygon(epicycloid(cx, cy, size * 0.455, k=17, amp=size * 0.012), outline=INK, width=3)
    d.ellipse([cx - size * 0.415, cy - size * 0.415, cx + size * 0.415, cy + size * 0.415], outline=INK, width=5)
    terminal_head(im, cx, cy - size * 0.045, scale=size / 900 * 0.86, gaze=0)
    arc_text(im, cx, cy, size * 0.395, "AI PROVE", font(0, int(size * 0.062)), fill=INK, start_deg=-90)
    arc_text(im, cx, cy, size * 0.395, "GRADED IN THE OPEN", font(3, int(size * 0.05)), fill=INK, start_deg=90, flip=True)
    return im


def contact_sheet(poses, W: int = 2400, H: int = 1500) -> Image.Image:
    im = paper(W, H, seed=71)
    d = ImageDraw.Draw(im)
    tracked(d, (W / 2, 58), "AI PROVE  ·  THE PROVER", font(0, 62), tracking=10, anchor_x="center")
    double_rule(d, 120, W - 120, 150, thick=7, gap=7, thin=2)
    tracked(d, (W / 2, 176), "ONE CHARACTER  ·  FOUR POSES  ·  DRAWN FROM PRIMITIVES",
            font(3, 24), fill=INK_SOFT, tracking=6, anchor_x="center")

    cell_w, cell_h = W / 4, H - 300
    labels = ["I  ·  IDLE", "II  ·  STAMP", "III  ·  BOARD", "IV  ·  BADGE"]
    for i, (p, lab) in enumerate(zip(poses, labels)):
        x0 = i * cell_w
        thumb = p.copy()
        thumb.thumbnail((int(cell_w - 40), int(cell_h - 90)), Image.LANCZOS)
        im.paste(thumb, (int(x0 + (cell_w - thumb.width) / 2), int(240 + (cell_h - 90 - thumb.height) / 2)))
        d.rectangle([x0 + 18, 240, x0 + cell_w - 18, H - 60], outline=INK_FAINT, width=2)
        tracked(d, (x0 + cell_w / 2, H - 108), lab, font(3, 22), fill=INK, tracking=4, anchor_x="center")

    tracked(d, (W / 2, H - 42), "NO IMAGE MODEL  ·  PILLOW PRIMITIVES  ·  PRIME SOLVER 3",
            font(3, 20), fill=INK_SOFT, tracking=3, anchor_x="center")
    return vignette(im, 0.12)


# ---------------------------------------------------------------- render


def main():
    os.makedirs(OUT, exist_ok=True)
    p1 = pose_idle(0.6)
    p1.save(os.path.join(OUT, "pose-1-idle.png"))
    p2 = pose_stamp(0)
    p2.save(os.path.join(OUT, "pose-2-stamp.png"))
    p3 = pose_ledger(0)
    p3.save(os.path.join(OUT, "pose-3-board.png"))
    p4 = mark_square(1200)
    p4.save(os.path.join(OUT, "pose-4-badge.png"))
    sheet = contact_sheet([p1, p2, p3, p4])
    sheet.save(os.path.join(OUT, "sheet.png"))
    for s in (32, 64, 128, 512):
        mark_square(1200).resize((s, s), Image.LANCZOS).save(os.path.join(OUT, f"badge-{s}.png"))
    for f in sorted(os.listdir(OUT)):
        im = Image.open(os.path.join(OUT, f))
        print(f, im.size, f"{os.path.getsize(os.path.join(OUT, f)) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
