#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path.cwd()
ACTIVITY = '\n        <activity android:name="com.crossdarkrix.dsre_realtime.D2AudioEffectControlPanelActivity" android:exported="true" android:launchMode="singleTop" android:theme="@android:style/Theme.Material.Light.NoActionBar">\n            <intent-filter>\n                <action android:name="android.media.action.DISPLAY_AUDIO_EFFECT_CONTROL_PANEL" />\n                <category android:name="android.intent.category.DEFAULT" />\n            </intent-filter>\n        </activity>\n'
PERMISSION = '<uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />'

def patch_manifest(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    changed = False
    if 'android.permission.MODIFY_AUDIO_SETTINGS' not in text:
        idx = text.find('<application')
        if idx >= 0:
            text = text[:idx] + '    ' + PERMISSION + '\n' + text[idx:]
            changed = True
    if 'D2AudioEffectControlPanelActivity' not in text:
        idx = text.rfind('</application>')
        if idx >= 0:
            text = text[:idx] + ACTIVITY + text[idx:]
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
            print('D2 dedicated activity manifest patch failed', p, exc)
    print('D2 dedicated activity manifest patched:', patched)

if __name__ == '__main__':
    main()
