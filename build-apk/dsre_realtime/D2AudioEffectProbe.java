package com.crossdarkrix.dsre_realtime;

import android.content.Context;
import android.content.Intent;
import android.media.audiofx.AudioEffect;
import android.media.audiofx.BassBoost;
import android.media.audiofx.Equalizer;
import android.media.audiofx.LoudnessEnhancer;
import android.os.Bundle;
import android.util.Log;

import java.io.File;
import java.io.FileWriter;
import java.util.HashMap;
import java.util.Map;

public final class D2AudioEffectProbe {
    private static final String TAG = "DSRED2Probe";
    private static volatile boolean FILE_LOG_ENABLED = false;
    private static final String LOG_FILE = "dsre_d2_audio_effect_probe.log";
    private static final Map<Integer, SessionEffects> EFFECTS = new HashMap<>();

    private D2AudioEffectProbe() {}
    public static void setFileLogEnabled(boolean enabled) { FILE_LOG_ENABLED = enabled; }

    public static void selfTest(Context context) {
        writeLog(context, "selfTest begin");
        try {
            AudioEffect.Descriptor[] descriptors = AudioEffect.queryEffects();
            int count = descriptors == null ? 0 : descriptors.length;
            writeLog(context, "queryEffects count=" + count);
            if (descriptors != null) {
                for (int i = 0; i < descriptors.length; i++) {
                    AudioEffect.Descriptor d = descriptors[i];
                    if (d != null) writeLog(context, "effect[" + i + "] name=" + d.name + " implementor=" + d.implementor + " type=" + d.type + " uuid=" + d.uuid + " connectMode=" + d.connectMode);
                }
            }
        } catch (Throwable t) {
            writeLog(context, "queryEffects failed: " + t.getClass().getSimpleName() + ": " + t.getMessage());
        }
        writeLog(context, "selfTest end");
    }

    public static synchronized void onOpenSession(Context context, Intent intent) {
        int sessionId = intent.getIntExtra(AudioEffect.EXTRA_AUDIO_SESSION, AudioEffect.ERROR_BAD_VALUE);
        String packageName = intent.getStringExtra(AudioEffect.EXTRA_PACKAGE_NAME);
        int contentType = intent.getIntExtra(AudioEffect.EXTRA_CONTENT_TYPE, -1);
        writeLog(context, "OPEN session=" + sessionId + " package=" + packageName + " contentType=" + contentType);
        if (sessionId <= 0) {
            writeLog(context, "OPEN ignored invalid session=" + sessionId);
            return;
        }
        releaseSession(context, sessionId, "replace-existing-before-open");
        SessionEffects effects = new SessionEffects(sessionId, packageName, contentType);
        effects.attach(context);
        EFFECTS.put(sessionId, effects);
    }

    public static synchronized void onCloseSession(Context context, Intent intent) {
        int sessionId = intent.getIntExtra(AudioEffect.EXTRA_AUDIO_SESSION, AudioEffect.ERROR_BAD_VALUE);
        String packageName = intent.getStringExtra(AudioEffect.EXTRA_PACKAGE_NAME);
        int contentType = intent.getIntExtra(AudioEffect.EXTRA_CONTENT_TYPE, -1);
        writeLog(context, "CLOSE session=" + sessionId + " package=" + packageName + " contentType=" + contentType);
        if (sessionId > 0) releaseSession(context, sessionId, "close-broadcast");
    }

    public static synchronized void releaseAll(Context context, String reason) {
        Integer[] sessions = EFFECTS.keySet().toArray(new Integer[0]);
        for (Integer session : sessions) if (session != null) releaseSession(context, session.intValue(), reason);
    }

    public static synchronized void releaseSession(Context context, int sessionId, String reason) {
        SessionEffects effects = EFFECTS.remove(sessionId);
        if (effects != null) {
            writeLog(context, "release session=" + sessionId + " reason=" + reason);
            effects.release(context);
        }
    }

    public static String dumpExtras(Intent intent) {
        try {
            Bundle extras = intent.getExtras();
            return extras == null ? "null" : extras.toString();
        } catch (Throwable t) {
            return "dumpExtras failed: " + t.getClass().getSimpleName() + ": " + t.getMessage();
        }
    }

