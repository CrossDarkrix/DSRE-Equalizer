#!/bin/sh
set -eu

# DSRE Realtime: Buildozer build -> patch AndroidManifest -> Gradle rebuild -> copy APK
# Run this from the project root where buildozer.spec and patch_activity_manifest.py exist.

WORK_PATH="$(pwd)"
DIST_NAME="dsre_realtime"
ARCH_DIR="build-arm64-v8a"
DIST_DIR="$WORK_PATH/.buildozer/android/platform/$ARCH_DIR/dists/$DIST_NAME"
OUT_DIR="$WORK_PATH/bin"

printf '%s\n' '[1/6] buildozer android debug'
buildozer android debug

printf '%s\n' '[2/6] patch AndroidManifest.xml'
python3.11 patch_activity_manifest.py
python3.11 patch_d2_probe_manifest.py
python3.11 patch_d2_control_panel_manifest.py
python3.11 patch_d2_dedicated_activity_manifest.py

if [ ! -d "$DIST_DIR" ]; then
    printf '%s\n' "ERROR: dist directory not found: $DIST_DIR" >&2
    printf '%s\n' 'Hint: ARCH_DIR may differ. Check .buildozer/android/platform/.' >&2
    exit 1
fi

printf '%s\n' '[3/6] verify patched Activity in AndroidManifest.xml'
MANIFEST="$DIST_DIR/src/main/AndroidManifest.xml"
if ! grep -q 'com.crossdarkrix.dsre_realtime.DSREPythonActivity' "$MANIFEST"; then
    printf '%s\n' 'ERROR: DSREPythonActivity not found in AndroidManifest.xml after patch.' >&2
    grep -n 'PythonActivity\|DSREPythonActivity' "$MANIFEST" || true
    exit 1
fi

grep -n 'PythonActivity\|DSREPythonActivity' "$MANIFEST" || true

printf '%s\n' '[4/6] Gradle assembleDebug'
cd "$DIST_DIR"
./gradlew assembleDebug

printf '%s\n' '[5/6] copy debug APK to project bin/'
mkdir -p "$OUT_DIR"
APK_PATH="$(find . -name '*debug*.apk' -print | head -n 1)"
if [ -z "$APK_PATH" ]; then
    printf '%s\n' 'ERROR: debug APK not found.' >&2
    exit 1
fi

cp -a "$APK_PATH" "$OUT_DIR/"
printf '%s\n' "Copied: $APK_PATH -> $OUT_DIR/"

printf '%s\n' '[6/6] done'
