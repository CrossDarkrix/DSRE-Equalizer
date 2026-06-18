package com.crossdarkrix.dsre_realtime;

import android.content.Context;
import android.content.Intent;
import android.util.Log;

import org.kivy.android.PythonService;

import java.io.File;
import java.io.FileWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class DSREPythonService extends PythonService {
    private static final String TAG = "DSREPythonService";
    private static final String LOG_FILE_NAME = "dsre_java_bridge.log";
    public static final String EXTRA_RESULT_CODE = "com.crossdarkrix.dsre_realtime.EXTRA_RESULT_CODE";
    public static final String EXTRA_RESULT_DATA = "com.crossdarkrix.dsre_realtime.EXTRA_RESULT_DATA";
    private static volatile int projectionResultCode = -1;
    private static volatile Intent projectionResultData = null;
    private static volatile int projectionStartCalls = 0;
    private static volatile String lastStage = "idle";
    public static boolean hasProjectionData() { return projectionResultData != null; }
    public static int getProjectionResultCode() { return projectionResultCode; }
    public static boolean isProjectionResultDataNull() { return projectionResultData == null; }
    public static Intent getProjectionResultData() { return projectionResultData; }
    public static int getProjectionStartCalls() { return projectionStartCalls; }
    public static String getLastStage() { return lastStage; }
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
            fw.write(ts + " [" + TAG + "] " + String.valueOf(msg) + "\n");
            fw.flush();
            fw.close();
        } catch (Throwable ignored) {}
    }
    @Override
    public void onCreate() {
        lastStage = "DSREPythonService.onCreate";
        Log.d(TAG, lastStage);
        writeExternalLog(this, lastStage);
        super.onCreate();
    }
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        projectionStartCalls += 1;
        lastStage = "DSREPythonService.onStartCommand";
        writeExternalLog(this, lastStage + " flags=" + flags + " startId=" + startId + " intentNull=" + (intent == null));
        try {
            if (intent != null) {
                projectionResultCode = intent.getIntExtra(EXTRA_RESULT_CODE, -1);
                projectionResultData = intent.getParcelableExtra(EXTRA_RESULT_DATA);
                lastStage = "projection extras captured: resultCode=" + projectionResultCode
                        + " dataNull=" + (projectionResultData == null)
                        + " extras=" + String.valueOf(intent.getExtras());
                Log.d(TAG, lastStage);
                writeExternalLog(this, lastStage);
            }
        } catch (Throwable t) {
            lastStage = "projection extras capture failed: " + t.getClass().getSimpleName() + ": " + String.valueOf(t.getMessage());
            Log.e(TAG, lastStage, t);
            writeExternalLog(this, lastStage);
        }
        return super.onStartCommand(intent, flags, startId);
    }
    @Override
    public void onDestroy() {
        lastStage = "DSREPythonService.onDestroy";
        Log.d(TAG, lastStage);
        writeExternalLog(this, lastStage);
        try { DSREAudioCaptureEngine.stopCapture(); } catch (Throwable ignored) {}
        super.onDestroy();
    }
}
