package com.crossdarkrix.dsre_realtime;

import android.content.Context;
import android.content.Intent;
import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioPlaybackCaptureConfiguration;
import android.media.AudioRecord;
import android.media.AudioTrack;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.os.Process;
import android.util.Log;

import org.kivy.android.PythonService;

import java.io.File;
import java.io.FileWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public final class DSREAudioCaptureEngine {
    private static final String TAG = "DSREAudioCaptureEngine";
    private static volatile boolean FILE_LOG_ENABLED = false;
    private static final String LOG_FILE_NAME = "dsre_audio_capture_engine.log";
    private static volatile boolean running = false;
    private static volatile String stage = "idle";
    private static volatile String lastError = "";
    private static volatile long framesRead = 0L;
    private static volatile long readCalls = 0L;
    private static volatile long writeCalls = 0L;
    private static volatile int lastRead = 0;
    private static volatile int lastWrite = 0;
    private static volatile float lastRms = 0.0f;
    private static volatile float lastOutRms = 0.0f;
    private static volatile float gain = 0.20f;
    public static final int PROCESS_GAIN_ONLY = 0;
    public static final int PROCESS_SOFT_CLIP = 1;
    public static final int PROCESS_SIMPLE_COMPRESSOR = 2;
    public static final int PROCESS_HARMONIC_SATURATION = 3;
    public static final int PROCESS_COMPRESSOR_PLUS_SATURATION = 4;
    public static final int PROCESS_COMPRESSOR_DIAGNOSTIC = 5;
    public static final int PROCESS_MINI_DSRE = 6;
    public static final int PROCESS_MINI_DSRE_WET_DELTA = 7;
    public static final int PROCESS_MINI_DSRE_AIR_ASSIST = 8;
    private static volatile int processMode = PROCESS_GAIN_ONLY;
    private static volatile long sessionId = 0L;
    private static volatile long writeZeroCount = 0L;
    private static volatile long shortWriteCount = 0L;
    private static volatile long errorCount = 0L;
    private static volatile long loopStartedAtMs = 0L;
    private static volatile float lastProcessorPeak = 0.0f;
    private static volatile float lastGainReduction = 0.0f;
    private static volatile int lastCompressorActiveSamples = 0;
    private static volatile float miniThreshold = 0.14f;
    private static volatile float miniRatio = 2.20f;
    private static volatile float miniMakeup = 1.05f;
    private static volatile float miniSaturationDrive = 1.22f;
    private static volatile float miniSaturationMix = 0.16f;
    private static volatile float miniOutputGain = 1.00f;
    private static volatile float miniAssistGain = 0.25f;
    private static volatile float miniAirMix = 0.80f;
    private static volatile float miniAirHpAlpha = 0.08f;
    private static volatile float miniAirLp0 = 0.0f;
    private static volatile float miniAirLp1 = 0.0f;
    private static volatile float lastWetRms = 0.0f;
    private static volatile float lastAssistRms = 0.0f;
    private static Thread workerThread = null;
    private static AudioRecord audioRecord = null;
    private static AudioTrack audioTrack = null;
    private static MediaProjection mediaProjection = null;
    private DSREAudioCaptureEngine() {}
    public static void setFileLogEnabled(boolean enabled) { FILE_LOG_ENABLED = enabled; }
    public static boolean isRunning() { return running; }
    public static String getStage() { return stage; }
    public static String getLastError() { return lastError; }
    public static long getFramesRead() { return framesRead; }
    public static long getReadCalls() { return readCalls; }
    public static long getWriteCalls() { return writeCalls; }
    public static int getLastRead() { return lastRead; }
    public static int getLastWrite() { return lastWrite; }
    public static float getLastRms() { return lastRms; }
    public static float getLastOutRms() { return lastOutRms; }
    public static float getGain() { return gain; }
    public static int getProcessMode() { return processMode; }
    public static long getSessionId() { return sessionId; }
    public static long getWriteZeroCount() { return writeZeroCount; }
    public static long getShortWriteCount() { return shortWriteCount; }
    public static long getErrorCount() { return errorCount; }
    public static long getLoopStartedAtMs() { return loopStartedAtMs; }
    public static float getLastProcessorPeak() { return lastProcessorPeak; }
    public static float getLastGainReduction() { return lastGainReduction; }
    public static int getLastCompressorActiveSamples() { return lastCompressorActiveSamples; }
    public static float getMiniThreshold() { return miniThreshold; }
    public static float getMiniRatio() { return miniRatio; }
    public static float getMiniMakeup() { return miniMakeup; }
    public static float getMiniSaturationDrive() { return miniSaturationDrive; }
    public static float getMiniSaturationMix() { return miniSaturationMix; }
    public static float getMiniOutputGain() { return miniOutputGain; }
    public static float getMiniAssistGain() { return miniAssistGain; }
    public static float getMiniAirMix() { return miniAirMix; }
    public static float getMiniAirHpAlpha() { return miniAirHpAlpha; }
    public static float getLastWetRms() { return lastWetRms; }
    public static float getLastAssistRms() { return lastAssistRms; }
    public static void configureMiniDsreAssist(float assistGain, float airMix, float airHpAlpha) {
        miniAssistGain = clamp(assistGain, 0.0f, 1.0f);
        miniAirMix = clamp(airMix, 0.0f, 1.0f);
        miniAirHpAlpha = clamp(airHpAlpha, 0.005f, 0.50f);
        miniAirLp0 = 0.0f;
        miniAirLp1 = 0.0f;
        writeLog(null, "configureMiniDsreAssist assistGain=" + miniAssistGain + " airMix=" + miniAirMix + " airHpAlpha=" + miniAirHpAlpha);
    }
    public static void configureMiniDsre(float threshold, float ratio, float makeup, float satDrive, float satMix, float outputGain) {
        miniThreshold = clamp(threshold, 0.02f, 0.60f);
        miniRatio = clamp(ratio, 1.0f, 8.0f);
        miniMakeup = clamp(makeup, 0.50f, 2.00f);
        miniSaturationDrive = clamp(satDrive, 0.50f, 3.00f);
        miniSaturationMix = clamp(satMix, 0.0f, 1.0f);
        miniOutputGain = clamp(outputGain, 0.20f, 2.00f);
        writeLog(null, "configureMiniDsre threshold=" + miniThreshold + " ratio=" + miniRatio + " makeup=" + miniMakeup + " satDrive=" + miniSaturationDrive + " satMix=" + miniSaturationMix + " outputGain=" + miniOutputGain);
    }
    private static float clamp(float value, float min, float max) {
        if (Float.isNaN(value) || Float.isInfinite(value)) return min;
        if (value < min) return min;
        if (value > max) return max;
        return value;
    }

    public static void startStablePassthroughFromStoredProjection(final int sampleRate, final int requestedChannels, final float requestedGain, final int requestedProcessMode) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            lastError = "AudioPlaybackCapture requires Android Q/API29+";
            stage = "unsupported sdk";
            writeLog(null, lastError);
            return;
        }
        synchronized (DSREAudioCaptureEngine.class) {
            if (running) {
                stage = "already running";
                writeLog(null, stage);
                return;
            }
            running = true;
            gain = sanitizeGain(requestedGain);
            processMode = sanitizeProcessMode(requestedProcessMode);
            sessionId = System.currentTimeMillis();
            writeZeroCount = 0L;
            shortWriteCount = 0L;
            errorCount = 0L;
            loopStartedAtMs = 0L;
            lastError = "";
            framesRead = 0L;
            readCalls = 0L;
            writeCalls = 0L;
            lastRead = 0;
            lastWrite = 0;
            lastRms = 0.0f;
            lastOutRms = 0.0f;
            stage = "start stable passthrough requested";
        }
        workerThread = new Thread(new Runnable() {
            @Override public void run() { runPassthrough(sampleRate, requestedChannels); }
        }, "DSRE-PassthroughEngine-" + sessionId);
        workerThread.start();
    }

    public static void stopCapture() {
        running = false;
        stage = "stop requested";
        try {
            if (audioRecord != null) {
                try { audioRecord.stop(); } catch (Throwable ignored) {}
                try { audioRecord.release(); } catch (Throwable ignored) {}
                audioRecord = null;
            }
        } catch (Throwable ignored) {}
        try {
            if (audioTrack != null) {
                try { audioTrack.stop(); } catch (Throwable ignored) {}
                try { audioTrack.release(); } catch (Throwable ignored) {}
                audioTrack = null;
            }
        } catch (Throwable ignored) {}
        try {
            if (mediaProjection != null) {
                mediaProjection.stop();
                mediaProjection = null;
            }
        } catch (Throwable ignored) {}
        writeLog(null, "stopCapture done session=" + sessionId + " frames=" + framesRead + " readCalls=" + readCalls + " writeCalls=" + writeCalls + " zeroWrites=" + writeZeroCount + " shortWrites=" + shortWriteCount + " errors=" + errorCount + " processorPeak=" + lastProcessorPeak + " gainReduction=" + lastGainReduction + " compressorActive=" + lastCompressorActiveSamples + " miniThreshold=" + miniThreshold + " miniRatio=" + miniRatio + " miniMakeup=" + miniMakeup + " satDrive=" + miniSaturationDrive + " satMix=" + miniSaturationMix + " miniOutputGain=" + miniOutputGain);
    }

    private static void runPassthrough(int sampleRate, int requestedChannels) {
        Process.setThreadPriority(Process.THREAD_PRIORITY_AUDIO);
        Context ctx = null;
        int channels = requestedChannels == 1 ? 1 : 2;
        try {
            stage = "get context";
            ctx = PythonService.mService;
            if (ctx == null) throw new IllegalStateException("PythonService.mService is null");
            writeLog(ctx, "runPassthrough entered session=" + sessionId + " sampleRate=" + sampleRate + " requestedChannels=" + requestedChannels + " gain=" + gain + " mode=" + processMode);
            stage = "get projection data";
            Intent resultData = DSREPythonService.getProjectionResultData();
            int resultCode = DSREPythonService.getProjectionResultCode();
            if (resultData == null) throw new IllegalStateException("projection resultData is null");
            stage = "get MediaProjection";
            MediaProjectionManager manager = (MediaProjectionManager) ctx.getSystemService(Context.MEDIA_PROJECTION_SERVICE);
            if (manager == null) throw new IllegalStateException("MediaProjectionManager is null");
            mediaProjection = manager.getMediaProjection(resultCode, resultData);
            if (mediaProjection == null) throw new IllegalStateException("MediaProjection is null");
            stage = "build capture config";
            AudioPlaybackCaptureConfiguration captureConfig = new AudioPlaybackCaptureConfiguration.Builder(mediaProjection)
                    .addMatchingUsage(AudioAttributes.USAGE_MEDIA)
                    .addMatchingUsage(AudioAttributes.USAGE_GAME)
                    .addMatchingUsage(AudioAttributes.USAGE_UNKNOWN)
                    .build();
            boolean opened = false;
            Throwable lastOpenError = null;
            for (int attempt = 0; attempt < 2 && !opened; attempt++) {
                if (attempt == 1) channels = 1;
                try {
                    openAudioRecordAndTrack(captureConfig, sampleRate, channels);
                    opened = true;
                } catch (Throwable t) {
                    lastOpenError = t;
                    closeAudioOnly();
                }
            }
            if (!opened) throw lastOpenError == null ? new IllegalStateException("openAudioRecordAndTrack failed") : lastOpenError;
            stage = "start recording/playback";
            audioRecord.startRecording();
            audioTrack.play();
            int bufferSamples = Math.max(1024, (sampleRate / 50) * channels);
            short[] inBuffer = new short[bufferSamples];
            short[] outBuffer = new short[bufferSamples];
            stage = "passthrough loop ch=" + channels + " bufferSamples=" + bufferSamples + " gain=" + gain;
            writeLog(ctx, stage);
            loopStartedAtMs = System.currentTimeMillis();
            while (running) {
                int read = audioRecord.read(inBuffer, 0, inBuffer.length);
                lastRead = read;
                if (read > 0) {
                    readCalls += 1;
                    framesRead += read / channels;
                    lastRms = computeRms(inBuffer, read);
                    processBuffer(inBuffer, outBuffer, read, gain, processMode);
                    lastOutRms = computeRms(outBuffer, read);
                    int writtenTotal = 0;
                    while (running && writtenTotal < read) {
                        int written = audioTrack.write(outBuffer, writtenTotal, read - writtenTotal);
                        lastWrite = written;
                        if (written < 0) throw new IllegalStateException("AudioTrack.write failed: " + written);
                        if (written == 0) {
                            writeZeroCount += 1;
                            Thread.yield();
                        }
                        if (written > 0 && written < (read - writtenTotal)) {
                            shortWriteCount += 1;
                        }
                        writtenTotal += written;
                    }
                    writeCalls += 1;
                    if (readCalls == 1 || readCalls % 100 == 0) {
                        writeLog(ctx, "passthrough_stats running=" + running
                                + " frames=" + framesRead
                                + " readCalls=" + readCalls
                                + " writeCalls=" + writeCalls
                                + " lastRead=" + lastRead
                                + " lastWrite=" + lastWrite
                                + " rms=" + lastRms
                                + " outRms=" + lastOutRms
                                + " gain=" + gain + " mode=" + processMode + " session=" + sessionId + " zeroWrites=" + writeZeroCount + " shortWrites=" + shortWriteCount + " errors=" + errorCount + " processorPeak=" + lastProcessorPeak + " gainReduction=" + lastGainReduction + " compressorActive=" + lastCompressorActiveSamples + " miniThreshold=" + miniThreshold + " miniRatio=" + miniRatio + " miniMakeup=" + miniMakeup + " satDrive=" + miniSaturationDrive + " satMix=" + miniSaturationMix + " miniOutputGain=" + miniOutputGain);
                    }
                } else if (read < 0) {
                    throw new IllegalStateException("AudioRecord.read failed: " + read);
                } else {
                    Thread.yield();
                }
            }
            stage = "passthrough loop ended";
        } catch (Throwable t) {
            errorCount += 1;
            lastError = t.getClass().getSimpleName() + ": " + String.valueOf(t.getMessage());
            stage = "error at " + stage;
            writeLog(ctx, "ERROR " + stage + " " + lastError);
            Log.e(TAG, lastError, t);
        } finally {
            running = false;
            closeAudioOnly();
            try {
                if (mediaProjection != null) {
                    mediaProjection.stop();
                    mediaProjection = null;
                }
            } catch (Throwable ignored) {}
            writeLog(ctx, "runPassthrough finally stage=" + stage + " error=" + lastError);
        }
    }

    private static void openAudioRecordAndTrack(AudioPlaybackCaptureConfiguration captureConfig, int sampleRate, int channels) {
        stage = "openAudioRecordAndTrack ch=" + channels;
        int channelMaskIn = channels == 2 ? AudioFormat.CHANNEL_IN_STEREO : AudioFormat.CHANNEL_IN_MONO;
        int channelMaskOut = channels == 2 ? AudioFormat.CHANNEL_OUT_STEREO : AudioFormat.CHANNEL_OUT_MONO;
        AudioFormat inFormat = new AudioFormat.Builder()
                .setSampleRate(sampleRate)
                .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                .setChannelMask(channelMaskIn)
                .build();
        AudioFormat outFormat = new AudioFormat.Builder()
                .setSampleRate(sampleRate)
                .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                .setChannelMask(channelMaskOut)
                .build();
        int minRec = AudioRecord.getMinBufferSize(sampleRate, channelMaskIn, AudioFormat.ENCODING_PCM_16BIT);
        int minOut = AudioTrack.getMinBufferSize(sampleRate, channelMaskOut, AudioFormat.ENCODING_PCM_16BIT);
        if (minRec <= 0) throw new IllegalStateException("invalid minRecordBuffer " + minRec + " ch=" + channels);
        if (minOut <= 0) throw new IllegalStateException("invalid minTrackBuffer " + minOut + " ch=" + channels);
        int bufferBytes = Math.max(Math.max(minRec, minOut) * 2, sampleRate * channels * 2 / 10);
        audioRecord = new AudioRecord.Builder()
                .setAudioPlaybackCaptureConfig(captureConfig)
                .setAudioFormat(inFormat)
                .setBufferSizeInBytes(bufferBytes)
                .build();
        if (audioRecord.getState() != AudioRecord.STATE_INITIALIZED) throw new IllegalStateException("AudioRecord not initialized ch=" + channels);
        audioTrack = new AudioTrack.Builder()
                .setAudioAttributes(new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                        .build())
                .setAudioFormat(outFormat)
                .setTransferMode(AudioTrack.MODE_STREAM)
                .setBufferSizeInBytes(bufferBytes)
                .build();
        if (audioTrack.getState() != AudioTrack.STATE_INITIALIZED) throw new IllegalStateException("AudioTrack not initialized ch=" + channels);
        writeLog(null, "AudioRecord/AudioTrack initialized ch=" + channels + " minRec=" + minRec + " minOut=" + minOut + " bufferBytes=" + bufferBytes + " gain=" + gain + " mode=" + processMode + " session=" + sessionId + " zeroWrites=" + writeZeroCount + " shortWrites=" + shortWriteCount + " errors=" + errorCount + " processorPeak=" + lastProcessorPeak + " gainReduction=" + lastGainReduction + " compressorActive=" + lastCompressorActiveSamples + " miniThreshold=" + miniThreshold + " miniRatio=" + miniRatio + " miniMakeup=" + miniMakeup + " satDrive=" + miniSaturationDrive + " satMix=" + miniSaturationMix + " miniOutputGain=" + miniOutputGain);
    }

    private static void closeAudioOnly() {
        try {
            if (audioRecord != null) {
                try { audioRecord.release(); } catch (Throwable ignored) {}
                audioRecord = null;
            }
        } catch (Throwable ignored) {}
        try {
            if (audioTrack != null) {
                try { audioTrack.release(); } catch (Throwable ignored) {}
                audioTrack = null;
            }
        } catch (Throwable ignored) {}
    }
    private static float sanitizeGain(float value) {
        if (Float.isNaN(value) || Float.isInfinite(value)) return 0.20f;
        if (value < 0.0f) return 0.0f;
        if (value > 1.0f) return 1.0f;
        return value;
    }
    private static int sanitizeProcessMode(int value) {
        if (value == PROCESS_SOFT_CLIP) return PROCESS_SOFT_CLIP;
        if (value == PROCESS_SIMPLE_COMPRESSOR) return PROCESS_SIMPLE_COMPRESSOR;
        if (value == PROCESS_HARMONIC_SATURATION) return PROCESS_HARMONIC_SATURATION;
        if (value == PROCESS_COMPRESSOR_PLUS_SATURATION) return PROCESS_COMPRESSOR_PLUS_SATURATION;
        if (value == PROCESS_COMPRESSOR_DIAGNOSTIC) return PROCESS_COMPRESSOR_DIAGNOSTIC;
        if (value == PROCESS_MINI_DSRE) return PROCESS_MINI_DSRE;
        if (value == PROCESS_MINI_DSRE_WET_DELTA) return PROCESS_MINI_DSRE_WET_DELTA;
        if (value == PROCESS_MINI_DSRE_AIR_ASSIST) return PROCESS_MINI_DSRE_AIR_ASSIST;
        return PROCESS_GAIN_ONLY;
    }

    private static void processBuffer(short[] input, short[] output, int samples, float g, int mode) {
        float peak = 0.0f;
        float totalReduction = 0.0f;
        float wetSquare = 0.0f;
        float assistSquare = 0.0f;
        int activeSamples = 0;
        for (int i = 0; i < samples; i++) {
            float x = input[i] / 32768.0f;
            float dry = x * g;
            float processed = dry;
            float out = dry;
            if (mode == PROCESS_SOFT_CLIP) { out = softClip(dry); processed = out; }
            else if (mode == PROCESS_SIMPLE_COMPRESSOR) { out = simpleCompressor(dry); processed = out; }
            else if (mode == PROCESS_HARMONIC_SATURATION) { out = harmonicSaturation(dry); processed = out; }
            else if (mode == PROCESS_COMPRESSOR_PLUS_SATURATION) { processed = simpleCompressor(dry); processed = harmonicSaturation(processed); out = processed; }
            else if (mode == PROCESS_COMPRESSOR_DIAGNOSTIC) { out = compressorDiagnostic(dry); processed = out; }
            else if (mode == PROCESS_MINI_DSRE) { processed = miniDsreCore(dry); out = processed * miniOutputGain; }
            else if (mode == PROCESS_MINI_DSRE_WET_DELTA) { processed = miniDsreCore(dry); float wet = processed - dry; out = wet * miniAssistGain; wetSquare += wet * wet; assistSquare += out * out; }
            else if (mode == PROCESS_MINI_DSRE_AIR_ASSIST) { processed = miniDsreCore(dry); float wet = processed - dry; float air = airAssistHighPass(wet, i); float assist = wet * (1.0f - miniAirMix) + air * miniAirMix; out = assist * miniAssistGain; wetSquare += wet * wet; assistSquare += out * out; }
            if (out > 1.0f) out = 1.0f;
            if (out < -1.0f) out = -1.0f;
            float beforeAbs = Math.abs(dry);
            float processedAbs = Math.abs(processed);
            float afterAbs = Math.abs(out);
            if (beforeAbs > processedAbs) { totalReduction += beforeAbs - processedAbs; activeSamples += 1; }
            if (afterAbs > peak) peak = afterAbs;
            int v = Math.round(out * 32767.0f);
            if (v > 32767) v = 32767;
            if (v < -32768) v = -32768;
            output[i] = (short) v;
        }
        lastProcessorPeak = peak;
        lastGainReduction = samples > 0 ? totalReduction / samples : 0.0f;
        lastCompressorActiveSamples = activeSamples;
        lastWetRms = samples > 0 ? (float)Math.sqrt(wetSquare / samples) : 0.0f;
        lastAssistRms = samples > 0 ? (float)Math.sqrt(assistSquare / samples) : 0.0f;
    }

    private static float miniDsreCore(float x) {
        float y = compressorCore(x, miniThreshold, miniRatio, miniMakeup);
        y = harmonicSaturationParam(y, miniSaturationDrive, miniSaturationMix);
        if (y > 1.0f) y = 1.0f;
        if (y < -1.0f) y = -1.0f;
        return y;
    }

    private static float airAssistHighPass(float wet, int index) {
        float alpha = miniAirHpAlpha;
        if (alpha < 0.005f) alpha = 0.005f;
        if (alpha > 0.50f) alpha = 0.50f;
        if ((index & 1) == 0) { miniAirLp0 = miniAirLp0 + alpha * (wet - miniAirLp0); return wet - miniAirLp0; }
        miniAirLp1 = miniAirLp1 + alpha * (wet - miniAirLp1); return wet - miniAirLp1;
    }

    private static float miniDsreProcess(float x) { return miniDsreCore(x) * miniOutputGain; }
    private static float simpleCompressor(float x) { return compressorCore(x, 0.22f, 3.0f, 1.10f); }
    private static float compressorDiagnostic(float x) { float y = compressorCore(x * 1.70f, 0.08f, 4.0f, 0.95f); if (y > 1.0f) y = 1.0f; if (y < -1.0f) y = -1.0f; return y; }
    private static float compressorCore(float x, float threshold, float ratio, float makeup) { float sign = x < 0.0f ? -1.0f : 1.0f; float a = Math.abs(x); if (a > threshold) a = threshold + (a - threshold) / Math.max(1.0f, ratio); float y = a * makeup; if (y > 1.0f) y = 1.0f; return sign * y; }
    private static float harmonicSaturation(float x) { return harmonicSaturationParam(x, 1.35f, 0.22f); }
    private static float harmonicSaturationParam(float x, float drive, float mix) { float safeDrive = Math.max(0.1f, drive); float safeMix = Math.max(0.0f, Math.min(1.0f, mix)); float saturated = (float)Math.tanh(x * safeDrive); float norm = (float)Math.tanh(safeDrive); if (norm > 0.0001f) saturated /= norm; float y = x * (1.0f - safeMix) + saturated * safeMix; if (y > 1.0f) y = 1.0f; if (y < -1.0f) y = -1.0f; return y; }
    private static float softClip(float x) { if (x > 1.0f) x = 1.0f; if (x < -1.0f) x = -1.0f; return x - (x * x * x) / 3.0f; }

    private static float computeRms(short[] buffer, int samples) {
        if (buffer == null || samples <= 0) return 0.0f;
        double sum = 0.0;
        for (int i = 0; i < samples; i++) {
            double v = buffer[i] / 32768.0;
            sum += v * v;
        }
        return (float) Math.sqrt(sum / samples);
    }
    private static void writeLog(Context ctx, String msg) {
        try {
            Context realCtx = ctx;
            if (realCtx == null) {
                try { realCtx = PythonService.mService; } catch (Throwable ignored) {}
            }
            File dir = null;
            if (realCtx != null) {
                dir = realCtx.getExternalFilesDir(null);
                if (dir == null) dir = realCtx.getFilesDir();
            }
            if (dir == null) return;
            if (!dir.exists()) dir.mkdirs();
            File file = new File(dir, LOG_FILE_NAME);
            FileWriter fw = new FileWriter(file, true);
            String ts = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(new Date());
        } catch (Throwable ignored) {}
    }
}
