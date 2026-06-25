package com.crossdarkrix.dsre_realtime;

import android.app.Activity;
import android.content.Intent;
import android.util.Log;

import org.kivy.android.PythonActivity;

public class DSREPythonActivity extends PythonActivity {
    private static final String TAG = "DSREPythonActivity";

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != DSREProjectionServiceStarter.REQUEST_MEDIA_PROJECTION) {
            return;
        }

        DSREProjectionServiceStarter.markProjectionResult(resultCode, data);
        DSREProjectionServiceStarter.writeExternalLog(
                this,
                "onActivityResult requestCode=" + requestCode
                        + " resultCode=" + resultCode
                        + " dataNull=" + (data == null)
        );

        if (resultCode == Activity.RESULT_OK && data != null) {
            try {
                DSREProjectionServiceStarter.startProjectionService(this, resultCode, data, "projection");
            } catch (Throwable t) {
                Log.e(TAG, "startProjectionService failed", t);
            }
        }
    }
}
