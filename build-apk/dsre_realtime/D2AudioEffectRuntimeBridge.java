package com.crossdarkrix.dsre_realtime;

import android.content.Context;
import android.content.IntentFilter;
import android.media.audiofx.AudioEffect;
import android.os.Build;

public final class D2AudioEffectRuntimeBridge {
    private static DSREAudioSessionReceiver runtimeReceiver = null;
    private static boolean registered = false;

    private D2AudioEffectRuntimeBridge() {}

    public static synchronized void initialize(Context context) {
        if (context == null) return;
        Context app = context.getApplicationContext();
        D2AudioEffectProbe.writeLog(app, "D2 runtime bridge initialize called sdk=" + Build.VERSION.SDK_INT + " registered=" + registered);
        D2AudioEffectProbe.selfTest(app);
        if (registered) return;
        try {
            runtimeReceiver = new DSREAudioSessionReceiver();
            IntentFilter filter = new IntentFilter();
            filter.addAction(AudioEffect.ACTION_OPEN_AUDIO_EFFECT_CONTROL_SESSION);
            filter.addAction(AudioEffect.ACTION_CLOSE_AUDIO_EFFECT_CONTROL_SESSION);
            if (Build.VERSION.SDK_INT >= 33) {
                app.registerReceiver(runtimeReceiver, filter, Context.RECEIVER_EXPORTED);
            } else {
                app.registerReceiver(runtimeReceiver, filter);
            }
            registered = true;
            D2AudioEffectProbe.writeLog(app, "D2 runtime receiver registered dynamically actions=" + filter.countActions());
        } catch (Throwable t) {
            D2AudioEffectProbe.writeLog(app, "D2 runtime receiver register failed: " + t.getClass().getSimpleName() + ": " + t.getMessage());
        }
    }

    public static synchronized void shutdown(Context context) {
        if (context == null) return;
        Context app = context.getApplicationContext();
        D2AudioEffectProbe.writeLog(app, "D2 runtime bridge shutdown called registered=" + registered);
        try {
            if (runtimeReceiver != null) app.unregisterReceiver(runtimeReceiver);
        } catch (Throwable t) {
            D2AudioEffectProbe.writeLog(app, "D2 runtime receiver unregister failed: " + t.getClass().getSimpleName() + ": " + t.getMessage());
        }
        runtimeReceiver = null;
        registered = false;
        D2AudioEffectProbe.releaseAll(app, "runtime-shutdown");
    }
}
