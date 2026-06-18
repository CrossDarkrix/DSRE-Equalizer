from pathlib import Path
DIST_NAME = "dsre_realtime"
manifest_candidates = list(Path(".buildozer").glob(f"android/platform/build-*/dists/{DIST_NAME}/src/main/AndroidManifest.xml"))
if not manifest_candidates:
    raise FileNotFoundError("AndroidManifest.xml が見つかりませんでした。")
manifest = manifest_candidates[0]
text = manifest.read_text(encoding="utf-8")
old = "org.kivy.android.PythonActivity"
new = "com.crossdarkrix.dsre_realtime.DSREPythonActivity"
if old not in text and new in text:
    print(f"already patched: {manifest}")
elif old not in text:
    print(f"{old} が見つかりませんでした。Manifestを確認してください: {manifest}")
else:
    text = text.replace(old, new)
    manifest.write_text(text, encoding="utf-8")
    print(f"patched: {manifest}")
    print(f"{old} -> {new}")
