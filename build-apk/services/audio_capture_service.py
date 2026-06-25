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
VERSION = "v1.0.7-notification-visible-lines"
DEFAULT_GAIN = 0.30
DEFAULT_QUALITY = 1
NOTIFICATION_ID = 1
NOTIFICATION_CHANNEL_ID = "dsre_runtime_status"
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


def safe_float_from_engine(callable_value, default=0.0):
    try:
        return float(callable_value())
    except Exception:
        return float(default)


def safe_int_from_engine(callable_value, default=0):
    try:
        return int(callable_value())
    except Exception:
        return int(default)


def quality_label(value: int) -> str:
    if value <= 0:
        return "Normal"
    if value == 1:
        return "HiFi"
    return "HiFi+"




def quality_short_label(value: int) -> str:
    if value <= 0:
        return "N"
    if value == 1:
        return "H"
    return "H+"


def format_load_rate_percent(avg_process_ms: float, process_ms: float = 0.0) -> str:
    """通知用の負荷率をパーセント文字列にする。

    Java側に専用の負荷率APIが無い場合でも、既存の平均処理時間から
    おおよそのDSP処理負荷を表示できるようにする。
    48kHz系の短いリアルタイム処理では10msを1処理予算として扱い、
    avgProcessMs / 10ms * 100 を目安値として表示する。
    """
    try:
        base_ms = float(avg_process_ms)
    except Exception:
        base_ms = 0.0
    if base_ms <= 0.0:
        try:
            base_ms = float(process_ms)
        except Exception:
            base_ms = 0.0
    load_percent = max(0.0, min(150.0, (base_ms / 10.0) * 100.0))
    return f"{load_percent:.1f}%"


def update_runtime_notification(DSREAudioCaptureEngine=None) -> None:
    if sys.platform != "android":
        return
    try:
        from jnius import autoclass
        if DSREAudioCaptureEngine is None:
            DSREAudioCaptureEngine = autoclass("com.crossdarkrix.dsre_realtime.DSREAudioCaptureEngine")
        PythonService = autoclass("org.kivy.android.PythonService")
        service = PythonService.mService
        if service is None:
            return

        BuildVersion = autoclass("android.os.Build$VERSION")
        Context = autoclass("android.content.Context")
        Notification = autoclass("android.app.Notification")
        NotificationBuilder = autoclass("android.app.Notification$Builder")

        quality = safe_int_from_engine(DSREAudioCaptureEngine.getQualityMode, DEFAULT_QUALITY)
        mode = safe_int_from_engine(DSREAudioCaptureEngine.getProcessMode, PROCESS_MODE)
        frames = safe_int_from_engine(DSREAudioCaptureEngine.getFramesRead, 0)
        process_ms = safe_float_from_engine(DSREAudioCaptureEngine.getLastProcessMs, 0.0)
        max_process_ms = safe_float_from_engine(DSREAudioCaptureEngine.getMaxProcessMs, 0.0)
        avg_process_ms = safe_float_from_engine(DSREAudioCaptureEngine.getAvgProcessMs, process_ms)
        recent_max_process_ms = safe_float_from_engine(DSREAudioCaptureEngine.getRecentMaxProcessMs, process_ms)
        spike_count = safe_int_from_engine(DSREAudioCaptureEngine.getSpikeCount, 0)
        recent_spike_count = safe_int_from_engine(DSREAudioCaptureEngine.getRecentSpikeCount, 0)
        zero_writes = safe_int_from_engine(DSREAudioCaptureEngine.getWriteZeroCount, 0)
        short_writes = safe_int_from_engine(DSREAudioCaptureEngine.getShortWriteCount, 0)
        errors = safe_int_from_engine(DSREAudioCaptureEngine.getErrorCount, 0)
        running = bool(DSREAudioCaptureEngine.isRunning())
        cfg_quality = DEFAULT_QUALITY
        try:
            cfg_quality = int(load_mini_dsre_config().get("quality", DEFAULT_QUALITY))
        except Exception:
            cfg_quality = quality
        quality_note = "" if cfg_quality == quality else f" / 設定: {quality_label(cfg_quality)}"
        load_rate_text = format_load_rate_percent(avg_process_ms, process_ms)

        line1 = "DSRE-Equalizerは動作中です。"
        separator = "------------------------------"
        line2 = f"クオリティ: {quality_label(quality)}{quality_note}  負荷率: {load_rate_text}"
        privacy_line = "※DSRE-Equalizerは\n音声データを外部に送信しません。"
        title = line1
        collapsed_text = f"\n{line2}"
        big_text = f"{line1}\n\n{separator}\n{line2}\n{separator}\n\n{privacy_line}"

        if BuildVersion.SDK_INT >= 26:
            NotificationChannel = autoclass("android.app.NotificationChannel")
            NotificationManager = autoclass("android.app.NotificationManager")
            manager = service.getSystemService(Context.NOTIFICATION_SERVICE)
            channel = NotificationChannel(
                NOTIFICATION_CHANNEL_ID,
                "DSRE runtime status",
                NotificationManager.IMPORTANCE_LOW,
            )
            channel.setDescription("DSRE realtime processing status")
            try:
                channel.setShowBadge(False)
            except Exception:
                pass
            manager.createNotificationChannel(channel)
            builder = NotificationBuilder(service, NOTIFICATION_CHANNEL_ID)
        else:
            manager = service.getSystemService(Context.NOTIFICATION_SERVICE)
            builder = NotificationBuilder(service)

        icon = service.getApplicationInfo().icon
        if icon:
            builder.setSmallIcon(icon)
        builder.setContentTitle(title)
        builder.setContentText(collapsed_text)
        try:
            style = Notification.BigTextStyle().bigText(big_text).setBigContentTitle(line1).setSummaryText(privacy_line)
            builder.setStyle(style)
        except Exception:
            pass
        builder.setOngoing(True)
        builder.setOnlyAlertOnce(True)
        builder.setShowWhen(False)

        notification = builder.build()
        # p4a/PythonService既定通知に戻る端末差を避けるため、notifyとstartForegroundの両方を試す。
        try:
            if manager is not None:
                manager.notify(NOTIFICATION_ID, notification)
        except Exception:
            pass
        try:
            service.startForeground(NOTIFICATION_ID, notification)
        except Exception:
            pass
    except Exception:
        # 通知更新は補助表示なので、失敗しても音声処理は止めない。
        pass

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
        "quality": DEFAULT_QUALITY,
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

