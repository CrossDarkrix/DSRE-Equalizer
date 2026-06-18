package com.crossdarkrix.dsre_realtime;

import android.app.Activity;
import android.content.Intent;
import android.media.audiofx.AudioEffect;
import android.os.Bundle;
import android.widget.TextView;

public class D2AudioEffectControlPanelActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TextView view = new TextView(this);
        view.setText("DSRE D2 AudioEffect Control Panel Probe\nChecking intent extras...\nYou can return to the player.");
        view.setPadding(32, 32, 32, 32);
        setContentView(view);
        D2AudioEffectProbe.writeLog(this, "DedicatedControlActivity onCreate");
        handleIntent(getIntent(), "DedicatedControlActivity.onCreate");
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        D2AudioEffectProbe.writeLog(this, "DedicatedControlActivity onNewIntent");
        handleIntent(intent, "DedicatedControlActivity.onNewIntent");
    }

    private void handleIntent(Intent intent, String source) {
        D2AudioEffectControlPanelBridge.handleIntent(this, intent, source);
        if (intent == null) return;
        String action = intent.getAction();
        int sessionId = intent.getIntExtra(AudioEffect.EXTRA_AUDIO_SESSION, AudioEffect.ERROR_BAD_VALUE);
        D2AudioEffectProbe.writeLog(this, "DedicatedControlActivity handled action=" + action + " session=" + sessionId + " extras=" + D2AudioEffectProbe.dumpExtras(intent));
    }
}
