package com.crossdarkrix.dsre_realtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.media.audiofx.AudioEffect;

public class DSREAudioSessionReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) {
            D2AudioEffectProbe.writeLog(context, "receiver intent null");
            return;
        }
        String action = intent.getAction();
        D2AudioEffectProbe.writeLog(context, "receiver action=" + action + " extras=" + D2AudioEffectProbe.dumpExtras(intent));
        if (AudioEffect.ACTION_OPEN_AUDIO_EFFECT_CONTROL_SESSION.equals(action)) {
            D2AudioEffectProbe.onOpenSession(context, intent);
        } else if (AudioEffect.ACTION_CLOSE_AUDIO_EFFECT_CONTROL_SESSION.equals(action)) {
            D2AudioEffectProbe.onCloseSession(context, intent);
        } else {
            D2AudioEffectProbe.writeLog(context, "receiver ignored action=" + action);
        }
    }
}
