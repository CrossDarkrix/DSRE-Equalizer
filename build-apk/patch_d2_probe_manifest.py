#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path.cwd()
RECEIVER = '\n        <receiver android:name="com.crossdarkrix.dsre_realtime.DSREAudioSessionReceiver" android:enabled="true" android:exported="true">\n            <intent-filter>\n                <action android:name="android.media.action.OPEN_AUDIO_EFFECT_CONTROL_SESSION" />\n                <action android:name="android.media.action.CLOSE_AUDIO_EFFECT_CONTROL_SESSION" />\n            </intent-filter>\n        </receiver>\n'
PERMISSION = '<uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />'

def patch_manifest(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    changed = False
    if 'android.permission.MODIFY_AUDIO_SETTINGS' not in text:
        idx = text.find('<application')
        if idx >= 0:
            text = text[:idx] + '    ' + PERMISSION + '\n' + text[idx:]
            changed = True
    if 'DSREAudioSessionReceiver' not in text:
        idx = text.rfind('</application>')
        if idx >= 0:
            text = text[:idx] + RECEIVER + text[idx:]
            changed = True
    if changed:
        path.write_text(text, encoding='utf-8')
    return changed

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
            print('D2 manifest patch failed', p, exc)
    print('D2 manifest patched:', patched)

if __name__ == '__main__':
    main()
