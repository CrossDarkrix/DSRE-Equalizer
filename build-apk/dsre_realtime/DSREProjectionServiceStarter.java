package com.crossdarkrix.dsre_realtime;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.util.Log;

import java.io.File;
import java.io.FileWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public final class DSREProjectionServiceStarter {
    private static final String TAG = "DSREProjectionStarter";
    private static final String LOG_FILE_NAME = "dsre_java_bridge.log";
    public static final int REQUEST_MEDIA_PROJECTION = 43001;
    private DSREProjectionServiceStarter() {}
    public static void writeExternalLog(Context ctx, String msg) {
        try {
            File dir = null;
            if (ctx != null) {
                dir = ctx.getExternalFilesDir(null);
                if (dir == null) dir = ctx.getFilesDir();
            }
            if (dir == null) return;
            if (!dir.exists()) dir.mkdirs();
            File file = new File(dir, LOG_FILE_NAME);
            FileWriter fw = new FileWriter(file, true);
            String ts = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(new Date());
        } catch (Throwable ignored) {}
    }
    public static void clearExternalLog(Context ctx) {
        try {
            File dir = ctx.getExternalFilesDir(null);
            if (dir == null) dir = ctx.getFilesDir();
            if (dir == null) return;
            File file = new File(dir, LOG_FILE_NAME);
            if (file.exists()) file.delete();
        } catch (Throwable ignored) {}
    }
    public static void requestProjection(Activity activity) {
        if (activity == null) throw new IllegalArgumentException("activity is null");
        writeExternalLog(activity, "requestProjection called");
        writeExternalLog(activity, "requestProjection activityClass=" + activity.getClass().getName());
        MediaProjectionManager manager = (MediaProjectionManager) activity.getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        if (manager == null) {
            writeExternalLog(activity, "MediaProjectionManager is null");
            throw new IllegalStateException("MediaProjectionManager is null");
        }
        Intent intent = manager.createScreenCaptureIntent();
        writeExternalLog(activity, "createScreenCaptureIntent returned; calling Activity.startActivityForResult");
        activity.startActivityForResult(intent, REQUEST_MEDIA_PROJECTION);
        writeExternalLog(activity, "Activity.startActivityForResult returned");
    }
    public static void startPlainServiceForDebug(Context ctx, String pythonServiceArgument) {
        writeExternalLog(ctx, "startPlainServiceForDebug called");
        Intent intent = buildBaseIntent(ctx, pythonServiceArgument);
        startIntent(ctx, intent, "plain");
    }
    public static void startProjectionService(Context ctx, int resultCode, Intent resultData, String pythonServiceArgument) {
        writeExternalLog(ctx, "startProjectionService called resultCode=" + resultCode + " dataNull=" + (resultData == null));
        if (ctx == null) throw new IllegalArgumentException("ctx is null");
        if (resultData == null) throw new IllegalArgumentException("resultData is null");
        Intent intent = buildBaseIntent(ctx, pythonServiceArgument);
        intent.putExtra(DSREPythonService.EXTRA_RESULT_CODE, resultCode);
        intent.putExtra(DSREPythonService.EXTRA_RESULT_DATA, resultData);
        startIntent(ctx, intent, "projection");
    }
    public static void stopProjectionService(Context ctx) {
        writeExternalLog(ctx, "stopProjectionService called");
        try { DSREAudioCaptureEngine.stopCapture(); } catch (Throwable ignored) {}
        try {
            Intent intent = new Intent(ctx, ServicePyaudiocaptureservice.class);
            ctx.stopService(intent);
            writeExternalLog(ctx, "stopService returned");
        } catch (Throwable t) {
            writeExternalLog(ctx, "stopProjectionService failed: " + t.getClass().getSimpleName() + ": " + t.getMessage());
            Log.e(TAG, "stopProjectionService failed", t);
        }
    }
    private static void startIntent(Context ctx, Intent intent, String mode) {
        try {
            writeExternalLog(ctx, "startIntent mode=" + mode + " sdk=" + Build.VERSION.SDK_INT + " extras=" + String.valueOf(intent.getExtras()));
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) ctx.startForegroundService(intent);
            else ctx.startService(intent);
            writeExternalLog(ctx, "startIntent returned mode=" + mode);
        } catch (Throwable t) {
            writeExternalLog(ctx, "startIntent failed mode=" + mode + " " + t.getClass().getSimpleName() + ": " + t.getMessage());
            Log.e(TAG, "startIntent failed", t);
            throw t;
        }
    }
    private static Intent buildBaseIntent(Context ctx, String pythonServiceArgument) {
        String filesDir = ctx.getFilesDir().getAbsolutePath();
        String appRoot = filesDir + "/app";
        Intent intent = new Intent(ctx, ServicePyaudiocaptureservice.class);
        intent.putExtra("androidPrivate", filesDir);
        intent.putExtra("androidArgument", appRoot);
        intent.putExtra("serviceEntrypoint", "services/audio_capture_service.py");
        intent.putExtra("pythonName", "PyAudioCaptureService");
        intent.putExtra("serviceTitle", "dsre_realtime");
        intent.putExtra("serviceDescription", "Pyaudiocaptureservice");
        intent.putExtra("pythonHome", appRoot);
        intent.putExtra("pythonPath", appRoot + ":" + appRoot + "/lib");
        intent.putExtra("pythonServiceArgument", pythonServiceArgument == null ? "" : pythonServiceArgument);
        intent.putExtra("serviceStartAsForeground", "true");
        File pythonBin = new File(appRoot, ".bin/python");
        File entrypoint = new File(appRoot, "services/audio_capture_service.py");
        writeExternalLog(ctx, "buildBaseIntent filesDir=" + filesDir
                + " appRoot=" + appRoot
                + " pythonHome=" + appRoot
                + " pythonPath=" + appRoot + ":" + appRoot + "/lib"
                + " entrypoint=services/audio_capture_service.py"
                + " existsPythonBin=" + pythonBin.exists()
                + " existsEntrypoint=" + entrypoint.exists());
        return intent;
    }
}
