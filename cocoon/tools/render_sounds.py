"""Synthesize the Cocoon sound set into astralabs/sounds/*.ogg.

The sounds are lab equipment rather than a game: short sine ticks, clean blips and relay clicks. Pitch changes
step instead of sliding, the way the brand's Flick motion steps, and the louder events (launch, achievements)
are the only ones with any tail. Everything is synthesized here, so there is nothing to license.

  python3 tools/render_sounds.py
"""
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

import brand as B

SR = 48000


def silence(ms):
    return np.zeros(int(SR * ms / 1000))


def tone(f, ms, decay=None, harm=.12, attack=1.5):
    """A sine with a touch of second harmonic, a short attack and an exponential decay."""
    t = np.arange(int(SR * ms / 1000)) / SR
    x = np.sin(2 * np.pi * f * t) + harm * np.sin(4 * np.pi * f * t)
    env = np.minimum(1, t / (attack / 1000)) * np.exp(-t / ((decay or ms / 3) / 1000))
    env *= np.minimum(1, (t[-1] - t) / .002)                           # 2ms fade so a cut-off blip never clicks
    return x * env


def click(ms=4, bright=6000, seed=1):
    """A relay click: a few milliseconds of filtered noise."""
    rng = np.random.default_rng(seed)
    n = int(SR * ms / 1000)
    x = rng.standard_normal(n)
    a = np.exp(-2 * np.pi * bright / SR)                               # one-pole low-pass
    y = np.zeros(n)
    for i in range(1, n):
        y[i] = (1 - a) * x[i] + a * y[i - 1]
    return y * np.exp(-np.arange(n) / (n / 4)) * 3


def steps(freqs, step_ms, tail_ms, gap_ms=0, **kw):
    """Stepped pitches, each its own blip. The last one rings out."""
    parts = []
    for i, f in enumerate(freqs):
        last = i == len(freqs) - 1
        parts.append(tone(f, tail_ms if last else step_ms, decay=(tail_ms / 3 if last else step_ms / 2), **kw))
        if not last and gap_ms:
            parts.append(silence(gap_ms))
    return np.concatenate(parts)


def mix(*layers):
    """Sum (offset_ms, signal) pairs."""
    n = max(int(SR * o / 1000) + len(s) for o, s in layers)
    out = np.zeros(n)
    for o, s in layers:
        i = int(SR * o / 1000)
        out[i:i + len(s)] += s
    return out


def buzz(f, ms):
    """A soft square: odd harmonics, rolled off."""
    t = np.arange(int(SR * ms / 1000)) / SR
    x = sum(np.sin(2 * np.pi * f * k * t) / k for k in (1, 3, 5, 7))
    return x * np.minimum(1, t / .002) * np.minimum(1, (t[-1] - t) / .01)


def chatter(ms, seed=3):
    """Disk-activity ticks for saving."""
    rng = np.random.default_rng(seed)
    out = silence(ms)
    t = 0
    while t < ms - 20:
        s = tone(rng.uniform(2500, 4000), 10, decay=3) * rng.uniform(.3, .7)
        i = int(SR * t / 1000)
        out[i:i + len(s)] += s[:len(out) - i]
        t += rng.uniform(18, 45)
    return out


SOUNDS = {
    # name: (signal, peak level in dBFS)
    'navigate': (mix((0, tone(2200, 22, decay=6)), (0, click(2) * .3)), -16),
    'select': (steps([1320, 1760], 40, 120), -10),
    'back': (steps([1760, 1175], 40, 110), -11),
    'folder_open': (steps([988, 1320, 1760], 30, 110), -12),
    'folder_close': (steps([1760, 1320, 988], 30, 100), -12),
    'launch': (mix((0, click(5)), (20, steps([440, 660, 880, 1320, 1760], 40, 420, harm=.2))), -8),
    'error': (mix((0, buzz(196, 70)), (120, buzz(196, 70))) * .5, -10),
    'notification': (mix((0, tone(1760, 160, decay=50)), (90, tone(2349, 260, decay=80))), -10),
    'discord_open': (steps([1175, 1568], 35, 110), -12),
    'discord_close': (steps([1568, 1175], 35, 100), -12),
    'screen_swap': (mix((0, click(4)), (10, steps([660, 990, 1320], 25, 90))), -12),
    'grid_zoom_in': (steps([880, 1175], 30, 70), -14),
    'grid_zoom_out': (steps([1175, 880], 30, 70), -14),
    'reorder_pickup': (mix((0, click(4)), (8, tone(660, 90, decay=25))), -12),
    'reorder_place': (mix((0, tone(880, 60, decay=15)), (40, click(5, seed=2))), -12),
    'open_edit': (mix((0, click(3)), (5, tone(1480, 110, decay=30))), -12),
    'pop': (steps([1320, 660], 18, 60), -12),
    'slider_increase': (tone(2093, 18, decay=5), -18),
    'slider_decrease': (tone(1568, 18, decay=5), -18),
    'saving': (chatter(320), -16),
    'saving_end': (steps([1760, 1760], 45, 120, gap_ms=25), -12),
    'retroachievements': (steps([1319, 1760, 2093, 2637], 70, 520, harm=.18), -9),
}


def write(name, sig, peak_db):
    sig = sig / max(1e-9, np.abs(sig).max()) * 10 ** (peak_db / 20)
    fade = min(len(sig), int(SR * .004))
    sig[-fade:] *= np.linspace(1, 0, fade)
    pcm = (np.clip(sig, -1, 1) * 32767).astype('<i2')
    out = B.THEME / 'sounds' / f'{name}.ogg'
    with tempfile.NamedTemporaryFile(suffix='.wav') as tmp:
        with wave.open(tmp.name, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp.name, '-c:a', 'libvorbis', '-q:a', '6', str(out)], check=True)
    return out


if __name__ == '__main__':
    (B.THEME / 'sounds').mkdir(parents=True, exist_ok=True)
    for name, (sig, peak) in SOUNDS.items():
        out = write(name, sig.astype(np.float64), peak)
        print(f'{out.relative_to(B.ROOT)}  {len(sig) / SR * 1000:.0f} ms')
