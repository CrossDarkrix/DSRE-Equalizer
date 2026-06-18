#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path.cwd()
DISPLAY_FILTER = '\n            <intent-filter>\n                <action android:name="android.media.action.DISPLAY_AUDIO_EFFECT_CONTROL_PANEL" />\n                <category android:name="android.intent.category.DEFAULT" />\n            </intent-filter>\n'

def patch_manifest(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    if 'android.media.action.DISPLAY_AUDIO_EFFECT_CONTROL_PANEL' in text:
        return False
    # Prefer PythonActivity / main launcher activity. Insert before first </activity>.
    idx = text.find('</activity>')
    if idx < 0:
        return False
    text = text[:idx] + DISPLAY_FILTER + text[idx:]
    path.write_text(text, encoding='utf-8')
    return True

def main():
    candidates = []
    candidates.extend(ROOT.glob('.buildozer/android/platform/build-*/dists/*/src/main/AndroidManifest.xml'))
    candidates.extend(ROOT.glob('.buildozer/android/platform/build-*/dists/*/AndroidManifest.xml'))
    candidates.extend(ROOT.glob('**/AndroidManifest.xml'))
    seen = set()
    patched = []
    for p in candidates:
        rp = str(p.resolve())
        if rp in seen:
            continue
        seen.add(rp)
        try:
            if patch_manifest(p):
                patched.append(str(p))
        except Exception as exc:
            print('D2 control panel manifest patch failed', p, exc)
    print('D2 control panel manifest patched:', patched)

if __name__ == '__main__':
    main()
