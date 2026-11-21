"""Render the smart-folder art into astralabs/smart_folders/{key}/.

  icon.png  512x512    a line-art glyph in Bone with one Acid detail, on the dot grid
  hero.png  1920x1080  the dot field with the glyph drawn large and faint on the right
  logo.png  wordmark   the folder name set like the [ASTRA/LABS] wordmark: Martian Mono 300 at full width,
                       wide tracking, Acid brackets and an Acid slash between words

  python3 tools/render_smart_folders.py
"""
import math

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import brand as B

FOLDERS = {
    # key: words in the logo
    'favorites': ['FAVORITES'],
    'recent': ['RECENT'],
    'most_played': ['MOST', 'PLAYED'],
    'unplayed': ['UNPLAYED'],
    'newly_added': ['NEWLY', 'ADDED'],
    'android_games': ['ANDROID', 'GAMES'],
    'emulators': ['EMULATORS'],
}
STROKE = 14


# ---------------------------------------------------------------- glyphs, drawn in a 512 box

# Icons draw at full strength with filled details. Heroes switch to outlines only, with the Bone line work faint
# and the Acid detail crisp, so a large glyph never turns into a block of color.
STYLE = {'bone': 1.0, 'outline': False}


def _bone(ctx):
    ctx.set_source_rgba(*B.rgb01(B.BONE), STYLE['bone'])


def _acid(ctx):
    ctx.set_source_rgb(*B.rgb01(B.ACID))


def _fill(ctx):
    ctx.stroke() if STYLE['outline'] else ctx.fill()


def star(ctx, a):
    pts = [(256 + (150 if i % 2 == 0 else 62) * math.sin(i * math.pi / 5), 266 - (150 if i % 2 == 0 else 62) * math.cos(i * math.pi / 5)) for i in range(10)]
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    _acid(ctx)
    ctx.stroke()


def clock(ctx, a):
    ctx.arc(256, 256, 150, 0, 2 * math.pi)
    _bone(ctx)
    ctx.stroke()
    ctx.move_to(256, 256)
    ctx.line_to(256, 170)                    # hour hand
    ctx.stroke()
    ctx.move_to(256, 256)
    ctx.line_to(256 + 110 * math.cos(math.radians(-20)), 256 - 110 * math.sin(math.radians(-20)))  # minute hand
    _acid(ctx)
    ctx.stroke()


def bars(ctx, a):
    base, w, gap = 386, 72, 32
    x0 = 256 - (3 * w + 2 * gap) / 2
    for i, hgt in enumerate((120, 190, 260)):
        x = x0 + i * (w + gap)
        ctx.rectangle(x, base - hgt, w, hgt)
        if i == 2:
            _acid(ctx)
            _fill(ctx)
        else:
            _bone(ctx)
            ctx.stroke()


def play(ctx, a):
    ctx.move_to(176, 116)
    ctx.line_to(176, 396)
    ctx.line_to(176 + 280 * math.sqrt(3) / 2, 256)
    ctx.close_path()
    _bone(ctx)
    ctx.stroke()
    ctx.rectangle(392, 104, 28, 28)          # status light: not started
    _acid(ctx)
    _fill(ctx)


def new(ctx, a):
    _bone(ctx)
    lo, hi, arm = 116, 396, 64                # corner ticks of a frame
    for x, y, dx, dy in ((lo, lo, 1, 1), (hi, lo, -1, 1), (lo, hi, 1, -1), (hi, hi, -1, -1)):
        ctx.move_to(x + dx * arm, y)
        ctx.line_to(x, y)
        ctx.line_to(x, y + dy * arm)
    ctx.stroke()
    ctx.move_to(256, 176)
    ctx.line_to(256, 336)
    ctx.move_to(176, 256)
    ctx.line_to(336, 256)
    _acid(ctx)
    ctx.stroke()


def gamepad(ctx, a):
    _bone(ctx)
    ctx.move_to(96, 196)                      # body with two grips, all square corners
    ctx.line_to(416, 196)
    ctx.line_to(436, 356)
    ctx.line_to(356, 356)
    ctx.line_to(326, 316)
    ctx.line_to(186, 316)
    ctx.line_to(156, 356)
    ctx.line_to(76, 356)
    ctx.close_path()
    ctx.stroke()
    ctx.move_to(166, 226)                     # d-pad
    ctx.line_to(166, 286)
    ctx.move_to(136, 256)
    ctx.line_to(196, 256)
    ctx.stroke()
    ctx.rectangle(330, 228, 24, 24)
    _fill(ctx)
    ctx.rectangle(362, 260, 24, 24)
    _acid(ctx)
    _fill(ctx)


def chip(ctx, a):
    _bone(ctx)
    ctx.rectangle(156, 156, 200, 200)
    ctx.stroke()
    for i in range(4):
        o = 196 + i * 40
        for x1, y1, x2, y2 in ((o, 156, o, 116), (o, 356, o, 396), (156, o, 116, o), (356, o, 396, o)):
            ctx.move_to(x1, y1)
            ctx.line_to(x2, y2)
    ctx.stroke()
    ctx.rectangle(216, 216, 80, 80)
    _acid(ctx)
    _fill(ctx)


GLYPHS = {'favorites': star, 'recent': clock, 'most_played': bars, 'unplayed': play,
          'newly_added': new, 'android_games': gamepad, 'emulators': chip}


