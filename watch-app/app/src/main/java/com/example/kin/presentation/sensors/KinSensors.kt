package com.example.kin.presentation.sensors

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.speech.RecognitionListener
import android.speech.SpeechRecognizer
import android.speech.RecognizerIntent
import android.util.Log

class KinSensors(private val context: Context) {

    private val vibrator = context.getSystemService(Vibrator::class.java)

    @SuppressLint("NewApi") // Suppress error because we check SDK_INT below
    fun vibrateTick() {
        // Only run this on Android 12 (API 31/S) or newer
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S) {
            val effect = VibrationEffect.startComposition()
                .addPrimitive(VibrationEffect.Composition.PRIMITIVE_LOW_TICK)
                .compose()
            vibrator?.vibrate(effect)
        } else {
            // Fallback for older updates
            vibrator?.vibrate(VibrationEffect.createOneShot(10, 50))
        }
    }

    fun vibrateSuccess() {
        val effect = VibrationEffect.createWaveform(longArrayOf(0, 50, 50, 100), -1)
        vibrator?.vibrate(effect)
    }

    fun listen(onText: (String) -> Unit) {
        android.os.Handler(android.os.Looper.getMainLooper()).post {
            val speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)
            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            }

            speechRecognizer.setRecognitionListener(object : RecognitionListener {
                override fun onResults(results: Bundle?) {
                    val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    if (!matches.isNullOrEmpty()) {
                        onText(matches[0])
                        Log.d("Kin", "Heard: ${matches[0]}")
                    }
                }
                override fun onReadyForSpeech(params: Bundle?) {}
                override fun onBeginningOfSpeech() {}
                override fun onRmsChanged(rmsdB: Float) {}
                override fun onBufferReceived(buffer: ByteArray?) {}
                override fun onEndOfSpeech() {}
                override fun onError(error: Int) { Log.e("Kin", "Speech Error: $error") }
                override fun onPartialResults(partialResults: Bundle?) {}
                override fun onEvent(eventType: Int, params: Bundle?) {}
            })

            speechRecognizer.startListening(intent)
        }
    }
}