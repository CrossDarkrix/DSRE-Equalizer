package com.crossdarkrix.dsre_realtime;

import android.content.Intent;
import android.util.Log;

import org.kivy.android.PythonActivity;

public class DSREPythonActivity extends PythonActivity {
    private static final String TAG = "DSREPythonActivity";

    @Override
    public void onActivityResult(int requestCode, int resultCode, Intent data) {
        DSREProjectionServiceStarter.writeExternalLog(
                this,
                "DSREPythonActivity.onActivityResult requestCode=" + requestCode
                        + " resultCode=" + resultCode + " dataNull=" + (data == null)
        );
        if (requestCode == DSREProjectionServiceStarter.REQUEST_MEDIA_PROJECTION) {
            if (data == null) {
                DSREProjectionServiceStarter.writeExternalLog(this, "MediaProjection result data is null; service not started");
                super.onActivityResult(requestCode, resultCode, data);
                return;
            }
            try {
                DSREProjectionServiceStarter.writeExternalLog(this, "MediaProjection result received in Java Activity; starting service");
                DSREProjectionServiceStarter.startProjectionService(this, resultCode, data, "projection_from_java_activity");
                DSREProjectionServiceStarter.writeExternalLog(this, "startProjectionService returned from Java Activity");
            } catch (Throwable t) {
                DSREProjectionServiceStarter.writeExternalLog(this, "startProjectionService failed in Java Activity: " + t.getClass().getSimpleName() + ": " + String.valueOf(t.getMessage()));
                Log.e(TAG, "startProjectionService failed", t);
            }
            super.onActivityResult(requestCode, resultCode, data);
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }
}