def glyph_layer(w, h, draw, x, y, size, stroke=STROKE):
    s, ctx = B.surface(w, h)
    ctx.translate(x, y)
    ctx.scale(size / 512, size / 512)
    ctx.set_line_width(stroke)
    ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
    ctx.set_line_join(cairo.LINE_JOIN_MITER)
    draw(ctx, 1)
    s.flush()
    return B.to_rgba(s)


# ---------------------------------------------------------------- wordmark-style logo

def logo(words, cap=72, ss=4):
    """Drawn as two coverage masks (Acid, Bone) at ss x the size, then downsampled, so edges are clean."""
    capx = cap * ss
    font = ImageFont.truetype(str(B.FONT), 100)
    font.set_variation_by_axes([300, 112])                    # weight, width: as the lockup
    probe = font.getbbox('H')
    size = round(100 * capx / (probe[3] - probe[1]))
    font = ImageFont.truetype(str(B.FONT), size)
    font.set_variation_by_axes([300, 112])
    top_off = font.getbbox('H')[1]
    track = .36 * size
    adv = font.getlength('M') + track                         # monospace advance plus tracking

    # proportions taken from the lockup SVG, relative to cap height
    br_h, br_w, br_arm = capx * 1.27, capx * .118, capx * .4
    sl_dx, sl_w = capx * .47, capx * .12
    gap = capx * .9                                           # bracket to first letter

    n = sum(len(w) for w in words) + (len(words) - 1)         # a slash takes one letter slot
    pad = capx * .2
    W = round((pad * 2 + br_arm + gap + n * adv - track + gap + br_arm) / ss) * ss
    H = round((pad * 2 + br_h) / ss) * ss
    acid, bone = Image.new('L', (W, H)), Image.new('L', (W, H))
    da, db = ImageDraw.Draw(acid), ImageDraw.Draw(bone)
    top, bot = pad, pad + br_h
    base_top = pad + (br_h - capx) / 2                        # letters sit centered on the brackets

    def bracket(x, left):
        stem = x if left else x + br_arm - br_w
        da.rectangle([stem, top, stem + br_w, bot], fill=255)
        da.rectangle([x, top, x + br_arm, top + br_w], fill=255)
        da.rectangle([x, bot - br_w, x + br_arm, bot], fill=255)

    x = pad
    bracket(x, True)
    x += br_arm + gap
    for wi, word in enumerate(words):
        if wi:
            cx = x + (adv - track) / 2                        # slash, centered in its slot
            da.polygon([(cx + sl_dx / 2, top), (cx + sl_dx / 2 + sl_w, top), (cx - sl_dx / 2 + sl_w, bot), (cx - sl_dx / 2, bot)], fill=255)
            x += adv
        for ch in word:
            db.text((x, base_top - top_off), ch, font=font, fill=255)
            x += adv
    bracket(x - track + gap, False)

    size_out = (W // ss, H // ss)
    a, b = acid.resize(size_out, Image.LANCZOS), bone.resize(size_out, Image.LANCZOS)
    ma, mb = np.asarray(a, np.float32) / 255, np.asarray(b, np.float32) / 255
    alpha = np.clip(ma + mb, 0, 1)
    rgb = np.zeros((*alpha.shape, 3), np.float32)
    for i in range(3):
        rgb[..., i] = (B.ACID[i] * ma + B.BONE[i] * mb) / np.maximum(alpha, 1e-6)
    out = np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


# ---------------------------------------------------------------- render

def icon(key):
    w = h = 512
    field = B.DotField(w, h)
    cov = field.coverage(0) * .8
    return Image.fromarray(B.compose(cov, [glyph_layer(w, h, GLYPHS[key], 0, 0, 512)]))


def hero(key):
    w, h = 1920, 1080
    field = B.DotField(w, h, center=(w * .72, h / 2))
    s, ctx = B.surface(w, h)
    B.plus_marks(ctx, w, h)
    s.flush()
    size = 900
    STYLE.update(bone=.35, outline=True)
    art = glyph_layer(w, h, GLYPHS[key], w * .72 - size / 2, (h - size) / 2, size, stroke=2.4)
    STYLE.update(bone=1.0, outline=False)
    return Image.fromarray(B.compose(field.coverage(0), [art, B.to_rgba(s)]))


if __name__ == '__main__':
    for key, words in FOLDERS.items():
        out = B.THEME / 'smart_folders' / key
        out.mkdir(parents=True, exist_ok=True)
        icon(key).save(out / 'icon.png', optimize=True)
        hero(key).save(out / 'hero.png', optimize=True)
        logo(words).save(out / 'logo.png', optimize=True)
        print(f'{out.relative_to(B.ROOT)}/  icon, hero, logo')

    # contact sheet for the README: every icon, then every logo
    keys = list(FOLDERS)
    sheet = Image.new('RGB', (len(keys) * 200 + 40, 200 + len(keys) * 56 + 60), B.VOID)
    for i, key in enumerate(keys):
        d = B.THEME / 'smart_folders' / key
        sheet.paste(Image.open(d / 'icon.png').convert('RGB').resize((180, 180), Image.LANCZOS), (20 + i * 200, 20))
        lg = Image.open(d / 'logo.png')
        lg.thumbnail((1000, 44), Image.LANCZOS)
        sheet.paste(lg, (20, 230 + i * 56), lg)
    sheet.save(B.ROOT / 'docs' / 'images' / 'smart-folders.png', optimize=True)