def apply_config_to_engine(DSREAudioCaptureEngine, cfg) -> None:
    try:
        DSREAudioCaptureEngine.configureQuality(int(cfg.get("quality", DEFAULT_QUALITY)))
    except Exception:
        android_log("audio_capture_engine configureQuality unavailable; using engine default")
    android_log(
        f"audio_capture_engine apply_config "
        f"quality={cfg.get('quality', DEFAULT_QUALITY)} "
        f"threshold={cfg['threshold']} ratio={cfg['ratio']} makeup={cfg['makeup']} "
        f"satDrive={cfg['satDrive']} satMix={cfg['satMix']} outputGain={cfg['outputGain']} "
        f"assistGain={cfg['assistGain']} airMix={cfg['airMix']} airHpAlpha={cfg['airHpAlpha']}"
    )
    DSREAudioCaptureEngine.configureMiniDsre(
        float(cfg["threshold"]),
        float(cfg["ratio"]),
        float(cfg["makeup"]),
        float(cfg["satDrive"]),
        float(cfg["satMix"]),
        float(cfg["outputGain"]),
    )
    DSREAudioCaptureEngine.configureMiniDsreAssist(
        float(cfg["assistGain"]),
        float(cfg["airMix"]),
        float(cfg["airHpAlpha"]),
    )

def start_audio_capture_if_possible():
    if sys.platform != "android":
        android_log("audio_capture_start skipped: not android")
        return
    try:
        from jnius import autoclass
        DSREAudioCaptureEngine = autoclass("com.crossdarkrix.dsre_realtime.DSREAudioCaptureEngine")
        if bool(DSREAudioCaptureEngine.isRunning()):
            cfg = load_mini_dsre_config()
            apply_config_to_engine(DSREAudioCaptureEngine, cfg)
            update_runtime_notification(DSREAudioCaptureEngine)
            android_log("audio_capture_engine already running; config refreshed")
            return
        cfg = load_mini_dsre_config()
        apply_config_to_engine(DSREAudioCaptureEngine, cfg)
        android_log(f"audio_capture_engine startStablePassthroughFromStoredProjection requested gain={cfg['gain']} mode={cfg['mode']} quality={cfg.get('quality', DEFAULT_QUALITY)}")
        DSREAudioCaptureEngine.startStablePassthroughFromStoredProjection(48000, 2, float(cfg["gain"]), int(cfg["mode"]))
        update_runtime_notification(DSREAudioCaptureEngine)
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
            f"qualityMode={int(DSREAudioCaptureEngine.getQualityMode())} "
            f"processMs={float(DSREAudioCaptureEngine.getLastProcessMs()):.3f} "
            f"maxProcessMs={float(DSREAudioCaptureEngine.getMaxProcessMs()):.3f} "
            f"avgProcessMs={float(DSREAudioCaptureEngine.getAvgProcessMs()):.3f} "
            f"recentMaxProcessMs={float(DSREAudioCaptureEngine.getRecentMaxProcessMs()):.3f} "
            f"spikeCount={int(DSREAudioCaptureEngine.getSpikeCount())} "
            f"recentSpikeCount={int(DSREAudioCaptureEngine.getRecentSpikeCount())} "
            f"processCalls={int(DSREAudioCaptureEngine.getProcessCalls())} "
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
        update_runtime_notification(DSREAudioCaptureEngine)
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
