package com.crossdarkrix.dsre_realtime;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.media.audiofx.AudioEffect;

public final class D2AudioEffectControlPanelBridge {
    private D2AudioEffectControlPanelBridge() {}

    public static void handleActivityIntent(Activity activity, String source) {
        if (activity == null) return;
        try {
            Intent intent = activity.getIntent();
            handleIntent(activity, intent, source);
        } catch (Throwable t) {
            D2AudioEffectProbe.writeLog(activity, "control panel handleActivityIntent failed source=" + source + " error=" + t.getClass().getSimpleName() + ": " + t.getMessage());
        }
    }

    public static void handleIntent(Context context, Intent intent, String source) {
        if (context == null) return;
        if (intent == null) {
            D2AudioEffectProbe.writeLog(context, "control panel intent null source=" + source);
            return;
        }
        String action = intent.getAction();
        D2AudioEffectProbe.writeLog(context, "control panel intent source=" + source + " action=" + action + " extras=" + D2AudioEffectProbe.dumpExtras(intent));
        if (AudioEffect.ACTION_DISPLAY_AUDIO_EFFECT_CONTROL_PANEL.equals(action)) {
            int sessionId = intent.getIntExtra(AudioEffect.EXTRA_AUDIO_SESSION, AudioEffect.ERROR_BAD_VALUE);
            String packageName = intent.getStringExtra(AudioEffect.EXTRA_PACKAGE_NAME);
            int contentType = intent.getIntExtra(AudioEffect.EXTRA_CONTENT_TYPE, -1);
            D2AudioEffectProbe.writeLog(context, "DISPLAY panel session=" + sessionId + " package=" + packageName + " contentType=" + contentType + " source=" + source);
            if (sessionId > 0) {
                D2AudioEffectProbe.onOpenSession(context, intent);
            } else {
                D2AudioEffectProbe.writeLog(context, "DISPLAY panel ignored invalid session=" + sessionId);
            }
        }
    }
}
