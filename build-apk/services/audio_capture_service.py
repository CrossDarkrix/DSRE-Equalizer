# -*- coding: utf-8 -*-
import os
import json
import sys
import time
import traceback
from datetime import datetime

TAG = "DSREAudioCapturePyService"
LOG_FILE_NAME = "dsre_audio_capture_service.log"
FILE_LOG_ENABLED = False
CONFIG_FILE_NAME = "mini_dsre_config.json"
SESSION_ID = f"{os.getpid()}-{int(time.time())}"
VERSION = "v0.9.2-clean-ui"
DEFAULT_GAIN = 0.30
# 0=GAIN_ONLY, 1=SOFT_CLIP, 2=COMPRESSOR, 3=SATURATION, 4=COMPRESSOR+SATURATION, 5=COMPRESSOR_DIAGNOSTIC, 6=MINI_DSRE
PROCESS_MODE = 8
MINI_THRESHOLD = 0.14
MINI_RATIO = 2.20
MINI_MAKEUP = 1.05
MINI_SAT_DRIVE = 1.22
MINI_SAT_MIX = 0.16
MINI_OUTPUT_GAIN = 1.00
MINI_ASSIST_GAIN = 0.25
MINI_AIR_MIX = 0.80
MINI_AIR_HP_ALPHA = 0.08
# 0=GAIN_ONLY, 1=SOFT_CLIP, 2=COMPRESSOR, 3=SATURATION, 4=COMPRESSOR+SATURATION, 5=COMPRESSOR_DIAGNOSTIC, 6=MINI_DSRE
PROCESS_MODE = 8
MINI_THRESHOLD = 0.14
MINI_RATIO = 2.20
MINI_MAKEUP = 1.05
MINI_SAT_DRIVE = 1.22
MINI_SAT_MIX = 0.16
MINI_OUTPUT_GAIN = 1.00
# 0=GAIN_ONLY, 1=SOFT_CLIP, 2=COMPRESSOR, 3=SATURATION, 4=COMPRESSOR+SATURATION, 5=COMPRESSOR_DIAGNOSTIC, 6=MINI_DSRE
PROCESS_MODE = 8
MINI_THRESHOLD = 0.14
MINI_RATIO = 2.20
MINI_MAKEUP = 1.05
MINI_SAT_DRIVE = 1.22
MINI_SAT_MIX = 0.16
MINI_OUTPUT_GAIN = 1.00


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def get_android_service():
    if sys.platform != "android":
        return None
    try:
        from jnius import autoclass
        PythonService = autoclass("org.kivy.android.PythonService")
        return PythonService.mService
    except Exception:
        return None


def get_log_directory() -> str:
    service = get_android_service()
    if service is not None:
        try:
            external_dir = service.getExternalFilesDir(None)
            if external_dir is not None:
                path = external_dir.getAbsolutePath()
                os.makedirs(path, exist_ok=True)
                return path
        except Exception:
            pass
        try:
            internal_dir = service.getFilesDir()
            if internal_dir is not None:
                path = internal_dir.getAbsolutePath()
                os.makedirs(path, exist_ok=True)
                return path
        except Exception:
            pass
    for path in ("/sdcard/Download", "/storage/emulated/0/Download", os.getcwd()):
        try:
            os.makedirs(path, exist_ok=True)
            return path
        except Exception:
            pass
    return os.getcwd()


def get_log_path() -> str:
    return os.path.join(get_log_directory(), LOG_FILE_NAME)


def file_log(message: str) -> None:
    """line = f"{now_text()} [{TAG}] {message}\n"
    try:
        with open(get_log_path(), "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
    except Exception:
        try:
            with open(LOG_FILE_NAME, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
        except Exception:
            pass"""
    pass


def android_log(message: str) -> None:
    message = str(message)
    file_log(message)
    try:
        print(f"[{TAG}] {message}", flush=True)
    except Exception:
        pass
    if sys.platform == "android":
        try:
            from jnius import autoclass
            Log = autoclass("android.util.Log")
            Log.d(TAG, message)
        except Exception as exc:
            file_log(f"android.util.Log failed: {exc}")


