"""Check the theme and package it as dist/astralabs-cocoon.zip for Cocoon's Import ZIP.

The ZIP uses the same layout as themes from Silk: themes/astralabs/theme.json and so on.
Checks follow the Theme JSON Reference: valid JSON, a name, every referenced file present, known sound names,
and colors in #RRGGBB or #AARRGGBB.

  python3 tools/build_zip.py
"""
import json
import re
import sys
import zipfile

import brand as B

SOUNDS = {'navigate', 'select', 'back', 'folder_open', 'folder_close', 'launch', 'error', 'notification',
          'discord_open', 'discord_close', 'screen_swap', 'grid_zoom_in', 'grid_zoom_out', 'reorder_pickup',
          'reorder_place', 'open_edit', 'pop', 'slider_increase', 'slider_decrease', 'saving', 'saving_end',
          'retroachievements'}
FOLDERS = {'favorites', 'recent', 'most_played', 'unplayed', 'newly_added', 'android_games', 'emulators'}


def check():
    problems = []
    theme = json.loads((B.THEME / 'theme.json').read_text(encoding='utf-8'))
    if not theme.get('name'):
        problems.append('theme.json has no name')
    for key, value in theme.get('color_scheme', {}).items():
        if not re.fullmatch(r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})', value):
            problems.append(f'color {key} is not #RRGGBB or #AARRGGBB: {value}')
    for field in ('wallpaper_main', 'wallpaper_external'):
        ref = theme.get(field)
        if ref and not list((B.THEME / 'wallpapers').glob(f'{ref}.*')):
            problems.append(f'{field} "{ref}" has no file in wallpapers/')
        if ref and len(list((B.THEME / 'wallpapers').glob(f'{ref}.*'))) > 1:
            problems.append(f'{field} "{ref}" matches more than one file')
    for f in (B.THEME / 'sounds').glob('*'):
        if f.stem not in SOUNDS:
            problems.append(f'sounds/{f.name} is not a Cocoon sound name')
    for d in (B.THEME / 'smart_folders').iterdir():
        if d.name not in FOLDERS:
            problems.append(f'smart_folders/{d.name} is not a Cocoon smart-folder key')
        for part in ('icon', 'hero', 'logo'):
            if not (d / f'{part}.png').exists():
                problems.append(f'smart_folders/{d.name}/{part}.png is missing')
    if not (B.THEME / 'preview.png').exists():
        problems.append('preview.png is missing')
    return theme, problems


if __name__ == '__main__':
    theme, problems = check()
    if problems:
        sys.exit('\n'.join(problems))
    out = B.ROOT / 'dist' / 'astralabs-cocoon.zip'
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(B.THEME.rglob('*')):
            if f.is_file():
                z.write(f, 'themes/astralabs/' + f.relative_to(B.THEME).as_posix())
    print(f'{theme["name"]} {theme["version"]}: {out.relative_to(B.ROOT)} ({out.stat().st_size / 1e6:.1f} MB)')
