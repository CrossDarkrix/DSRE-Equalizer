package com.crossdarkrix.dsre_realtime;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.util.Log;

import org.json.JSONObject;
import org.kivy.android.PythonService;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.util.Locale;

public class DSREPythonService extends PythonService {
    private static final String TAG = "DSREPythonService";
    private static final String CONFIG_FILE_NAME = "mini_dsre_config.json";
    private static final int NOTIFICATION_ID = 43002;
    private static final String CHANNEL_ID = "dsre_equalizer_processing";
    private static final String CHANNEL_NAME = "DSRE-Equalizer processing";
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
    public static void writeExternalLog(Context ctx, String msg) { try { Log.d(TAG, String.valueOf(msg)); } catch (Throwable ignored) {} }
    @Override public void onCreate() { lastStage = "DSREPythonService.onCreate"; super.onCreate(); }
    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        projectionStartCalls += 1;
        lastStage = "DSREPythonService.onStartCommand";
        try {
            if (intent != null) {
                projectionResultCode = intent.getIntExtra(EXTRA_RESULT_CODE, -1);
                projectionResultData = intent.getParcelableExtra(EXTRA_RESULT_DATA);
                lastStage = "projection extras captured: resultCode=" + projectionResultCode + " dataNull=" + (projectionResultData == null);
            }
        } catch (Throwable t) { lastStage = "projection extras capture failed: " + t.getClass().getSimpleName() + ": " + String.valueOf(t.getMessage()); Log.e(TAG, lastStage, t); }
        int result = super.onStartCommand(intent, flags, startId);
        try { startDsreForegroundNotification(); updateDsreForegroundNotification(this); } catch (Throwable t) { Log.e(TAG, "startDsreForegroundNotification failed", t); }
        return result;
    }
    @Override public void onDestroy() { lastStage = "DSREPythonService.onDestroy"; try { DSREAudioCaptureEngine.stopCapture(); } catch (Throwable ignored) {} super.onDestroy(); }
    private void startDsreForegroundNotification() { Notification notification = buildDsreNotification(this); if (Build.VERSION.SDK_INT >= 29) startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION); else startForeground(NOTIFICATION_ID, notification); }
    public static void updateDsreForegroundNotification(Context ctx) { if (ctx == null) return; try { ensureNotificationChannel(ctx); NotificationManager manager = (NotificationManager) ctx.getSystemService(Context.NOTIFICATION_SERVICE); if (manager != null) manager.notify(NOTIFICATION_ID, buildDsreNotification(ctx)); } catch (Throwable t) { try { Log.e(TAG, "updateDsreForegroundNotification failed", t); } catch (Throwable ignored) {} } }
    private static Notification buildDsreNotification(Context ctx) {
        ensureNotificationChannel(ctx); DsreConfig cfg = readConfig(ctx);
        String compact = String.format(Locale.US, "mode=%d / gain=%.2f / assist=%.2f / air=%.2f / hp=%.3f", cfg.mode, cfg.gain, cfg.assistGain, cfg.airMix, cfg.airHpAlpha);
        String title = "DSRE-Equalizer 動作中";
        String bigText = "DSRE-Equalizer は端末内でリアルタイム音声補助処理を実行中です。\n音声データは外部サーバーへ送信されません。\n" + compact;
        int icon = getSmallIcon(ctx); Intent openIntent = new Intent(ctx, DSREPythonActivity.class); openIntent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        int pFlags = PendingIntent.FLAG_UPDATE_CURRENT; if (Build.VERSION.SDK_INT >= 23) pFlags |= PendingIntent.FLAG_IMMUTABLE;
        PendingIntent pendingIntent = PendingIntent.getActivity(ctx, 43002, openIntent, pFlags);
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(ctx, CHANNEL_ID) : new Notification.Builder(ctx);
        builder.setContentTitle(title).setContentText(compact).setStyle(new Notification.BigTextStyle().bigText(bigText)).setSmallIcon(icon).setContentIntent(pendingIntent).setOngoing(true).setOnlyAlertOnce(true).setShowWhen(false);
        if (Build.VERSION.SDK_INT >= 21) builder.setCategory(Notification.CATEGORY_SERVICE).setVisibility(Notification.VISIBILITY_PUBLIC);
        return builder.build();
    }
    private static void ensureNotificationChannel(Context ctx) { if (ctx == null || Build.VERSION.SDK_INT < 26) return; NotificationManager manager = (NotificationManager) ctx.getSystemService(Context.NOTIFICATION_SERVICE); if (manager == null) return; NotificationChannel channel = new NotificationChannel(CHANNEL_ID, CHANNEL_NAME, NotificationManager.IMPORTANCE_LOW); channel.setDescription("Shows DSRE-Equalizer realtime audio assist processing status."); channel.setShowBadge(false); manager.createNotificationChannel(channel); }
    private static int getSmallIcon(Context ctx) { try { ApplicationInfo info = ctx.getApplicationInfo(); if (info != null && info.icon != 0) return info.icon; } catch (Throwable ignored) {} return android.R.drawable.ic_media_play; }
    private static DsreConfig readConfig(Context ctx) { DsreConfig cfg = new DsreConfig(); try { File dir = ctx.getExternalFilesDir(null); if (dir == null) dir = ctx.getFilesDir(); if (dir == null) return cfg; File file = new File(dir, CONFIG_FILE_NAME); if (!file.exists()) return cfg; JSONObject obj = new JSONObject(readAllText(file)); cfg.mode = obj.optInt("mode", cfg.mode); cfg.gain = (float) obj.optDouble("gain", cfg.gain); cfg.assistGain = (float) obj.optDouble("assistGain", cfg.assistGain); cfg.airMix = (float) obj.optDouble("airMix", cfg.airMix); cfg.airHpAlpha = (float) obj.optDouble("airHpAlpha", cfg.airHpAlpha); } catch (Throwable ignored) {} return cfg; }
    private static String readAllText(File file) throws Exception { FileInputStream input = new FileInputStream(file); try { ByteArrayOutputStream output = new ByteArrayOutputStream(); byte[] buffer = new byte[4096]; int read; while ((read = input.read(buffer)) >= 0) output.write(buffer, 0, read); return output.toString("UTF-8"); } finally { try { input.close(); } catch (Throwable ignored) {} } }
    private static final class DsreConfig { int mode = 8; float gain = 0.30f; float assistGain = 0.25f; float airMix = 0.80f; float airHpAlpha = 0.08f; }
}