def read_projection_state():
    if sys.platform != "android":
        android_log("projection_state not_android")
        return False
    try:
        from jnius import autoclass
        DSREPythonService = autoclass("com.crossdarkrix.dsre_realtime.DSREPythonService")
        has_data = bool(DSREPythonService.hasProjectionData())
        result_code = int(DSREPythonService.getProjectionResultCode())
        data_is_null = bool(DSREPythonService.isProjectionResultDataNull())
        start_calls = int(DSREPythonService.getProjectionStartCalls())
        last_stage = str(DSREPythonService.getLastStage() or "")
        android_log(
            "projection_state "
            f"hasProjectionData={has_data} "
            f"resultCode={result_code} "
            f"data_is_null={data_is_null} "
            f"startCalls={start_calls} "
            f"stage={last_stage}"
        )
        return has_data and not data_is_null
    except Exception as exc:
        android_log(f"read_projection_state failed: {exc}")
        android_log(traceback.format_exc())
        return False



def load_mini_dsre_config():
    config = {
        "gain": DEFAULT_GAIN, "mode": PROCESS_MODE,
        "threshold": MINI_THRESHOLD, "ratio": MINI_RATIO, "makeup": MINI_MAKEUP,
        "satDrive": MINI_SAT_DRIVE, "satMix": MINI_SAT_MIX, "outputGain": MINI_OUTPUT_GAIN,
        "assistGain": MINI_ASSIST_GAIN, "airMix": MINI_AIR_MIX, "airHpAlpha": MINI_AIR_HP_ALPHA,
    }
    try:
        path = os.path.join(get_log_directory(), CONFIG_FILE_NAME)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f: loaded = json.load(f)
            if isinstance(loaded, dict): config.update(loaded)
            android_log(f"mini_dsre_config loaded path={path} values={config}")
        else:
            android_log(f"mini_dsre_config not found; using defaults path={path}")
    except Exception as exc:
        android_log(f"mini_dsre_config load failed: {exc}")
    return config

def start_audio_capture_if_possible():
    if sys.platform != "android":
        android_log("audio_capture_start skipped: not android")
        return
    try:
        from jnius import autoclass
        DSREAudioCaptureEngine = autoclass("com.crossdarkrix.dsre_realtime.DSREAudioCaptureEngine")
        if bool(DSREAudioCaptureEngine.isRunning()):
            android_log("audio_capture_engine already running")
            return
        cfg = load_mini_dsre_config()
        android_log(f"audio_capture_engine configureMiniDsre threshold={cfg['threshold']} ratio={cfg['ratio']} makeup={cfg['makeup']} satDrive={cfg['satDrive']} satMix={cfg['satMix']} outputGain={cfg['outputGain']}")
        DSREAudioCaptureEngine.configureMiniDsre(float(cfg["threshold"]), float(cfg["ratio"]), float(cfg["makeup"]), float(cfg["satDrive"]), float(cfg["satMix"]), float(cfg["outputGain"]))
        android_log(f"audio_capture_engine configureMiniDsreAssist assistGain={cfg['assistGain']} airMix={cfg['airMix']} airHpAlpha={cfg['airHpAlpha']}")
        DSREAudioCaptureEngine.configureMiniDsreAssist(float(cfg["assistGain"]), float(cfg["airMix"]), float(cfg["airHpAlpha"]))
        android_log(f"audio_capture_engine startStablePassthroughFromStoredProjection requested gain={cfg['gain']} mode={cfg['mode']}")
        DSREAudioCaptureEngine.startStablePassthroughFromStoredProjection(48000, 2, float(cfg["gain"]), int(cfg["mode"]))
        android_log("audio_capture_engine startStablePassthroughFromStoredProjection returned")
    except Exception as exc:
        android_log(f"audio_capture_engine start failed: {exc}")
        android_log(traceback.format_exc())


