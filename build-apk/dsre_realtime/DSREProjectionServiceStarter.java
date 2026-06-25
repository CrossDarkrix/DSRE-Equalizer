package com.crossdarkrix.dsre_realtime;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.util.Log;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.util.Locale;

public final class DSREProjectionServiceStarter {
    private static final String TAG = "DSREProjectionStarter";
    private static final String CONFIG_FILE_NAME = "mini_dsre_config.json";
    public static final int REQUEST_MEDIA_PROJECTION = 43001;
    private static volatile boolean projectionResultKnown = false;
    private static volatile int lastProjectionResultCode = 0;
    private static volatile boolean lastProjectionDataNull = true;
    private DSREProjectionServiceStarter() {}
    public static void writeExternalLog(Context ctx, String msg) { try { Log.d(TAG, String.valueOf(msg)); } catch (Throwable ignored) {} }
    public static void clearExternalLog(Context ctx) {}
    public static void resetProjectionResult() { projectionResultKnown = false; lastProjectionResultCode = 0; lastProjectionDataNull = true; }
    public static void markProjectionResult(int resultCode, Intent resultData) { lastProjectionResultCode = resultCode; lastProjectionDataNull = (resultData == null); projectionResultKnown = true; }
    public static boolean hasProjectionResult() { return projectionResultKnown; }
    public static int getLastProjectionResultCode() { return lastProjectionResultCode; }
    public static boolean wasLastProjectionDataNull() { return lastProjectionDataNull; }
    public static void requestProjection(Activity activity) {
        if (activity == null) throw new IllegalArgumentException("activity is null");
        resetProjectionResult();
        MediaProjectionManager manager = (MediaProjectionManager) activity.getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        if (manager == null) throw new IllegalStateException("MediaProjectionManager is null");
        Intent intent = manager.createScreenCaptureIntent();
        activity.startActivityForResult(intent, REQUEST_MEDIA_PROJECTION);
    }
    public static void startPlainServiceForDebug(Context ctx, String pythonServiceArgument) { startIntent(ctx, buildBaseIntent(ctx, pythonServiceArgument), "plain"); }
    public static void startProjectionService(Context ctx, int resultCode, Intent resultData, String pythonServiceArgument) {
        if (ctx == null) throw new IllegalArgumentException("ctx is null");
        if (resultData == null) throw new IllegalArgumentException("resultData is null");
        Intent intent = buildBaseIntent(ctx, pythonServiceArgument);
        intent.putExtra(DSREPythonService.EXTRA_RESULT_CODE, resultCode);
        intent.putExtra(DSREPythonService.EXTRA_RESULT_DATA, resultData);
        startIntent(ctx, intent, "projection");
    }
    public static void stopProjectionService(Context ctx) {
        try { DSREAudioCaptureEngine.stopCapture(); } catch (Throwable ignored) {}
        try { ctx.stopService(new Intent(ctx, ServiceAudioenhanceservice.class)); } catch (Throwable t) { Log.e(TAG, "stopProjectionService failed", t); }
    }
    private static void startIntent(Context ctx, Intent intent, String mode) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) ctx.startForegroundService(intent); else ctx.startService(intent);
    }
    private static Intent buildBaseIntent(Context ctx, String pythonServiceArgument) {
        String filesDir = ctx.getFilesDir().getAbsolutePath();
        String appRoot = filesDir + "/app";
        String status = buildStatusText(ctx);
        Intent intent = new Intent(ctx, ServiceAudioenhanceservice.class);
        intent.putExtra("androidPrivate", filesDir);
        intent.putExtra("androidArgument", appRoot);
        intent.putExtra("serviceEntrypoint", "services/audio_capture_service.py");
        intent.putExtra("pythonName", "AudioEnhanceService");
        intent.putExtra("serviceTitle", "DSRE-Equalizer 動作中");
        intent.putExtra("serviceDescription", status);
        intent.putExtra("pythonHome", appRoot);
        intent.putExtra("pythonPath", appRoot + ":" + appRoot + "/lib");
        intent.putExtra("pythonServiceArgument", pythonServiceArgument == null ? "" : pythonServiceArgument);
        intent.putExtra("serviceStartAsForeground", "true");
        return intent;
    }
    private static String buildStatusText(Context ctx) {
        DsreConfig cfg = readConfig(ctx);
        return String.format(Locale.US, "mode=%d / gain=%.2f / assist=%.2f / air=%.2f / hp=%.3f", cfg.mode, cfg.gain, cfg.assistGain, cfg.airMix, cfg.airHpAlpha);
    }
    private static DsreConfig readConfig(Context ctx) {
        DsreConfig cfg = new DsreConfig();
        try {
            File dir = ctx.getExternalFilesDir(null); if (dir == null) dir = ctx.getFilesDir(); if (dir == null) return cfg;
            File file = new File(dir, CONFIG_FILE_NAME); if (!file.exists()) return cfg;
            JSONObject obj = new JSONObject(readAllText(file));
            cfg.mode = obj.optInt("mode", cfg.mode);
            cfg.gain = (float) obj.optDouble("gain", cfg.gain);
            cfg.assistGain = (float) obj.optDouble("assistGain", cfg.assistGain);
            cfg.airMix = (float) obj.optDouble("airMix", cfg.airMix);
            cfg.airHpAlpha = (float) obj.optDouble("airHpAlpha", cfg.airHpAlpha);
        } catch (Throwable ignored) {}
        return cfg;
    }
    private static String readAllText(File file) throws Exception {
        FileInputStream input = new FileInputStream(file);
        try { ByteArrayOutputStream output = new ByteArrayOutputStream(); byte[] buffer = new byte[4096]; int read; while ((read = input.read(buffer)) >= 0) output.write(buffer, 0, read); return output.toString("UTF-8"); }
        finally { try { input.close(); } catch (Throwable ignored) {} }
    }
    private static final class DsreConfig { int mode = 8; float gain = 0.30f; float assistGain = 0.25f; float airMix = 0.80f; float airHpAlpha = 0.08f; }
}