    public static void writeLog(Context context, String msg) {
        String line = String.valueOf(System.currentTimeMillis()) + " [D2AudioEffectProbe] " + msg;
        Log.d(TAG, line);
        if (!FILE_LOG_ENABLED) return;
        try {
            Context appContext = context != null ? context.getApplicationContext() : null;
            if (appContext == null) return;
            File dir = appContext.getExternalFilesDir(null);
            if (dir == null) dir = appContext.getFilesDir();
            if (dir == null) return;
            File file = new File(dir, LOG_FILE);
            FileWriter writer = new FileWriter(file, true);
        } catch (Throwable ignored) {}
    }

    private static final class SessionEffects {
        final int sessionId;
        final String packageName;
        final int contentType;
        Equalizer equalizer;
        LoudnessEnhancer loudnessEnhancer;
        BassBoost bassBoost;

        SessionEffects(int sessionId, String packageName, int contentType) {
            this.sessionId = sessionId;
            this.packageName = packageName;
            this.contentType = contentType;
        }

        void attach(Context context) {
            writeLog(context, "attach begin session=" + sessionId + " package=" + packageName);
            attachEqualizer(context);
            attachLoudness(context);
            attachBassBoost(context);
            writeLog(context, "attach end session=" + sessionId + " eq=" + (equalizer != null) + " loudness=" + (loudnessEnhancer != null) + " bass=" + (bassBoost != null));
        }

        void attachEqualizer(Context context) {
            try {
                Equalizer eq = new Equalizer(1000, sessionId);
                short bands = eq.getNumberOfBands();
                short[] range = eq.getBandLevelRange();
                short min = range != null && range.length > 0 ? range[0] : -1500;
                short max = range != null && range.length > 1 ? range[1] : 1500;
                short level = (short)Math.max(min, Math.min(max, 250));
                for (short i = 0; i < bands; i++) {
                    try { eq.setBandLevel(i, level); } catch (Throwable bandError) { writeLog(context, "eq band failed session=" + sessionId + " band=" + i + " error=" + bandError); }
                }
                eq.setEnabled(true);
                equalizer = eq;
                writeLog(context, "Equalizer attached session=" + sessionId + " bands=" + bands + " level=" + level + " enabled=" + eq.getEnabled());
            } catch (Throwable t) {
                writeLog(context, "Equalizer attach failed session=" + sessionId + " error=" + t.getClass().getSimpleName() + ": " + t.getMessage());
            }
        }

        void attachLoudness(Context context) {
            try {
                LoudnessEnhancer le = new LoudnessEnhancer(sessionId);
                le.setTargetGain(300);
                le.setEnabled(true);
                loudnessEnhancer = le;
                writeLog(context, "LoudnessEnhancer attached session=" + sessionId + " targetGain=300 enabled=" + le.getEnabled());
            } catch (Throwable t) {
                writeLog(context, "LoudnessEnhancer attach failed session=" + sessionId + " error=" + t.getClass().getSimpleName() + ": " + t.getMessage());
            }
        }

        void attachBassBoost(Context context) {
            try {
                BassBoost bb = new BassBoost(1000, sessionId);
                if (bb.getStrengthSupported()) bb.setStrength((short)300);
                bb.setEnabled(true);
                bassBoost = bb;
                writeLog(context, "BassBoost attached session=" + sessionId + " strengthSupported=" + bb.getStrengthSupported() + " enabled=" + bb.getEnabled());
            } catch (Throwable t) {
                writeLog(context, "BassBoost attach failed session=" + sessionId + " error=" + t.getClass().getSimpleName() + ": " + t.getMessage());
            }
        }

        void release(Context context) {
            if (equalizer != null) {
                try { equalizer.setEnabled(false); } catch (Throwable ignored) {}
                try { equalizer.release(); } catch (Throwable ignored) {}
                writeLog(context, "Equalizer released session=" + sessionId);
                equalizer = null;
            }
            if (loudnessEnhancer != null) {
                try { loudnessEnhancer.setEnabled(false); } catch (Throwable ignored) {}
                try { loudnessEnhancer.release(); } catch (Throwable ignored) {}
                writeLog(context, "LoudnessEnhancer released session=" + sessionId);
                loudnessEnhancer = null;
            }
            if (bassBoost != null) {
                try { bassBoost.setEnabled(false); } catch (Throwable ignored) {}
                try { bassBoost.release(); } catch (Throwable ignored) {}
                writeLog(context, "BassBoost released session=" + sessionId);
                bassBoost = null;
            }
        }
    }
}
