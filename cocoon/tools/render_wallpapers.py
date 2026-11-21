"""Render the Cocoon wallpapers.

  main.webm      1920x1080  the dot field in the Sea idle, the lockup, and the scope: one Lissajous phase
                            and one vector-mark phase per loop
  external.webm  1240x1080  the dot field in the Sea idle with the corner plus marks, quiet behind the UI

Both are 30 fps VP9 loops of 48s that join seamlessly: every wave in the Sea completes a whole number of
cycles per loop, and the scope is dark at the seam. Static WebP versions go to extras/ for anyone who
would rather save the battery.

  python3 tools/render_wallpapers.py            render everything
  python3 tools/render_wallpapers.py main       only re-encode one video (main or external)
  python3 tools/render_wallpapers.py --frames   only write a few check frames to docs/images/
"""
import subprocess
import sys

import numpy as np
from PIL import Image

import brand as B

FPS, LOOP = 30, 48.0
MAIN, EXTERNAL = (1920, 1080), (1240, 1080)
LISS_AT, MARK_AT = 8000, 28000                   # ms into the loop
LOCKUP_W = 720


def static_layer(w, h, lockup):
    s, ctx = B.surface(w, h)
    B.plus_marks(ctx, w, h)
    if lockup:
        img = B.svg_image(B.BRANDING / 'astralabs-lockup.svg', LOCKUP_W)
        B.paste_premul(ctx, img, (w - img.width) // 2, (h - img.height) // 2)
    s.flush()
    return B.to_rgba(s)


def main_scene():
    w, h = MAIN
    field = B.DotField(w, h, LOOP)
    A = min(w, h) * .3
    liss = B.lissajous_samples(LISS_AT, w / 2, h / 2, A, 2, 3)
    mark = B.mark_samples(MARK_AT, w / 2, h / 2, A)
    top = static_layer(w, h, lockup=True)

    def frame(t_ms):
        s, ctx = B.surface(w, h)
        B.draw_beam(ctx, liss, t_ms, 340, .55)
        B.draw_beam(ctx, mark, t_ms, 650, .6)
        s.flush()
        return B.compose(field.coverage(t_ms / 1000), [B.to_rgba(s), top])
    return frame


def external_scene():
    w, h = EXTERNAL
    field = B.DotField(w, h, LOOP)
    top = static_layer(w, h, lockup=False)
    return lambda t_ms: B.compose(field.coverage(t_ms / 1000), [top])


def encode(frame, size, out, crf):
    w, h = size
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libvpx-vp9', '-crf', str(crf), '-b:v', '0', '-row-mt', '1', '-cpu-used', '4', '-pix_fmt', 'yuv420p', '-an', str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(LOOP * FPS)
    for i in range(n):
        p.stdin.write(frame(i * 1000 / FPS).tobytes())
        if i % 120 == 0:
            print(f'  {out.name} {i}/{n}', flush=True)
    p.stdin.close()
    if p.wait():
        sys.exit(f'ffmpeg failed on {out}')
    print(f'{out.relative_to(B.ROOT)} ({out.stat().st_size / 1e6:.1f} MB)')


if __name__ == '__main__':
    main_f, ext_f = main_scene(), external_scene()
    only = [a for a in sys.argv[1:] if a in ('main', 'external')]
    docs = B.ROOT / 'docs' / 'images'
    if '--frames' in sys.argv:
        for t in (0, LISS_AT + 4000, MARK_AT + 1500, MARK_AT + 5000):
            Image.fromarray(main_f(t)).save(docs / f'check-main-{t}.png')
        Image.fromarray(ext_f(0)).save(docs / 'check-external.png')
        sys.exit()

    extras = B.ROOT / 'extras' / 'wallpapers'
    extras.mkdir(parents=True, exist_ok=True)
    Image.fromarray(main_f(0)).save(extras / 'main.webp', quality=92)
    Image.fromarray(ext_f(0)).save(extras / 'external.webp', quality=92)
    Image.fromarray(main_f(LISS_AT + 4000)).resize((1280, 720), Image.LANCZOS).save(B.THEME / 'preview.png')
    Image.fromarray(main_f(MARK_AT + 5000)).save(docs / 'main.png')
    Image.fromarray(ext_f(0)).save(docs / 'external.png')

    wp = B.THEME / 'wallpapers'
    wp.mkdir(parents=True, exist_ok=True)
    if not only or 'main' in only:
        encode(main_f, MAIN, wp / 'main.webm', crf=24)          # finer: keeps the faint end of the beam trail
    if not only or 'external' in only:
        encode(ext_f, EXTERNAL, wp / 'external.webm', crf=30)