def log_audio_engine_state():
    if sys.platform != "android":
        return
    try:
        from jnius import autoclass
        DSREAudioCaptureEngine = autoclass("com.crossdarkrix.dsre_realtime.DSREAudioCaptureEngine")
        android_log(
            "audio_engine_state "
            f"running={bool(DSREAudioCaptureEngine.isRunning())} "
            f"frames={int(DSREAudioCaptureEngine.getFramesRead())} "
            f"rms={float(DSREAudioCaptureEngine.getLastRms()):.6f} "
            f"outRms={float(DSREAudioCaptureEngine.getLastOutRms()):.6f} "
            f"readCalls={int(DSREAudioCaptureEngine.getReadCalls())} "
            f"writeCalls={int(DSREAudioCaptureEngine.getWriteCalls())} "
            f"zeroWrites={int(DSREAudioCaptureEngine.getWriteZeroCount())} "
            f"shortWrites={int(DSREAudioCaptureEngine.getShortWriteCount())} "
            f"errorCount={int(DSREAudioCaptureEngine.getErrorCount())} "
            f"mode={int(DSREAudioCaptureEngine.getProcessMode())} "
            f"processorPeak={float(DSREAudioCaptureEngine.getLastProcessorPeak()):.6f} "
            f"gainReduction={float(DSREAudioCaptureEngine.getLastGainReduction()):.6f} "
            f"compressorActive={int(DSREAudioCaptureEngine.getLastCompressorActiveSamples())} "
            f"miniThreshold={float(DSREAudioCaptureEngine.getMiniThreshold()):.3f} "
            f"miniRatio={float(DSREAudioCaptureEngine.getMiniRatio()):.3f} "
            f"assistGain={float(DSREAudioCaptureEngine.getMiniAssistGain()):.3f} "
            f"wetRms={float(DSREAudioCaptureEngine.getLastWetRms()):.6f} "
            f"assistRms={float(DSREAudioCaptureEngine.getLastAssistRms()):.6f} "
            f"satDrive={float(DSREAudioCaptureEngine.getMiniSaturationDrive()):.3f} "
            f"satMix={float(DSREAudioCaptureEngine.getMiniSaturationMix()):.3f} "
            f"session={int(DSREAudioCaptureEngine.getSessionId())} "
            f"lastRead={int(DSREAudioCaptureEngine.getLastRead())} "
            f"lastWrite={int(DSREAudioCaptureEngine.getLastWrite())} "
            f"gain={float(DSREAudioCaptureEngine.getGain()):.3f} "
            f"error={str(DSREAudioCaptureEngine.getLastError() or '')} "
            f"stage={str(DSREAudioCaptureEngine.getStage() or '')}"
        )
    except Exception as exc:
        android_log(f"audio_engine_state failed: {exc}")


def describe_environment() -> None:
    android_log(f"service script started version={VERSION} session={SESSION_ID}")
    android_log(f"sys.platform={sys.platform}")
    android_log(f"pid={os.getpid()}")
    android_log(f"cwd={os.getcwd()}")
    android_log(f"argv={sys.argv}")
    android_log(f"log_path={get_log_path()}")
    service = get_android_service()
    android_log(f"PythonService.mService is None: {service is None}")
    if service is not None:
        try:
            android_log(f"package={service.getPackageName()}")
        except Exception as exc:
            android_log(f"getPackageName failed: {exc}")
    if read_projection_state():
        start_audio_capture_if_possible()
    log_audio_engine_state()


def main() -> None:
    describe_environment()
    tick = 0
    try:
        os.remove(os.path.join(get_log_directory(), "dsre_java_bridge.log"))
    except:
        pass
    while True:     
        tick += 1
        if tick == 1 or tick % 5 == 0:
            android_log(f"heartbeat version={VERSION} session={SESSION_ID} tick={tick}")
            has_projection = read_projection_state()
            if has_projection:
                start_audio_capture_if_possible()
            log_audio_engine_state()
        time.sleep(1.0)

if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        file_log("service crashed")
        file_log("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
        while True:
            time.sleep(5.0)
            file_log("crashed fallback loop")
